from __future__ import unicode_literals, print_function

import logging
import time
from collections import defaultdict
from datetime import timedelta

from celery import shared_task, chord
from celery.exceptions import TimeoutError, MaxRetriesExceededError
from dateutil.rrule import rrule, DAILY
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail as django_send_mail, send_mass_mail as django_send_mass_mail, \
    mail_admins as django_mail_admins, mail_managers as django_mail_managers
from django.db import transaction
from django.utils import timezone

from poms.audit.models import AuthLogEntry
from poms.common import formula
from poms.common.utils import date_now, isclose
from poms.currencies.models import Currency, CurrencyHistory
from poms.instruments.models import Instrument, DailyPricingModel, PricingPolicy, PriceHistory
from poms.integrations.models import Task, PriceDownloadScheme, InstrumentDownloadScheme, PricingAutomatedSchedule
from poms.integrations.providers.base import get_provider, parse_date_iso, fill_instrument_price, fill_currency_price, \
    AbstractProvider
from poms.integrations.storage import import_file_storage
from poms.reports.builders import Report, ReportItem, ReportBuilder
from poms.users.models import MasterUser

_l = logging.getLogger('poms.integrations')


@shared_task(name='integrations.health_check')
def health_check_async():
    return True


def health_check():
    result = health_check_async.apply_async()
    try:
        return result.get(timeout=0.5, interval=0.1)
    except TimeoutError:
        pass
    return False


@shared_task(name='integrations.send_mail_async', ignore_result=True)
def send_mail_async(subject, message, from_email, recipient_list, html_message=None):
    django_send_mail(subject, message, from_email, recipient_list, fail_silently=True, html_message=html_message)


def send_mail(subject, message, from_email, recipient_list, html_message=None):
    send_mail_async.apply_async(kwargs={
        'subject': subject,
        'message': message,
        'from_email': from_email,
        'recipient_list': recipient_list,
        'html_message': html_message,
    })


@shared_task(name='integrations.send_mass_mail', ignore_result=True)
def send_mass_mail_async(messages):
    django_send_mass_mail(messages, fail_silently=True)


def send_mass_mail(messages):
    send_mass_mail_async.apply_async(kwargs={
        'messages': messages,
    })


@shared_task(name='integrations.mail_admins', ignore_result=True)
def mail_admins_async(subject, message):
    django_mail_admins(subject, message, fail_silently=True, )


def mail_admins(subject, message):
    mail_admins_async.apply_async(kwargs={
        'subject': subject,
        'message': message,
    })


@shared_task(name='integrations.mail_managers', ignore_result=True)
def mail_managers_async(subject, message):
    django_mail_managers(subject, message, fail_silently=True, )


def mail_managers(subject, message):
    mail_managers_async.apply_async(kwargs={
        'subject': subject,
        'message': message,
    })


@shared_task(name='integrations.file_import_delete', ignore_result=True)
def file_import_delete_async(path):
    _l.debug('file_import_delete_async: path=%s', path)
    import_file_storage.delete(path)


def schedule_file_import_delete(path, countdown=None):
    if countdown is None:
        countdown = 600
    _l.debug('schedule_file_import_delete: path=%s, countdown=%s', path, countdown)
    file_import_delete_async.apply_async(kwargs={'path': path}, countdown=countdown)


@shared_task(name='integrations.auth_log_statistics', ignore_result=True)
def auth_log_statistics():
    logged_in_count = AuthLogEntry.objects.filter(is_success=True).count()
    login_failed_count = AuthLogEntry.objects.filter(is_success=False).count()
    _l.debug('auth (total): logged_in=%s, login_failed=%s', logged_in_count, login_failed_count)

    now = timezone.now().date()
    logged_in_count = AuthLogEntry.objects.filter(is_success=True, date__startswith=now).count()
    login_failed_count = AuthLogEntry.objects.filter(is_success=False, date__startswith=now).count()
    _l.debug('auth (today): logged_in=%s, login_failed=%s', logged_in_count, login_failed_count)


