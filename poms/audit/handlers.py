from __future__ import unicode_literals

import six
from django.contrib.auth import user_logged_in, user_login_failed, get_user_model
from django.core import serializers as django_serializers
from django.db.models.signals import post_init, post_save, post_delete
from django.dispatch import receiver
from django.utils.encoding import force_text
from reversion import revisions as reversion

from poms import notifications
from poms.audit import history
from poms.audit.models import AuthLogEntry
from poms.common.middleware import get_request


@receiver(user_logged_in, dispatch_uid='audit_user_logged_in')
def audit_user_logged_in(request=None, user=None, **kwargs):
    AuthLogEntry.objects.create(user=user, is_success=True,
                                user_agent=getattr(request, 'user_agent', None),
                                user_ip=getattr(request, 'user_ip', None))
    notifications.info([user], actor=user, verb='logged in')


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
    AuthLogEntry.objects.create(user=user,
                                is_success=False,
                                user_agent=getattr(request, 'user_agent', None),
                                user_ip=getattr(request, 'user_ip', None))
    notifications.warning([user], actor=user, verb='login failed')


def is_track_enabled(obj):
    return history.is_active() and reversion.is_registered(obj)


def fields_to_set(fields):
    ret = set()
    for k, v in six.iteritems(fields):
        if isinstance(v, list):
            ret.add((k, tuple(v)))
        else:
            ret.add((k, v))
    return ret


@receiver(post_init, dispatch_uid='tracker_on_init')
def tracker_on_init(sender, instance=None, **kwargs):
    if not is_track_enabled(instance):
        return
    if instance.pk:
        instance._tracker_data = django_serializers.serialize('python', [instance])[0]
    else:
        instance._tracker_data = {'pk': None, 'fields': {}}


@receiver(post_save, dispatch_uid='tracker_on_save')
def tracker_on_save(sender, instance=None, created=None, **kwargs):
    if not is_track_enabled(instance):
        return

    if created:
        history.object_added(instance)
    else:
        c = django_serializers.serialize('python', [instance])[0]
        i = instance._tracker_data

        if c['pk'] == i['pk']:
            cfields = fields_to_set(c['fields'])
            ifileds = fields_to_set(i['fields'])
            changed = ifileds - cfields
            if changed:
                fields = []
                for attr, v in changed:
                    f = instance._meta.get_field(attr)
                    fields.append(force_text(f.verbose_name))
                fields.sort()
                history.object_changed(instance, fields)


@receiver(post_delete, dispatch_uid='tracker_on_delete')
def tracker_on_delete(sender, instance=None, **kwargs):
    if not is_track_enabled(instance):
        return
    history.object_deleted(instance)

# post_init.connect(_tracker_init, dispatch_uid='tracker_init')
# post_save.connect(_tracker_save, dispatch_uid='tracker_save')
# post_delete.connect(_tracker_delete, dispatch_uid='tracker_delete')
