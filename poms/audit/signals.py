from __future__ import unicode_literals

from django.contrib.auth import user_logged_in, user_login_failed, get_user_model
from django.dispatch import receiver

from poms.audit.models import AuthLog
from poms.middleware import get_request


@receiver(user_logged_in, dispatch_uid='audit_user_logged_in')
def audit_user_logged_in(request=None, user=None, **kwargs):
    AuthLog.objects.create(user=user, is_success=True,
                           user_agent=getattr(request, 'user_agent', None),
                           user_ip=getattr(request, 'user_ip', None))


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