@shared_task(name='integrations.download_instrument', bind=True, ignore_result=False)
def download_instrument_async(self, task_id=None):
    task = Task.objects.get(pk=task_id)
    _l.debug('download_instrument_async: master_user_id=%s, task=%s', task.master_user_id, task.info)

    task.add_celery_task_id(self.request.id)

    try:
        provider = get_provider(task.master_user, task.provider_id)
    except:
        _l.info('provider load error', exc_info=True)
        task.status = Task.STATUS_ERROR
        task.save()
        raise

    if provider is None:
        _l.info('provider not found')
        task.status = Task.STATUS_ERROR
        task.save()
        return

    if task.status not in [Task.STATUS_PENDING, Task.STATUS_WAIT_RESPONSE]:
        _l.debug('invalid task status')
        return
    options = task.options_object

    try:
        result, is_ready = provider.download_instrument(options)
    except Exception:
        _l.error('provider processing error', exc_info=True)
        task.status = Task.STATUS_ERROR
    else:
        if is_ready:
            task.status = Task.STATUS_DONE
            task.result_object = result
        else:
            task.status = Task.STATUS_WAIT_RESPONSE

    response_id = options.get('response_id', None)
    if response_id:
        task.response_id = response_id

    task.options_object = options
    task.save()

    if task.status == Task.STATUS_WAIT_RESPONSE:
        if self.request.is_eager:
            time.sleep(provider.get_retry_delay())
        try:
            self.retry(countdown=provider.get_retry_delay(), max_retries=provider.get_max_retries())
            # self.retry(countdown=provider.get_retry_delay(), max_retries=provider.get_max_retries(), throw=False)
        except MaxRetriesExceededError:
            task.status = Task.STATUS_TIMEOUT
            task.save()
        return

    return task_id


def download_instrument(instrument_code=None, instrument_download_scheme=None, master_user=None, member=None,
                        task=None, value_overrides=None):
    _l.debug('download_pricing: master_user_id=%s, task=%s, instrument_code=%s, instrument_download_scheme=%s',
             getattr(master_user, 'id', None), getattr(task, 'info', None), instrument_code, instrument_download_scheme)

    if task is None:
        provider = get_provider(instrument_download_scheme.master_user, instrument_download_scheme.provider)
        if not provider.is_valid_reference(instrument_code):
            raise ValueError('Invalid instrument_code value')

        options = {
            'instrument_download_scheme_id': instrument_download_scheme.id,
            'instrument_code': instrument_code,
        }
        with transaction.atomic():
            task = Task(
                master_user=master_user,
                member=member,
                provider=instrument_download_scheme.provider,
                status=Task.STATUS_PENDING,
                action=Task.ACTION_INSTRUMENT
            )
            task.options_object = options
            task.save()
            # transaction.on_commit(
            #     lambda: download_instrument_async.apply_async(kwargs={'task_id': task.id}, countdown=1))
            transaction.on_commit(lambda: download_instrument_async.apply_async(kwargs={'task_id': task.id}))
        return task, None, None
    else:
        if task.status == Task.STATUS_DONE:
            provider = get_provider(task.master_user, task.provider_id)

            options = task.options_object
            values = task.result_object.copy()
            if value_overrides:
                values.update(value_overrides)

            instrument_download_scheme_id = options['instrument_download_scheme_id']
            instrument_download_scheme = InstrumentDownloadScheme.objects.get(pk=instrument_download_scheme_id)

            instrument, errors = provider.create_instrument(instrument_download_scheme, values)
            return task, instrument, errors
        return task, None, None


