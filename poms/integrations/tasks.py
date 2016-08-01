from __future__ import unicode_literals, print_function

import json
import time
from datetime import datetime, timedelta
from logging import getLogger

from celery import shared_task, chain
from celery.exceptions import TimeoutError
from django.conf import settings
from django.core.mail import send_mail as django_send_mail, send_mass_mail as django_send_mass_mail, \
    mail_admins as django_mail_admins, mail_managers as django_mail_managers
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction, models
from django.utils import timezone

from poms.audit.models import AuthLogEntry
from poms.instruments.models import PriceDownloadMode
from poms.integrations.models import BloombergTask
from poms.integrations.providers.bloomberg import get_provider, BloombergException, str_to_date, \
    create_instrument_price_history, create_currency_price_history
from poms.integrations.storage import file_import_storage
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
    _l.debug('> file_import_delete: path=%s', path)
    try:
        file_import_storage.delete(path)
    except Exception:
        _l.error("Can't delete file %s", path, exc_info=True)


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


@shared_task(name='backend.bloomberg_send_request', bind=True, ignore_result=True)
def bloomberg_send_request(self, task_id):
    _l.info('bloomberg_send_request: task_id=%s', task_id)

    task = BloombergTask.objects.select_related('master_user', 'master_user__bloomberg_config').get(pk=task_id)
    if settings.BLOOMBERG_SANDBOX:
        provider = get_provider()
    else:
        master_user = task.master_user
        config = master_user.bloomberg_config
        cert, key = config.pair
        provider = get_provider(cert=cert, key=key)

    action = task.action
    params = json.loads(task.kwargs)

    try:
        if action == 'fields':
            response_id = None

        elif action == 'instrument':
            response_id = provider.get_instrument_send_request(
                instrument=params['instrument'],
                fields=params['fields']
            )

        elif action == 'pricing_latest':
            response_id = provider.get_pricing_latest_send_request(
                instruments=params['instruments']
            )

        elif action == 'pricing_history':
            date_from = datetime.strptime(params['date_from'], '%Y-%m-%d').date()
            date_to = datetime.strptime(params['date_to'], '%Y-%m-%d').date()
            response_id = provider.get_pricing_history_send_request(
                instruments=params['instruments'],
                date_from=date_from,
                date_to=date_to
            )

        else:
            raise BloombergException('Unknown action')

    except BloombergException:
        with transaction.atomic():
            task.status = BloombergTask.STATUS_ERROR
            task.save()
        raise

    with transaction.atomic():
        task.response_id = response_id
        task.status = BloombergTask.STATUS_REQUEST_SENT
        task.save()

    return task_id


@shared_task(name='backend.bloomberg_wait_reponse', bind=True, ignore_result=True)
def bloomberg_wait_reponse(self, task_id):
    _l.info('bloomberg_wait_reponse: task_id=%s', task_id)

    task = BloombergTask.objects.select_related('master_user', 'master_user__bloomberg_config').get(pk=task_id)

    if task.status == BloombergTask.STATUS_REQUEST_SENT:
        with transaction.atomic():
            task.status = BloombergTask.STATUS_WAIT_RESPONSE
            task.save()
    elif task.status == BloombergTask.STATUS_WAIT_RESPONSE:
        pass
    else:
        return

    if settings.BLOOMBERG_SANDBOX:
        provider = get_provider()
    else:
        master_user = task.master_user
        config = master_user.bloomberg_config
        cert, key = config.pair
        provider = get_provider(cert=cert, key=key)

    action = task.action
    response_id = task.response_id

    try:
        if action == 'fields':
            provider.get_fields()
            result = 'fields'

        elif action == 'instrument':
            result = provider.get_instrument_get_response(response_id)

        elif action == 'pricing_latest':
            result = provider.get_pricing_latest_get_response(response_id)

        elif action == 'pricing_history':
            result = provider.get_pricing_history_get_response(response_id)

        else:
            raise BloombergException('Unknown action')

    except BloombergException:
        with transaction.atomic():
            task.status = BloombergTask.STATUS_ERROR
            task.save()
        raise

    if result is None:
        if self.request.is_eager:
            time.sleep(settings.BLOOMBERG_RETRY_DELAY)

        raise self.retry(
            countdown=settings.BLOOMBERG_RETRY_DELAY,
            max_retries=settings.BLOOMBERG_MAX_RETRIES,
        )

    with transaction.atomic():
        task.result = json.dumps(result, cls=DjangoJSONEncoder, sort_keys=True, indent=2)
        task.status = BloombergTask.STATUS_DONE
        task.save()

    return task.id


