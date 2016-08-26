from __future__ import unicode_literals, print_function

import json
import time
from collections import defaultdict
from datetime import timedelta, date
from logging import getLogger

import six
from celery import shared_task, chord
from celery.exceptions import TimeoutError, MaxRetriesExceededError
from dateutil.rrule import rrule, DAILY
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail as django_send_mail, send_mass_mail as django_send_mass_mail, \
    mail_admins as django_mail_admins, mail_managers as django_mail_managers
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.utils import timezone

from poms.audit.models import AuthLogEntry
from poms.common import formula
from poms.common.utils import date_now
from poms.currencies.models import Currency, CurrencyHistory
from poms.currencies.serializers import CurrencyHistorySerializer
from poms.instruments.models import Instrument, DailyPricingModel, PricingPolicy, PriceHistory
from poms.instruments.serializers import PriceHistorySerializer
from poms.integrations.models import Task, PriceDownloadScheme, InstrumentDownloadScheme
from poms.integrations.providers.base import get_provider, parse_date_iso, fill_instrument_price
from poms.integrations.storage import import_file_storage
from poms.reports.backends.balance import BalanceReport2PositionBuilder
from poms.reports.models import BalanceReport
from poms.users.models import MasterUser

_l = getLogger('poms.integrations')


@shared_task(name='backend.health_check')
def health_check_async():
    return True


def health_check():
    result = health_check_async.apply_async()
    try:
        return result.get(timeout=0.5, interval=0.1)
    except TimeoutError:
        pass
    return False


@shared_task(name='backend.send_mail_async', ignore_result=True)
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


@shared_task(name='backend.send_mass_mail', ignore_result=True)
def send_mass_mail_async(messages):
    django_send_mass_mail(messages, fail_silently=True)


def send_mass_mail(messages):
    send_mass_mail_async.apply_async(kwargs={
        'messages': messages,
    })


@shared_task(name='backend.mail_admins', ignore_result=True)
def mail_admins_async(subject, message):
    django_mail_admins(subject, message, fail_silently=True, )


def mail_admins(subject, message):
    mail_admins_async.apply_async(kwargs={
        'subject': subject,
        'message': message,
    })


@shared_task(name='backend.mail_managers', ignore_result=True)
def mail_managers_async(subject, message):
    django_mail_managers(subject, message, fail_silently=True, )


def mail_managers(subject, message):
    mail_managers_async.apply_async(kwargs={
        'subject': subject,
        'message': message,
    })


@shared_task(name='backend.file_import_delete', ignore_result=True)
def file_import_delete_async(path):
    _l.debug('file_import_delete_async: path=%s', path)
    import_file_storage.delete(path)


def schedule_file_import_delete(path, countdown=None):
    if countdown is None:
        countdown = 600
    _l.debug('schedule_file_import_delete: path=%s, countdown=%s', path, countdown)
    file_import_delete_async.apply_async(countdown=countdown, kwargs={
        'path': path,
    })


@shared_task(name='backend.auth_log_statistics', ignore_result=True)
def auth_log_statistics():
    logged_in_count = AuthLogEntry.objects.filter(is_success=True).count()
    login_failed_count = AuthLogEntry.objects.filter(is_success=False).count()
    _l.debug('auth (total): logged_in=%s, login_failed=%s', logged_in_count, login_failed_count)

    now = timezone.now().date()
    logged_in_count = AuthLogEntry.objects.filter(is_success=True, date__startswith=now).count()
    login_failed_count = AuthLogEntry.objects.filter(is_success=False, date__startswith=now).count()
    _l.debug('auth (today): logged_in=%s, login_failed=%s', logged_in_count, login_failed_count)