@shared_task(name='integrations.download_instrument_pricing_async', bind=True, ignore_result=False)
def download_instrument_pricing_async(self, task_id):
    task = Task.objects.get(pk=task_id)
    _l.debug('download_instrument_pricing_async: master_user_id=%s, task=%s', task.master_user_id, task.info)

    task.add_celery_task_id(self.request.id)

    try:
        provider = get_provider(task.master_user, task.provider_id)
    except:
        _l.info('provider load error', exc_info=True)
        task.status = Task.STATUS_ERROR
        task.save()
        return

    if provider is None:
        _l.info('provider not found')
        task.status = Task.STATUS_ERROR
        task.save()
        return

    if task.status not in [Task.STATUS_PENDING, Task.STATUS_WAIT_RESPONSE]:
        _l.warn('invalid task status')
        return

    options = task.options_object

    try:
        result, is_ready = provider.download_instrument_pricing(options)
    except:
        _l.warn("provider processing error", exc_info=True)
        task.status = Task.STATUS_ERROR
    else:
        if is_ready:
            task.status = Task.STATUS_DONE
            task.result_object = result
        else:
            task.status = Task.STATUS_WAIT_RESPONSE

    response_id = options.get('response_id', None)
    if response_id:
        task.response_id = response_id
    task.options_object = options
    task.save()

    if task.status == Task.STATUS_WAIT_RESPONSE:
        if self.request.is_eager:
            time.sleep(provider.get_retry_delay())
        try:
            self.retry(countdown=provider.get_retry_delay(), max_retries=provider.get_max_retries())
            # self.retry(countdown=provider.get_retry_delay(), max_retries=provider.get_max_retries(), throw=False)
        except MaxRetriesExceededError:
            task.status = Task.STATUS_TIMEOUT
            task.save()
        return

    return task_id


@shared_task(name='integrations.download_currency_pricing_async', bind=True, ignore_result=False)
def download_currency_pricing_async(self, task_id):
    task = Task.objects.get(pk=task_id)
    _l.debug('download_currency_pricing_async: master_user_id=%s, task=%s', task.master_user_id, task.info)

    task.add_celery_task_id(self.request.id)

    try:
        provider = get_provider(task.master_user, task.provider_id)
    except:
        _l.info('provider load error', exc_info=True)
        task.status = Task.STATUS_ERROR
        task.save()
        return

    if provider is None:
        _l.info('provider not found')
        task.status = Task.STATUS_ERROR
        task.save()
        return

    if task.status not in [Task.STATUS_PENDING, Task.STATUS_WAIT_RESPONSE]:
        _l.warn('invalid task status')
        return

    options = task.options_object

    try:
        result, is_ready = provider.download_currency_pricing(options)
    except:
        _l.warn("provider processing error", exc_info=True)
        task.status = Task.STATUS_ERROR
    else:
        if is_ready:
            task.status = Task.STATUS_DONE
            task.result_object = result
        else:
            task.status = Task.STATUS_WAIT_RESPONSE

    response_id = options.get('response_id', None)
    if response_id:
        task.response_id = response_id

    task.options_object = options
    task.save()

    if task.status == Task.STATUS_WAIT_RESPONSE:
        if self.request.is_eager:
            time.sleep(provider.get_retry_delay())
        try:
            self.retry(countdown=provider.get_retry_delay(), max_retries=provider.get_max_retries())
            # self.retry(countdown=provider.get_retry_delay(), max_retries=provider.get_max_retries(), throw=False)
        except MaxRetriesExceededError:
            task.status = Task.STATUS_TIMEOUT
            task.save()
        return

    return task_id


