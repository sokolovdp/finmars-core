import logging

from celery import shared_task
from celery.exceptions import TimeoutError

_l = logging.getLogger('poms.integrations')


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
