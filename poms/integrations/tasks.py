from celery import shared_task


@shared_task(name='backend.health_check')
def health_check_async():
    send_mail('send_mail', 'send_mail', None, ['ailyukhin@vitaminsoft.com'])
    mail_admins('mail_admins', 'mail_admins')
    mail_managers('mail_managers', 'mail_managers')
    return True


def health_check():
    result = health_check_async.apply_async()
    try:
        return result.get(timeout=1, interval=0.1)
    except TimeoutError:
        pass
    return False


@shared_task(name='backend.send_mail_async', ignore_result=True)
def send_mail_async(subject, message, from_email, recipient_list):
    from django.core.mail import send_mail
    send_mail(subject, message, from_email, recipient_list, fail_silently=True, )


def send_mail(subject, message, from_email, recipient_list):
    send_mail_async.apply_async(kwargs={
        'subject': subject,
        'message': message,
        'from_email': from_email,
        'recipient_list': recipient_list,
    })


@shared_task(name='backend.send_mass_mail', ignore_result=True)
def send_mass_mail_async(messages):
    from django.core.mail import send_mass_mail
    send_mass_mail(messages, fail_silently=True, )


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