@shared_task(name='integrations.download_pricing_async', bind=True, ignore_result=False)
def download_pricing_async(self, task_id):
    task = Task.objects.get(pk=task_id)
    _l.debug('download_pricing_async: master_user_id=%s, task=%s', task.master_user_id, task.info)

    if task.status not in [Task.STATUS_PENDING, Task.STATUS_WAIT_RESPONSE]:
        return

    task.add_celery_task_id(self.request.id)
    task.status = Task.STATUS_WAIT_RESPONSE

    master_user = task.master_user
    options = task.options_object

    instruments = Instrument.objects.select_related('price_download_scheme').filter(
        master_user=master_user
    ).exclude(
        daily_pricing_model=DailyPricingModel.SKIP
    )
    _l.debug('instruments: %s', [i.id for i in instruments])

    currencies = Currency.objects.select_related('price_download_scheme').filter(
        master_user=master_user
    ).exclude(
        daily_pricing_model=DailyPricingModel.SKIP
    )
    _l.debug('currencies: %s', [i.id for i in currencies])

    instruments_always = set()
    instruments_if_open = set()
    instruments_opened = set()
    for i in instruments:
        if i.daily_pricing_model_id in [DailyPricingModel.FORMULA_IF_OPEN, DailyPricingModel.PROVIDER_IF_OPEN]:
            instruments_if_open.add(i.id)
        elif i.daily_pricing_model_id in [DailyPricingModel.FORMULA_ALWAYS, DailyPricingModel.PROVIDER_ALWAYS]:
            instruments_always.add(i.id)

    currencies_always = set()
    currencies_if_open = set()
    currencies_opened = set()
    for i in currencies:
        if i.daily_pricing_model_id in [DailyPricingModel.FORMULA_IF_OPEN, DailyPricingModel.PROVIDER_IF_OPEN]:
            currencies_if_open.add(i.id)
        elif i.daily_pricing_model_id in [DailyPricingModel.FORMULA_ALWAYS, DailyPricingModel.PROVIDER_ALWAYS]:
            currencies_always.add(i.id)

    _l.debug('always: instruments=%s, currencies=%s',
             sorted(instruments_always), sorted(currencies_always))

    balance_date = parse_date_iso(options['balance_date'])
    _l.debug('calculate position report on %s for: instruments=%s, currencies=%s',
             balance_date, sorted(instruments_if_open), sorted(currencies_if_open))

    if balance_date and (instruments_if_open or currencies_if_open):
        report = Report(master_user=task.master_user, report_date=balance_date, detail_by_portfolio=True)
        _l.debug('calculate position report: %s', report)
        builder = ReportBuilder(instance=report)
        builder.build()
        for i in report.items:
            if i.type == ReportItem.TYPE_INSTRUMENT and not isclose(i.position_size, 0.0):
                instruments_opened.add(i.instrument.id)
            elif i.type == ReportItem.TYPE_CURRENCY and not isclose(i.position_size, 0.0):
                currencies_opened.add(i.currency.id)
        _l.debug('opened: instruments=%s, currencies=%s', sorted(instruments_opened), sorted(currencies_opened))

    instruments = instruments.filter(pk__in=(instruments_always | instruments_opened))
    _l.debug('instruments: %s', [i.id for i in instruments])

    currencies = currencies.filter(pk__in=(currencies_always | currencies_opened))
    _l.debug('currencies: %s', [i.id for i in currencies])

    price_download_schemes = {}

    instruments_by_scheme = defaultdict(list)
    instruments_by_formula = []
    for i in instruments:
        if i.daily_pricing_model_id in [DailyPricingModel.PROVIDER_ALWAYS, DailyPricingModel.PROVIDER_IF_OPEN]:
            if i.price_download_scheme_id and i.reference_for_pricing:
                instruments_by_scheme[i.price_download_scheme.id].append(i)
                price_download_schemes[i.price_download_scheme.id] = i.price_download_scheme
        elif i.daily_pricing_model_id in [DailyPricingModel.FORMULA_ALWAYS, DailyPricingModel.FORMULA_IF_OPEN]:
            instruments_by_formula.append(i)
    _l.debug('instruments_by_scheme: %s', instruments_by_scheme)
    _l.debug('instruments_by_formula: %s', instruments_by_formula)

    currencies_by_scheme = defaultdict(list)
    for i in currencies:
        if i.daily_pricing_model_id in [DailyPricingModel.PROVIDER_ALWAYS, DailyPricingModel.PROVIDER_IF_OPEN]:
            if i.price_download_scheme_id and i.reference_for_pricing:
                currencies_by_scheme[i.price_download_scheme.id].append(i)
                price_download_schemes[i.price_download_scheme.id] = i.price_download_scheme
    _l.debug('currencies_by_scheme: %s', currencies_by_scheme)

    # sub_tasks = []
    # celery_sub_tasks = []

    instrument_sub_tasks = []
    currency_sub_tasks = []

    def sub_tasks_submit():
        celery_sub_tasks = []

        for sub_task_id in instrument_sub_tasks:
            ct = download_instrument_pricing_async.s(task_id=sub_task_id)
            celery_sub_tasks.append(ct)

        for sub_task_id in currency_sub_tasks:
            ct = download_currency_pricing_async.s(task_id=sub_task_id)
            celery_sub_tasks.append(ct)

        _l.info('celery_sub_tasks: %s', celery_sub_tasks)
        if celery_sub_tasks:
            _l.info('use chord')
            sub_tasks = instrument_sub_tasks + currency_sub_tasks
            chord(celery_sub_tasks, download_pricing_wait.si(sub_tasks_id=sub_tasks, task_id=task_id)).apply_async()
        else:
            _l.info('use apply_async')
            download_pricing_wait.apply_async(kwargs={'sub_tasks_id': [], 'task_id': task_id})

    with transaction.atomic():
        instrument_task = defaultdict(list)
        for scheme_id, instruments0 in instruments_by_scheme.items():
            price_download_scheme = price_download_schemes[scheme_id]
            sub_options = options.copy()
            sub_options['price_download_scheme_id'] = price_download_scheme.id
            sub_options['instruments'] = [i.reference_for_pricing for i in instruments0]
            sub_options['instruments_pk'] = [i.id for i in instruments0]

            sub_task = Task(
                master_user=master_user,
                member=task.member,
                parent=task,
                provider=price_download_scheme.provider,
                status=Task.STATUS_PENDING,
                action=Task.ACTION_PRICING
            )
            sub_task.options_object = sub_options
            sub_task.save()

            instrument_sub_tasks.append(sub_task.id)
            # celery_sub_task = download_instrument_pricing_async.apply_async(kwargs={'task_id': sub_task.id})
            # celery_sub_tasks.append(celery_sub_task)

            for i in instruments0:
                instrument_task[i.id] = sub_task.id

        # for manual formula& calculate on final stage
        for i in instruments_by_formula:
            instrument_task[i.id] = None

        currency_task = defaultdict(list)
        for scheme_id, currencies0 in currencies_by_scheme.items():
            price_download_scheme = price_download_schemes[scheme_id]
            sub_options = options.copy()
            sub_options['price_download_scheme_id'] = price_download_scheme.id
            sub_options['currencies'] = [i.reference_for_pricing for i in currencies0]
            sub_options['currencies_pk'] = [i.id for i in currencies0]

            sub_task = Task(
                master_user=master_user,
                member=task.member,
                parent=task,
                provider=price_download_scheme.provider,
                status=Task.STATUS_PENDING,
                action=Task.ACTION_PRICING
            )
            sub_task.options_object = sub_options
            sub_task.save()

            currency_sub_tasks.append(sub_task.id)
            # celery_sub_task = download_currency_pricing_async.apply_async(kwargs={'task_id': sub_task.id})
            # celery_sub_tasks.append(celery_sub_task)

            for i in currencies0:
                currency_task[i.id] = sub_task.id

        options['instrument_task'] = instrument_task
        options['currency_task'] = currency_task
        options['sub_tasks'] = instrument_sub_tasks + currency_sub_tasks

        task.options_object = options
        task.save()

        # if self.request.is_eager:
        #     download_pricing_wait.apply_async(kwargs={'sub_tasks_id': sub_tasks, 'task_id': task_id})
        # else:
        #     if celery_sub_tasks:
        #         chord(celery_sub_tasks, download_pricing_wait.s(task_id=task_id)).apply_async()
        #     else:
        #         download_pricing_wait.apply_async(kwargs={'sub_tasks_id': [], 'task_id': task_id})

        transaction.on_commit(sub_tasks_submit)

    return task_id


