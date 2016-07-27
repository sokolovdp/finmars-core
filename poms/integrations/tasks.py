from __future__ import unicode_literals, print_function

from logging import getLogger

import six
from celery import shared_task, chain
from celery.exceptions import TimeoutError, MaxRetriesExceededError
from dateutil import parser

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
    from django.core.mail import send_mail
    send_mail(subject, message, from_email, recipient_list, fail_silently=True, html_message=html_message)


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
    from django.core.mail import send_mass_mail
    send_mass_mail(messages, fail_silently=True)


def send_mass_mail(messages):
    send_mass_mail_async.apply_async(kwargs={
        'messages': messages,
    })


@shared_task(name='backend.mail_admins', ignore_result=True)
def mail_admins_async(subject, message):
    from django.core.mail import mail_admins
    mail_admins(subject, message, fail_silently=True, )


def mail_admins(subject, message):
    mail_admins_async.apply_async(kwargs={
        'subject': subject,
        'message': message,
    })


@shared_task(name='backend.mail_managers', ignore_result=True)
def mail_managers_async(subject, message):
    from django.core.mail import mail_managers
    mail_managers(subject, message, fail_silently=True, )


def mail_managers(subject, message):
    mail_managers_async.apply_async(kwargs={
        'subject': subject,
        'message': message,
    })


@shared_task(name='backend.file_import_delete', ignore_result=True)
def file_import_delete_async(path):
    _l.debug('file_import_delete: path=%s', path)
    # from poms.integrations.storages import FileImportStorage
    # storage = FileImportStorage()
    # try:
    #     storage.delete(path)
    # except Exception as e:
    #     _l.error("Can't delete file %s", path, exc_info=True)


def schedule_file_import_delete(path, countdown=None):
    if countdown is None:
        countdown = 600
    _l.debug('schedule_file_import_delete: path=%s, countdown=%s', path, countdown)
    file_import_delete_async.apply_async(countdown=countdown, kwargs={
        'path': path,
    })


@shared_task(name='backend.auth_log_statistics', ignore_result=True)
def auth_log_statistics():
    from django.utils import timezone
    from poms.audit.models import AuthLogEntry

    logged_in_count = AuthLogEntry.objects.filter(is_success=True).count()
    login_failed_count = AuthLogEntry.objects.filter(is_success=False).count()
    _l.debug('auth (total): logged_in=%s, login_failed=%s', logged_in_count, login_failed_count)

    now = timezone.now().date()
    logged_in_count = AuthLogEntry.objects.filter(is_success=True, date__startswith=now).count()
    login_failed_count = AuthLogEntry.objects.filter(is_success=False, date__startswith=now).count()
    _l.debug('auth (today): logged_in=%s, login_failed=%s', logged_in_count, login_failed_count)


@shared_task(name='backend.bloomberg_get_response', bind=True, ignore_result=True,
             default_retry_delay=1, max_retries=10)
def bloomberg_get_response_async(self, entry_id):
    from poms.integrations.models import BloombergRequestLogEntry
    _l.info('bloomberg_receive_async: entry_id=%s, attempt=%s', entry_id, self.request.retries)
    try:
        BloombergRequestLogEntry.objects.get(pk=entry_id)
        raise self.retry()
    except BloombergRequestLogEntry.DoesNotExist:
        pass
    except MaxRetriesExceededError:
        _l.error('bloomberg_receive_async: entry_id=%s, MaxRetriesExceededError', entry_id)
        pass


def bloomberg_get_response(entry_id):
    bloomberg_get_response_async.apply_async(
        kwargs={
            'entry_id': entry_id
        },
        countdown=1
    )


@shared_task(name='backend.test123', bind=True, default_retry_delay=1, max_retries=10)
def test123(self, v):
    # some call bloomberg
    if self.request.retries == 0:
        # first call
        pass

    is_ready = self.request.retries > 3
    if is_ready:
        if v == 0:
            raise ValueError()
        import uuid
        return uuid.uuid4().hex
    raise self.retry()


@shared_task(name='backend.bloomberg_send_request', bind=True)
def bloomberg_send_request(self, master_user_id, action, params):
    _l.info('bloomberg_send_request: master_user=%s, action=%s, params=%s', master_user_id, action, params)
    from poms.users.models import MasterUser
    from poms.integrations.providers.bloomberg import FakeBloomberDataProvider
    master_user = MasterUser.objects.get(pk=master_user_id)
    context = {'master_user': master_user, 'member': None}
    # p12cert = os.environ['TEST_BLOOMBERG_CERT']
    # password = os.environ['TEST_BLOOMBERG_CERT_PASSWORD']
    # cert, key = get_certs_from_file(p12cert, password)
    # b = FakeBloomberDataProvider(cert=cert, key=key, context=context)
    b = FakeBloomberDataProvider(context=context)

    if action == 'fields':
        return master_user_id, action, None

    elif action == 'instrument':
        response_id = b.get_instrument_send_request(
            instrument=params['instrument'],
            fields=params['fields']
        )
        return master_user_id, action, response_id

    elif action == 'pricing_latest':
        response_id = b.get_pricing_latest_send_request(
            instruments=params['instruments']
        )
        return master_user_id, action, response_id

    elif action == 'pricing_history':
        response_id = b.get_pricing_history_send_request(
            instruments=params['instruments'],
            date_from=parser.parse(params['date_from']).date(),
            date_to=parser.parse(params['date_to']).date()
        )
        return master_user_id, action, response_id

    raise RuntimeError('Unknown action')


@shared_task(name='backend.bloomberg_wait_reponse', bind=True, default_retry_delay=1, max_retries=10)
def bloomberg_wait_reponse(self, req):
    master_user_id, action, response_id = req
    _l.info('bloomberg_wait_reponse: master_user=%s, action=%s, response_id=%s', master_user_id, action, response_id)

    from poms.users.models import MasterUser
    from poms.integrations.providers.bloomberg import FakeBloomberDataProvider
    master_user = MasterUser.objects.get(pk=master_user_id)
    context = {'master_user': master_user, 'member': None}
    # p12cert = os.environ['TEST_BLOOMBERG_CERT']
    # password = os.environ['TEST_BLOOMBERG_CERT_PASSWORD']
    # cert, key = get_certs_from_file(p12cert, password)
    # b = FakeBloomberDataProvider(cert=cert, key=key, context=context)
    b = FakeBloomberDataProvider(context=context)

    if action == 'fields':
        b.get_fields()
        return 'OK'

    elif action == 'instrument':
        result = b.get_instrument_get_response(response_id)
        if result is None:
            raise self.retry()
        return result
    elif action == 'pricing_latest':
        result = b.get_pricing_latest_get_response(response_id)
        if result is None:
            raise self.retry()
        return result
    elif action == 'pricing_history':
        result = b.get_pricing_history_get_response(response_id)
        if result is None:
            raise self.retry()
        for k, instr in six.iteritems(result):
            for r in instr:
                r['date'] = '%s' % r['date']
        return result

    raise RuntimeError('Unknown action')


def bloomberg_async(master_user_id, action, params):
    if 'date_from' in params:
        params['date_from'] = '%s' % params['date_from']
    if 'date_to' in params:
        params['date_to'] = '%s' % params['date_to']
    return chain(
        bloomberg_send_request.s(),
        bloomberg_wait_reponse.s()
    ).apply_async([master_user_id, action, params])
