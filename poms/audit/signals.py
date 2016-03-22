from __future__ import unicode_literals

from django.contrib.auth import user_logged_in, user_login_failed, get_user_model
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from poms.audit.models import AuthLog
from poms.middleware import get_request
from notifications.signals import notify


@receiver(user_logged_in, dispatch_uid='audit_user_logged_in')
def audit_user_logged_in(request=None, user=None, **kwargs):
    AuthLog.objects.create(user=user, is_success=True,
                           user_agent=getattr(request, 'user_agent', None),
                           user_ip=getattr(request, 'user_ip', None))

    notify.send(user, verb='logged in', recipient=user, public=False)
    # notify.send(user, verb='logged in', recipient=user, public=False, data={
    #     'user_agent': getattr(request, 'user_agent', None),
    #     'user_ip': getattr(request, 'user_ip', None),
    # })


@receiver(user_login_failed, dispatch_uid='audit_user_login_failed')
def audit_user_login_failed(credentials=None, **kwargs):
    if credentials is None:
        return
    username = credentials.get('username', None)
    if username is None:
        return
    user_model = get_user_model()
    try:
        user = user_model.objects.get(username=username)
    except user_model.DoesNotExist:
        return
    request = get_request()
    AuthLog.objects.create(user=user, is_success=False,
                           user_agent=getattr(request, 'user_agent', None),
                           user_ip=getattr(request, 'user_ip', None))

    notify.send(user, verb='login failed', level='warning', recipient=user, public=False)


def _get_actor():
    request = get_request()
    if request:
        user = request.user
        return user
    return None


def _get_recipients():
    # request = get_request()
    # if request:
    #     user = request.user
    #     # profile = getattr(user, 'profile', None)
    #     # master_user = getattr(profile, 'master_user', None)
    #     return [user]
    # return []
    from django.contrib.auth.models import User
    return User.objects.all()


@receiver(post_save, dispatch_uid='audit_post_save')
def audit_post_save(sender=None, instance=None, created=False, **kwargs):
    if instance._meta.app_label in ['currencies']:
        from notifications.signals import notify
        user = _get_actor()
        if user:
            verb = 'create' if created else 'update'
            for recipient in _get_recipients():
                notify.send(user, verb=verb, target=instance, recipient=recipient, public=False)


@receiver(post_delete, dispatch_uid='audit_post_delete')
def audit_post_delete(sender=None, instance=None, created=False, **kwargs):
    if instance._meta.app_label in ['currencies']:
        user = _get_actor()
        if user:
            verb = 'delete'
            for recipient in _get_recipients():
                notify.send(user, verb=verb, target=instance, recipient=recipient, public=False)