@shared_task(name='integrations.download_pricing_wait', bind=True, ignore_result=False)
def download_pricing_wait(self, sub_tasks_id, task_id):
    task = Task.objects.get(pk=task_id)
    _l.debug('download_pricing_wait: master_user_id=%s, task=%s', task.master_user_id, task.info)

    if task.status != Task.STATUS_WAIT_RESPONSE:
        return

    task.add_celery_task_id(self.request.id)

    pricing_policies = [p for p in PricingPolicy.objects.filter(master_user=task.master_user)]

    options = task.options_object
    date_from = parse_date_iso(options['date_from'])
    date_to = parse_date_iso(options['date_to'])
    is_yesterday = options['is_yesterday']
    override_existed = options['override_existed']
    fill_days = options['fill_days']
    # sub_tasks_id = options['sub_tasks']
    instrument_task = options['instrument_task']
    currency_task = options['currency_task']

    result = {}
    errors = {}
    instruments_prices = []
    currencies_prices = []

    _l.debug('instrument_task: %s', instrument_task)
    _l.debug('currency_task: %s', currency_task)

    instruments_pk = [int(pk) for pk in instrument_task.keys()]
    _l.debug('instruments_pk: %s', instruments_pk)
    currencies_pk = [int(pk) for pk in currency_task.keys()]
    _l.debug('currencies_pk: %s', currencies_pk)

    _l.debug('sub_tasks_id: %s', sub_tasks_id)
    for sub_task in Task.objects.filter(pk__in=sub_tasks_id):
        _l.debug('sub_task: %s', sub_task.info)
        if sub_task.status != Task.STATUS_DONE:
            continue

        provider = get_provider(task=sub_task)

        sub_task_options = sub_task.options_object

        if 'instruments_pk' in sub_task_options:
            task_instruments_pk = sub_task_options['instruments_pk']
            task_instruments = Instrument.objects.filter(pk__in=task_instruments_pk)

            price_download_scheme_id = sub_task_options['price_download_scheme_id']
            price_download_scheme = PriceDownloadScheme.objects.get(pk=price_download_scheme_id)

            sub_task_instruments_prices, sub_task_errors = provider.create_instrument_pricing(
                price_download_scheme=price_download_scheme,
                options=sub_task_options,
                values=sub_task.result_object,
                instruments=task_instruments,
                pricing_policies=pricing_policies
            )

            instruments_prices += sub_task_instruments_prices
            errors.update(sub_task_errors)

        elif 'currencies_pk' in sub_task_options:
            task_currencies_pk = sub_task_options['currencies_pk']
            task_currencies = Currency.objects.filter(pk__in=task_currencies_pk)

            price_download_scheme_id = sub_task_options['price_download_scheme_id']
            price_download_scheme = PriceDownloadScheme.objects.get(pk=price_download_scheme_id)

            sub_task_currencies_prices, sub_task_errors = provider.create_currency_pricing(
                price_download_scheme=price_download_scheme,
                options=sub_task_options,
                values=sub_task.result_object,
                currencies=task_currencies,
                pricing_policies=pricing_policies
            )

            currencies_prices += sub_task_currencies_prices
            errors.update(sub_task_errors)

    instrument_for_manual_price = [int(i_id) for i_id, task_id in instrument_task.items() if task_id is None]
    _l.debug('instrument_for_manual_price: %s', instrument_for_manual_price)
    manual_instruments_prices, manual_instruments_errors = _create_instrument_manual_prices(
        options=options, instruments=instrument_for_manual_price)

    instruments_prices += manual_instruments_prices
    errors.update(manual_instruments_errors)

    if errors:
        options['errors'] = errors
        task.options_object = options
        task.result_object = result
        task.status = Task.STATUS_ERROR
        task.save()

    if fill_days > 0:
        fill_date_from = date_to + timedelta(days=1)
        instrument_last_price = [p for p in instruments_prices if p.date == date_to]
        _l.debug('instrument last prices: %s', instrument_last_price)
        for p in instrument_last_price:
            instruments_prices + fill_instrument_price(fill_date_from, fill_days, p)

        currency_last_price = [p for p in currencies_prices if p.date == date_to]
        _l.debug('currency last prices: %s', currency_last_price)
        for p in currency_last_price:
            currencies_prices += fill_currency_price(fill_date_from, fill_days, p)

    _l.debug('instruments_prices: %s', instruments_prices)
    _l.debug('currencies_prices: %s', currencies_prices)

    for p in instruments_prices:
        # p.calculate_accrued_price(save=False)
        accrued_price = p.instrument.get_accrued_price(p.date)
        p.accrued_price = accrued_price if accrued_price is not None else 0.0

    with transaction.atomic():
        _l.debug('instruments_pk: %s', instruments_pk)
        existed_instrument_prices = {
            (p.instrument_id, p.pricing_policy_id, p.date): p
            for p in PriceHistory.objects.filter(instrument__in=instruments_pk,
                                                 date__range=(date_from, date_to + timedelta(days=fill_days)))
            }
        _l.debug('existed_instrument_prices: %s', existed_instrument_prices)
        for p in instruments_prices:
            op = existed_instrument_prices.get((p.instrument_id, p.pricing_policy_id, p.date), None)
            if op is None:
                p.save()
            else:
                if override_existed:
                    op.principal_price = p.principal_price
                    op.accrued_price = p.accrued_price
                    op.save()

        _l.debug('currencies_pk: %s', currencies_pk)
        existed_currency_prices = {
            (p.currency_id, p.pricing_policy_id, p.date): p
            for p in CurrencyHistory.objects.filter(currency__in=currencies_pk,
                                                    date__range=(date_from, date_to + timedelta(days=fill_days)))
            }
        _l.debug('existed_currency_prices: %s', existed_currency_prices)
        for p in currencies_prices:
            op = existed_currency_prices.get((p.currency_id, p.pricing_policy_id, p.date), None)

            if op is None:
                p.save()
            else:
                if override_existed:
                    op.fx_rate = p.fx_rate
                    op.save()

        if is_yesterday:
            instrument_price_real = {(p.instrument_id, p.pricing_policy_id) for p in instruments_prices
                                     if p.date == date_to}
            currency_price_real = {(p.currency_id, p.pricing_policy_id) for p in currencies_prices
                                   if p.date == date_to}

            instrument_price_expected = set()
            currency_price_expected = set()
            for pp in pricing_policies:
                for i_id, task_id in instrument_task.items():
                    instrument_price_expected.add((int(i_id), pp.id))

                for c_id, task_id in currency_task.items():
                    currency_price_expected.add((int(c_id), pp.id))

            instrument_price_missed = instrument_price_expected.difference(instrument_price_real)
            # instrument_price_missed_objects = []
            # for instrument_id, pricing_policy_id in instrument_price_missed:
            #     op = existed_instrument_prices.get((instrument_id, pricing_policy_id, date_to), None)
            #     if op is None:
            #         op = PriceHistory(instrument_id=instrument_id, pricing_policy_id=pricing_policy_id, date=date_to)
            #     instrument_price_missed_objects.append(op)
            # instrument_price_missed = PriceHistorySerializer(instance=instrument_price_missed_objects, many=True,
            #                                                  context={'member': task.member}).data
            result['instrument_price_missed'] = list(instrument_price_missed)

            currency_price_missed = currency_price_expected.difference(currency_price_real)
            # currency_price_missed_objects = []
            # for currency_id, pricing_policy_id in currency_price_missed:
            #     op = existed_currency_prices.get((currency_id, pricing_policy_id, date_to), None)
            #     if op is None:
            #         op = CurrencyHistory(currency_id=currency_id, pricing_policy_id=pricing_policy_id, date=date_to)
            #     currency_price_missed_objects.append(op)
            # currency_price_missed = CurrencyHistorySerializer(instance=currency_price_missed_objects, many=True).data
            result['currency_price_missed'] = list(currency_price_missed)

            _l.debug('instrument_price_missed: %s', instrument_price_missed)
            _l.debug('currency_price_missed: %s', currency_price_missed)

        task.options_object = options
        task.result_object = result
        task.status = Task.STATUS_DONE
        task.save()

    return task_id