@shared_task(name='backend.download_instrument', bind=True, ignore_result=True)
def download_instrument_async(self, task_id=None):
    task = Task.objects.get(pk=task_id)
    _l.debug('download_instrument_async: master_user_id=%s, task=%s', task.master_user_id, task.id, task)

    try:
        provider = get_provider(task.master_user, task.provider_id)
    except:
        task.status = Task.STATUS_ERROR
        task.save()
        raise

    if provider is None:
        task.status = Task.STATUS_ERROR
        task.save()
        return

    if task.status not in [Task.STATUS_PENDING, Task.STATUS_WAIT_RESPONSE]:
        return
    options = task.options_object

    try:
        result, is_ready = provider.download_instrument(options)
    except Exception:
        task.status = Task.STATUS_ERROR
        _l.error('fatal provider error', exc_info=True)
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
            self.retry(countdown=provider.get_retry_delay(), max_retries=provider.get_max_retries(), throw=False)
        except MaxRetriesExceededError:
            task.status = Task.STATUS_TIMEOUT
            task.save()
        return

    return task_id


def download_instrument(instrument_code=None, instrument_download_scheme=None, master_user=None, member=None,
                        task=None, value_overrides=None):
    _l.debug('download_pricing: master_user_id=%s, task=%s, instrument_code=%s, instrument_download_scheme=%s',
             getattr(master_user, 'id', None), task, instrument_code, instrument_download_scheme)

    if task is None:
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
            transaction.on_commit(
                lambda: download_instrument_async.apply_async(kwargs={'task_id': task.id}, countdown=1))
        return task, None
    else:
        if task.status == Task.STATUS_DONE:
            provider = get_provider(task.master_user, task.provider_id)

            options = task.options_object
            values = task.result_object.copy()
            if value_overrides:
                values.update(value_overrides)

            instrument_download_scheme_id = options['instrument_download_scheme_id']
            instrument_download_scheme = InstrumentDownloadScheme.objects.get(pk=instrument_download_scheme_id)

            instrument = provider.create_instrument(instrument_download_scheme, values)
            return task, instrument
        return task, None


@shared_task(name='backend.download_instrument_pricing_async', bind=True, ignore_result=False)
def download_instrument_pricing_async(self, task_id):
    task = Task.objects.get(pk=task_id)
    _l.debug('download_instrument_pricing_async: master_user_id=%s, task=%s', task.master_user_id, task)

    try:
        provider = get_provider(task.master_user, task.provider_id)
    except:
        task.status = Task.STATUS_ERROR
        task.save()
        return

    if provider is None:
        task.status = Task.STATUS_ERROR
        task.save()
        return

    if task.status not in [Task.STATUS_PENDING, Task.STATUS_WAIT_RESPONSE]:
        return

    options = task.options_object

    try:
        result, is_ready = provider.download_instrument_pricing(options)
    except Exception:
        task.status = Task.STATUS_ERROR
        _l.error('fatal provider error', exc_info=True)
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
            self.retry(countdown=provider.get_retry_delay(), max_retries=provider.get_max_retries(), throw=False)
        except MaxRetriesExceededError:
            task.status = Task.STATUS_TIMEOUT
            task.save()
        return

    return task_id


@shared_task(name='backend.download_currency_pricing_async', bind=True, ignore_result=False)
def download_currency_pricing_async(self, task_id):
    task = Task.objects.get(pk=task_id)
    _l.debug('download_currency_pricing_async: master_user_id=%s, task=%s', task.master_user_id, task)

    try:
        provider = get_provider(task.master_user, task.provider_id)
    except:
        task.status = Task.STATUS_ERROR
        task.save()
        return

    if provider is None:
        task.status = Task.STATUS_ERROR
        task.save()
        return

    if task.status not in [Task.STATUS_PENDING, Task.STATUS_WAIT_RESPONSE]:
        return

    options = task.options_object

    try:
        result, is_ready = provider.download_currency_pricing(options)
    except Exception:
        task.status = Task.STATUS_ERROR
        _l.error('fatal provider error', exc_info=True)
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
            self.retry(countdown=provider.get_retry_delay(), max_retries=provider.get_max_retries(), throw=False)
        except MaxRetriesExceededError:
            task.status = Task.STATUS_TIMEOUT
            task.save()
        return

    return task_id


