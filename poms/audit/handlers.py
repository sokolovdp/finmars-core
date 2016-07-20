from __future__ import unicode_literals

import logging

import six
from django.contrib.auth import user_logged_in, user_login_failed, get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core import serializers as django_serializers
from django.db.models.signals import post_init, post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.utils.encoding import force_text
from reversion import revisions as reversion

from poms import notifications
from poms.audit import history
from poms.audit.models import AuthLogEntry
from poms.common.middleware import get_request

_l = logging.getLogger('poms.audit')


@receiver(user_logged_in, dispatch_uid='audit_user_logged_in')
def audit_user_logged_in(request=None, user=None, **kwargs):
    AuthLogEntry.objects.create(user=user, is_success=True,
                                user_agent=getattr(request, 'user_agent', None),
                                user_ip=getattr(request, 'user_ip', None))
    notifications.send([user], actor=user, verb='logged in')


@receiver(user_login_failed, dispatch_uid='audit_user_login_failed')
def audit_user_login_failed(credentials=None, **kwargs):
    if credentials is None:
        return
    request = get_request()
    username = credentials.get('username', None)
    if username is None:
        return
    user_model = get_user_model()
    try:
        user = user_model.objects.get(username=username)
    except user_model.DoesNotExist:
        return
    AuthLogEntry.objects.create(user=user,
                                is_success=False,
                                user_agent=getattr(request, 'user_agent', None),
                                user_ip=getattr(request, 'user_ip', None))
    # notifications.send([user], actor=user, verb='login failed')


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


def _to_json_value(value):
    if type(value) in six.string_types:
        return value
    elif type(value) in six.integer_types:
        return value
    elif type(value) in [list, tuple, dict]:
        return value
    return force_text(value)


@receiver(post_init, dispatch_uid='tracker_on_init')
def tracker_post_init(sender, instance=None, **kwargs):
    if not is_track_enabled(instance):
        return
    if instance.pk:
        instance._tracker_data = django_serializers.serialize('python', [instance])[0]
    else:
        instance._tracker_data = {'pk': None, 'fields': {}}


@receiver(post_save, dispatch_uid='tracker_on_save')
def tracker_post_save(sender, instance=None, created=None, **kwargs):
    if not is_track_enabled(instance):
        return
    _l.debug('post_save: sender=%s, instance=%s, created=%s, kwargs=%s',
             sender, instance, created, kwargs)

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
                    old_value = i['fields'].get(attr, None)
                    new_value = c['fields'].get(attr, None)

                    if f.one_to_one or f.one_to_many:
                        ct = ContentType.objects.get_for_model(f.related_model)
                        if old_value:
                            old_value = ct.get_object_for_this_type(pk=old_value)
                            old_value = force_text(old_value)
                        if new_value:
                            new_value = ct.get_object_for_this_type(pk=new_value)
                            new_value = force_text(new_value)
                    elif f.many_to_many:
                        pass
                    old_value = _to_json_value(old_value)
                    new_value = _to_json_value(new_value)
                    fields.append({
                        'name': six.text_type(f.name),
                        'verbose_name': six.text_type(f.verbose_name),
                        'old_value': old_value,
                        'new_value': new_value,
                    })
                # fields.sort()
                history.object_changed(instance, fields)


@receiver(m2m_changed, dispatch_uid='tracker_on_m2m_changed')
def tracker_on_m2m_changed(sender, instance=None, action=None, reverse=None, model=None, pk_set=None, **kwargs):
    if not is_track_enabled(instance):
        return

    if not hasattr(instance, '_tracker_data'):
        return

    _l.debug('m2m_changed: sender=%s, instance=%s, action=%s, reverse=%s, model=%s, pk_set=%s, kwargs=%s',
             sender, instance, action, reverse, model, pk_set, kwargs)

    if action == 'pre_remove':
        pass
    if action == 'post_add':
        pass

    # m2m_changed: sender=<class 'poms.tags.models.Tag_thread_groups'>, instance=G2, action=pre_remove, reverse=True, model=<class 'poms.tags.models.Tag'>, pk_set={4}, kwargs={'signal': <django.db.models.signals.ModelSignal object at 0x101fe5438>, 'using': 'default'}
    # m2m_changed: sender=<class 'poms.tags.models.Tag_thread_groups'>, instance=G2, action=post_remove, reverse=True, model=<class 'poms.tags.models.Tag'>, pk_set={4}, kwargs={'signal': <django.db.models.signals.ModelSignal object at 0x101fe5438>, 'using': 'default'}
    # m2m_changed: sender=<class 'poms.tags.models.Tag_thread_groups'>, instance=G2, action=pre_add, reverse=True, model=<class 'poms.tags.models.Tag'>, pk_set={1, 5, 6}, kwargs={'signal': <django.db.models.signals.ModelSignal object at 0x101fe5438>, 'using': 'default'}
    # m2m_changed: sender=<class 'poms.tags.models.Tag_thread_groups'>, instance=G2, action=post_add, reverse=True, model=<class 'poms.tags.models.Tag'>, pk_set={1, 5, 6}, kwargs={'signal': <django.db.models.signals.ModelSignal object at 0x101fe5438>, 'using': 'default'}
    # post_save: sender=<class 'poms.chats.models.ThreadGroup'>, instance=G2, created=False, kwargs={'signal': <django.db.models.signals.ModelSignal object at 0x101fe5240>, 'raw': False, 'update_fields': None, 'using': 'default'}

    # m2m_changed: sender=<class 'poms.tags.models.Tag_thread_groups'>, instance=G2, action=pre_remove, reverse=True, model=<class 'poms.tags.models.Tag'>, pk_set={6}, kwargs={'signal': <django.db.models.signals.ModelSignal object at 0x101fe5438>, 'using': 'default'}
    # m2m_changed: sender=<class 'poms.tags.models.Tag_thread_groups'>, instance=G2, action=post_remove, reverse=True, model=<class 'poms.tags.models.Tag'>, pk_set={6}, kwargs={'signal': <django.db.models.signals.ModelSignal object at 0x101fe5438>, 'using': 'default'}
    # m2m_changed: sender=<class 'poms.tags.models.Tag_thread_groups'>, instance=G2, action=pre_add, reverse=True, model=<class 'poms.tags.models.Tag'>, pk_set={4}, kwargs={'signal': <django.db.models.signals.ModelSignal object at 0x101fe5438>, 'using': 'default'}
    # m2m_changed: sender=<class 'poms.tags.models.Tag_thread_groups'>, instance=G2, action=post_add, reverse=True, model=<class 'poms.tags.models.Tag'>, pk_set={4}, kwargs={'signal': <django.db.models.signals.ModelSignal object at 0x101fe5438>, 'using': 'default'}
    # post_save: sender=<class 'poms.chats.models.ThreadGroup'>, instance=G2, created=False, kwargs={'signal': <django.db.models.signals.ModelSignal object at 0x101fe5240>, 'raw': False, 'update_fields': None, 'using': 'default'}
    pass


@receiver(post_delete, dispatch_uid='tracker_on_delete')
def tracker_post_delete(sender, instance=None, **kwargs):
    if not is_track_enabled(instance):
        return
    _l.debug('post_delete: sender=%s, instance=%s, kwargs=%s',
             sender, instance, kwargs)
    history.object_deleted(instance)