def _create_instrument_manual_prices(options, instruments):
    _l.debug('create_instrument_manual_prices: instruments=%s', instruments)

    date_from = parse_date_iso(options['date_from'])
    date_to = parse_date_iso(options['date_to'])
    is_yesterday = options['is_yesterday']
    fill_days = options['fill_days']

    errors = {}
    prices = []

    if is_yesterday:
        for i in Instrument.objects.filter(pk__in=instruments):
            for mf in i.manual_pricing_formulas.all():
                if mf.expr:
                    values = {
                        'd': date_to
                    }
                    try:
                        principal_price = formula.safe_eval(mf.expr, names=values)
                    except formula.InvalidExpression:
                        AbstractProvider.fail_manual_pricing_formula(errors, mf, values)
                        continue
                    price = PriceHistory(
                        instrument=i,
                        pricing_policy=mf.pricing_policy,
                        date=date_to,
                        principal_price=principal_price
                    )
                    prices.append(price)
    else:
        days = (date_to - date_from).days + 1

        for i in Instrument.objects.filter(pk__in=instruments):
            safe_instrument = {
                'id': i.id,
            }
            for mf in i.manual_pricing_formulas.all():
                if mf.expr:
                    for dt in rrule(freq=DAILY, count=days, dtstart=date_from):
                        d = dt.date()
                        values = {
                            'd': d,
                            'instrument': safe_instrument,
                        }
                        try:
                            principal_price = formula.safe_eval(mf.expr, names=values)
                        except formula.InvalidExpression:
                            AbstractProvider.fail_manual_pricing_formula(errors, mf, values)
                            continue
                        price = PriceHistory(
                            instrument=i,
                            pricing_policy=mf.pricing_policy,
                            date=d,
                            principal_price=principal_price
                        )
                        prices.append(price)

    return prices, errors