@shared_task(name='backend.download_pricing_async', bind=True, ignore_result=True)
def download_pricing_async(self, task_id):
    task = Task.objects.get(pk=task_id)
    _l.debug('download_pricing_async: master_user_id=%s, task=%s', task.master_user_id, task)

    if task.status not in [Task.STATUS_PENDING, Task.STATUS_WAIT_RESPONSE]:
        return

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
        # TODO: calculate balance and than filter instruments & currencies
        report = BalanceReport(master_user=task.master_user, begin_date=date.min, end_date=balance_date,
                               use_portfolio=True, show_transaction_details=False)
        _l.debug('calculate position report: %s', report)
        builder = BalanceReport2PositionBuilder(instance=report)
        builder.build()
        for i in report.items:
            if i.instrument:
                instruments_opened.add(i.instrument.id)
            elif i.currency:
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

        # if self.request.is_eager:
        #     sub_tasks = instrument_sub_tasks + currency_sub_tasks
        #     download_pricing_wait.apply_async(kwargs={'sub_tasks_id': sub_tasks, 'task_id': task_id})
        # else:
        if celery_sub_tasks:
            sub_tasks = instrument_sub_tasks + currency_sub_tasks
            chord(celery_sub_tasks, download_pricing_wait.si(sub_tasks_id=sub_tasks, task_id=task_id)).apply_async()
        else:
            download_pricing_wait.apply_async(kwargs={'sub_tasks_id': [], 'task_id': task_id})

    with transaction.atomic():
        instrument_task = defaultdict(list)
        for scheme_id, instruments0 in six.iteritems(instruments_by_scheme):
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
        for scheme_id, currencies0 in six.iteritems(currencies_by_scheme):
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