def bloomberg_call(master_user=None, member=None, action=None, params=None):
    master_user_id = master_user.id if isinstance(master_user, models.Model)  else master_user
    if member:
        member_id = member.id if isinstance(member, models.Model) else member
    else:
        member_id = None

    with transaction.atomic():
        bt = BloombergTask.objects.create(
            master_user_id=master_user_id,
            member_id=member_id,
            status=BloombergTask.STATUS_PENDING,
            action=action,
            kwargs=json.dumps(params, cls=DjangoJSONEncoder, sort_keys=True, indent=2),
        )
        transaction.on_commit(
            lambda: chain(bloomberg_send_request.s(bt.pk), bloomberg_wait_reponse.s()).apply_async(countdown=1))

    return bt.pk
    # return chain(
    #     bloomberg_send_request.s(bt.id),
    #     bloomberg_wait_reponse.s()
    # ).apply_async(countdown=1)


def bloomberg_instrument(master_user=None, member=None, instrument=None, fields=None):
    return bloomberg_call(
        master_user=master_user,
        member=member,
        action='instrument',
        params={
            'instrument': instrument,
            'fields': fields,
        }
    )


def bloomberg_pricing_latest(master_user=None, member=None, instruments=None):
    return bloomberg_call(
        master_user=master_user,
        member=member,
        action='pricing_latest',
        params={
            'instruments': instruments,
        }
    )


def bloomberg_pricing_history(master_user=None, member=None, instruments=None, date_from=None, date_to=None):
    return bloomberg_call(
        master_user=master_user,
        member=member,
        action='pricing_history',
        params={
            'instruments': instruments,
            'date_from': date_from,
            'date_to': date_to,
        }
    )


@shared_task(name='backend.bloomberg_price_history_auto_save', bind=True, ignore_result=True)
def bloomberg_price_history_auto_save(self, task_id):
    _l.debug('> bloomberg_price_history_auto_save: task_id=%s', task_id)

    task = BloombergTask.objects.get(pk=task_id)
    master_user = task.master_user
    kwargs = task.kwargs_object
    task_res = task.result_object
    pricing_policies = list(task.master_user.pricing_policies.all())
    download_modes = [PriceDownloadMode.AUTO, PriceDownloadMode.IF_PORTFOLIO]

    date_from = str_to_date(kwargs['date_from'])
    date_to = str_to_date(kwargs['date_to'])

    _l.debug('master_user=%s', master_user.id)

    instruments = []
    for instr in master_user.instruments.order_by('id').all():
        if instr.price_download_mode_id not in download_modes:
            continue
        if str(instr.id) in task_res:
            _l.debug('instrument=%s', instr.id)
            instruments.append(instr)

    currencies = []
    for ccy in master_user.currencies.order_by('id').all():
        if ccy.history_download_mode_id not in download_modes:
            continue
        if str(ccy.id) in task_res:
            _l.debug('currency=%s', ccy.id)
            currencies.append(ccy)

    create_instrument_price_history(
        task=task,
        instruments=instruments,
        pricing_policies=pricing_policies,
        save=False,
        date_range=(date_from, date_to),
        fail_silently=True
    )
    create_currency_price_history(
        task=task,
        currencies=currencies,
        pricing_policies=pricing_policies,
        save=False,
        date_range=(date_from, date_to),
        fail_silently=True
    )

    _l.debug('<')


@shared_task(name='backend.bloomberg_price_history_auto', bind=True, ignore_result=True)
def bloomberg_price_history_auto(self):
    _l.debug('-' * 79)
    _l.debug('bloomberg_price_history_auto: >')

    if not settings.BLOOMBERG_SANDBOX:
        _l.warn('only sandbox')
        _l.debug('<')

    req_date = timezone.now().date() - timedelta(days=1)
    download_modes = [PriceDownloadMode.AUTO, PriceDownloadMode.IF_PORTFOLIO]

    for master_user in MasterUser.objects. \
            filter(bloomberg_config__isnull=False). \
            select_related('bloomberg_config'). \
            prefetch_related('instruments', 'currencies'):

        bloomberg_config = master_user.bloomberg_config
        if not bloomberg_config.is_ready:
            continue

        _l.debug('master_user=%s', master_user.id)

        instruments = []

        for instr in master_user.instruments.all():
            if instr.price_download_mode_id not in download_modes:
                continue
            _l.debug('instrument=%s', instr.id)

            instruments.append({
                'code': str(instr.id),
                'industry': 'Corp',
            })

        for ccy in master_user.currencies.all():
            if ccy.history_download_mode_id not in download_modes:
                continue
            _l.debug('currency=%s', ccy.id)

            instruments.append({
                'code': str(ccy.id),
                'industry': 'CCY',
            })

        params = {
            'instruments': instruments,
            'date_from': req_date,
            'date_to': req_date,
        }

        with transaction.atomic():
            bt = BloombergTask.objects.create(
                master_user_id=master_user.id,
                status=BloombergTask.STATUS_PENDING,
                action='pricing_history',
                kwargs=json.dumps(params, cls=DjangoJSONEncoder, sort_keys=True, indent=2),
            )
            transaction.on_commit(
                lambda: chain(bloomberg_send_request.s(bt.pk), bloomberg_wait_reponse.s(),
                              bloomberg_price_history_auto_save.s()).apply_async())

    _l.debug('<')