def download_pricing(master_user=None, member=None, date_from=None, date_to=None, is_yesterday=None, balance_date=None,
                     fill_days=None, override_existed=None, task=None):
    _l.debug('download_pricing: master_user_id=%s, task=%s, date_from=%s, date_to=%s, is_yesterday=%s,'
             ' balance_date=%s, fill_days=%s, override_existed=%s',
             getattr(master_user, 'id', None), getattr(task, 'info', None), date_from, date_to, is_yesterday,
             balance_date, fill_days, override_existed)
    if task is None:
        with transaction.atomic():
            options = {
                'date_from': date_from,
                'date_to': date_to,
                'is_yesterday': is_yesterday,
                'balance_date': balance_date,
                'fill_days': fill_days,
                'override_existed': override_existed,
            }
            task = Task(
                master_user=master_user,
                member=member,
                provider_id=None,
                status=Task.STATUS_PENDING,
                action=Task.ACTION_PRICING
            )
            task.options_object = options
            task.save()

            # transaction.on_commit(lambda: download_pricing_async.apply_async(kwargs={'task_id': task.id}, countdown=1))
            transaction.on_commit(lambda: download_pricing_async.apply_async(kwargs={'task_id': task.id}))
        return task, False
    else:
        if task.status == Task.STATUS_DONE:
            return task, True
        return task, False