@shared_task(name='backend.download_pricing_wait', bind=True, ignore_result=True)
def download_pricing_wait(self, sub_tasks_id, task_id):
    task = Task.objects.get(pk=task_id)
    _l.debug('download_pricing_wait: master_user_id=%s, task=%s', task.master_user_id, task)

    if task.status != Task.STATUS_WAIT_RESPONSE:
        return

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
    # currency_task = result['currency_task']

    instrument_prices = []
    currency_prices = []

    for sub_task in Task.objects.filter(pk__in=sub_tasks_id):
        _l.debug('sub_task: %s', sub_task)
        if sub_task.status != Task.STATUS_DONE:
            continue

        provider = get_provider(task=sub_task)

        subtask_options = sub_task.options_object

        if 'instruments_pk' in subtask_options:
            instruments_pk = subtask_options['instruments_pk']
            instruments = Instrument.objects.filter(pk__in=instruments_pk)
            price_download_scheme_id = subtask_options['price_download_scheme_id']
            price_download_scheme = PriceDownloadScheme.objects.get(pk=price_download_scheme_id)

            instrument_prices += provider.create_instrument_pricing(
                price_download_scheme=price_download_scheme,
                options=subtask_options,
                values=sub_task.result_object,
                instruments=instruments,
                pricing_policies=pricing_policies
            )

        elif 'currencies_pk' in subtask_options:
            currencies_pk = subtask_options['currencies_pk']
            currencies = Currency.objects.filter(pk__in=currencies_pk)
            price_download_scheme_id = subtask_options['price_download_scheme_id']
            price_download_scheme = PriceDownloadScheme.objects.get(pk=price_download_scheme_id)

            currency_prices += provider.create_currency_pricing(
                price_download_scheme=price_download_scheme,
                options=subtask_options,
                values=sub_task.result_object,
                currencies=currencies,
                pricing_policies=pricing_policies
            )

    instrument_for_manual_price = [i_id for i_id, task_id in six.iteritems(instrument_task) if task_id is None]
    instrument_prices += _create_instrument_manual_prices(options=options, instruments=instrument_for_manual_price)

    _l.debug('instrument prices: %s',
             json.dumps([(p.instrument_id, p.pricing_policy_id, p.date) for p in instrument_prices],
                        cls=DjangoJSONEncoder))
    _l.debug('currency prices: %s',
             json.dumps([(p.currency_id, p.pricing_policy_id, p.date) for p in currency_prices],
                        cls=DjangoJSONEncoder))

    with transaction.atomic():
        existed_instrument_prices = {
            (p.instrument_id, p.pricing_policy_id, p.date): p
            for p in PriceHistory.objects.filter(instrument__in={np.instrument_id for np in instrument_prices},
                                                 date__range=(date_from, date_to + timedelta(days=fill_days)))
            }
        for p in instrument_prices:
            op = existed_instrument_prices.get(
                (p.instrument_id, p.pricing_policy_id, p.date),
                None
            )
            if op is None:
                p.save()
            else:
                if override_existed:
                    op.principal_price = p.principal_price
                    op.accrued_price = p.accrued_price
                    op.save()

        existed_currency_prices = {
            (p.currency_id, p.pricing_policy_id, p.date): p
            for p in CurrencyHistory.objects.filter(currency__in={np.currency_id for np in currency_prices},
                                                    date__range=(date_from, date_to + timedelta(days=fill_days)))
            }
        for p in currency_prices:
            op = existed_currency_prices.get(
                (p.currency_id, p.pricing_policy_id, p.date),
                None
            )

            if op is None:
                p.save()
            else:
                if override_existed:
                    op.fx_rate = p.fx_rate
                    op.save()

        if is_yesterday:
            instrument_price_real = {
                (p.instrument_id, p.pricing_policy_id)
                for p in instrument_prices
                if p.date == date_to
                }
            currency_price_real = {
                (p.currency_id, p.pricing_policy_id)
                for p in currency_prices
                if p.date == date_to
                }

            instrument_price_expected = set()
            currency_price_expected = set()
            for pp in pricing_policies:
                for i_id, task_id in six.iteritems(instrument_task):
                    instrument_price_expected.add(
                        (int(i_id), pp.id)
                    )

                for c_id, task_id in six.iteritems(currency_task):
                    currency_price_expected.add(
                        (int(c_id), pp.id)
                    )

            instrument_price_missed = instrument_price_expected.difference(instrument_price_real)
            instrument_price_missed_objects = []
            for instrument_id, pricing_policy_id in instrument_price_missed:
                instrument_price_missed_objects.append(
                    PriceHistory(instrument_id=instrument_id, pricing_policy_id=pricing_policy_id, date=date_to)
                )
            instrument_price_missed = PriceHistorySerializer(instance=instrument_price_missed_objects, many=True).data
            result['instrument_price_missed'] = instrument_price_missed

            currency_price_missed = currency_price_expected.difference(currency_price_real)
            currency_price_missed_objects = []
            for currency_id, pricing_policy_id in currency_price_missed:
                currency_price_missed_objects.append(
                    CurrencyHistory(currency_id=currency_id, pricing_policy_id=pricing_policy_id, date=date_to)
                )
            currency_price_missed = CurrencyHistorySerializer(instance=currency_price_missed_objects, many=True).data
            result['currency_price_missed'] = currency_price_missed

            _l.debug('missed instrument prices: %s',
                     json.dumps(
                         [(p.instrument_id, p.pricing_policy_id, p.date) for p in instrument_price_missed_objects],
                         cls=DjangoJSONEncoder))
            _l.debug('missed currency prices: %s',
                     json.dumps([(p.currency_id, p.pricing_policy_id, p.date) for p in currency_price_missed_objects],
                                cls=DjangoJSONEncoder))

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

    prices = []
    if is_yesterday:
        for i in Instrument.objects.filter(pk__in=instruments):
            for mf in i.manual_pricing_formulas.all():
                if not mf.expr:
                    continue
                values = {
                    'd': date_to
                }
                principal_price = formula.safe_eval(mf.expr, names=values)
                price = PriceHistory(
                    instrument=i,
                    pricing_policy=mf.pricing_policy,
                    date=date_to,
                    principal_price=principal_price
                )
                prices.append(price)

                if fill_days:
                    prices += fill_instrument_price(date_to + timedelta(days=1), fill_days, price)
    else:
        days = (date_to - date_from).days + 1

        for i in Instrument.objects.filter(pk__in=instruments):
            safe_instrument = {
                'id': i.id,
            }
            for mf in i.manual_pricing_formulas.all():
                if not mf.expr:
                    continue
                for dt in rrule(freq=DAILY, count=days, dtstart=date_from):
                    d = dt.date()
                    values = {
                        'd': d,
                        'instrument': safe_instrument,
                    }
                    principal_price = formula.safe_eval(mf.expr, names=values)
                    price = PriceHistory(
                        instrument=i,
                        pricing_policy=mf.pricing_policy,
                        date=d,
                        principal_price=principal_price
                    )
                    prices.append(price)
    return prices