@shared_task(name='integrations.download_pricing_auto', bind=True, ignore_result=True)
def download_pricing_auto(self, master_user_id):
    _l.info('download_pricing_auto: master_user=%s', master_user_id)
    try:
        master_user = MasterUser.objects.get(pk=master_user_id)
        sched = master_user.pricing_automated_schedule
    except ObjectDoesNotExist:
        # from poms.integrations.handlers import pricing_auto_cancel
        # pricing_auto_cancel(master_user_id)
        return

    with timezone.override(master_user.timezone or settings.TIME_ZONE):
        if getattr(settings, 'PRICING_AUTO_DOWNLOAD_ENABLED', True):
            now = date_now() - timedelta(days=1)
            date_from = now - timedelta(days=(sched.load_days if sched.load_days > 1 else 0))
            date_to = now
            is_yesterday = (date_from == now) and (date_to == now)
            balance_date = now - timedelta(days=sched.balance_day)
            task, _ = download_pricing(
                master_user=master_user,
                date_from=date_from,
                date_to=date_to,
                is_yesterday=is_yesterday, balance_date=balance_date,
                fill_days=sched.fill_days,
                override_existed=sched.override_existed
            )
        else:
            task = None

        sched.last_run_at = timezone.now()
        sched.last_run_task = task
        sched.save(update_fields=['last_run_at', 'last_run_task'])


@shared_task(name='integrations.download_pricing_auto_scheduler', bind=True, ignore_result=True)
def download_pricing_auto_scheduler(self):
    _l.debug('pricing_auto')
    schedule_qs = PricingAutomatedSchedule.objects.select_related('master_user').filter(
        is_enabled=True, next_run_at__lte=timezone.now()
    )
    _l.debug('count=%s', schedule_qs.count())
    for s in schedule_qs:
        master_user = s.master_user
        with timezone.override(master_user.timezone or settings.TIME_ZONE):
            next_run_at = timezone.localtime(s.next_run_at)
            s.schedule(save=True)
            _l.debug('pricing_auto: master_user=%s, next_run_at=%s',
                     master_user.id, s.next_run_at)
        download_pricing_auto.apply_async(kwargs={'master_user_id': master_user.id})
    _l.debug('finished')