def download_pricing(master_user=None, member=None, date_from=None, date_to=None, is_yesterday=None, balance_date=None,
                     fill_days=None, override_existed=None, task=None):
    _l.debug('download_pricing: master_user_id=%s, task=%s, date_from=%s, date_to=%s, is_yesterday=%s,'
             ' balance_date=%s, fill_days=%s, override_existed=%s',
             getattr(master_user, 'id', None), task, date_from, date_to, is_yesterday,
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

            transaction.on_commit(
                lambda: download_pricing_async.apply_async(kwargs={'task_id': task.id}, countdown=1))
        return task, False
    else:
        if task.status == Task.STATUS_DONE:
            return task, True
        return task, False


@shared_task(name='backend.download_pricing_auto', bind=True, ignore_result=True)
def download_pricing_auto(self, master_user_id):
    _l.info('download_pricing_auto: master_user=%s', master_user_id)
    try:
        master_user = MasterUser.objects.get(pk=master_user_id)
        pricing_automated_schedule = master_user.pricing_automated_schedule
    except ObjectDoesNotExist:
        from poms.integrations.handlers import pricing_auto_cancel
        pricing_auto_cancel(master_user_id)
        return

    if getattr(settings, 'PRICING_AUTO_DOWNLOAD_ENABLED', True):
        _l.warning('PRICING_AUTO_DOWNLOAD_ENABLED is False')
        return

    # class PricingAutomatedSchedule(models.Model):
    #     master_user = models.OneToOneField('users.MasterUser', related_name='pricing_automated_schedule',
    #                                        verbose_name=_('master user'))
    #
    #     is_enabled = models.BooleanField(default=True)
    #     cron_expr = models.CharField(max_length=255, blank=True, default='', validators=[validate_crontab],
    #                                  help_text=_('Format is "* * * * *" (m/h/d/dM/MY)'))
    #     balance_day = models.SmallIntegerField(default=0)
    #     load_days = models.SmallIntegerField(default=1)
    #     fill_days = models.SmallIntegerField(default=0)
    #     override_existed = models.BooleanField(default=True)

    now = date_now() - timedelta(days=1)
    date_from = now - timedelta(days=abs(pricing_automated_schedule.load_days))
    date_to = now
    is_yesterday = (date_from == now) and (date_to == now)
    balance_date = now - timedelta(days=abs(pricing_automated_schedule.balance_day))
    download_pricing(
        master_user=master_user,
        date_from=date_from,
        date_to=date_to,
        is_yesterday=is_yesterday, balance_date=balance_date,
        fill_days=pricing_automated_schedule.fill_days,
        override_existed=pricing_automated_schedule.override_existed
    )
