from __future__ import unicode_literals
from __future__ import unicode_literals

import six
from django.contrib.auth import user_logged_in, user_login_failed, get_user_model
from django.core import serializers as django_serializers
from django.db.models.signals import post_init, post_save, post_delete
from django.dispatch import receiver
from django.utils.encoding import force_text
from django.utils.text import get_text_list
from django.utils.translation import ugettext as _
from reversion import revisions as reversion

from poms.audit.models import AuthLogEntry
from poms.audit.utils import set_comment_safe
from poms.middleware import get_request


@receiver(user_logged_in, dispatch_uid='audit_user_logged_in')
def audit_user_logged_in(request=None, user=None, **kwargs):
    AuthLogEntry.objects.create(user=user, is_success=True,
                                user_agent=getattr(request, 'user_agent', None),
                                user_ip=getattr(request, 'user_ip', None))

    # notify.send(user, verb='logged in', recipient=user, public=False,
    #             user_agent=getattr(request, 'user_agent', None),
    #             user_ip=getattr(request, 'user_ip', None))


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
    AuthLogEntry.objects.create(user=user, is_success=False,
                                user_agent=getattr(request, 'user_agent', None),
                                user_ip=getattr(request, 'user_ip', None))

    # notify.send(user, verb='login failed', level='warning', recipient=user, public=False,
    #             user_agent=getattr(request, 'user_agent', None),
    #             user_ip=getattr(request, 'user_ip', None))


# def _get_actor():
#     request = get_request()
#     if request:
#         user = request.user
#         return user
#     return None
#
#
# def _get_recipients():
#     # request = get_request()
#     # if request:
#     #     user = request.user
#     #     # profile = getattr(user, 'profile', None)
#     #     # master_user = getattr(profile, 'master_user', None)
#     #     return [user]
#     # return []
#     from django.contrib.auth.models import User
#     return User.objects.filter(id__gt=0)
#
#
# @receiver(post_save, dispatch_uid='audit_post_save')
# def audit_post_save(sender=None, instance=None, created=False, **kwargs):
#     if instance._meta.app_label in ['currencies']:
#         user = _get_actor()
#         if user:
#             verb = 'created' if created else 'updated'
#             for recipient in _get_recipients():
#                 notify.send(user, verb=verb, target=instance, recipient=recipient, public=False)
#
#
# @receiver(post_delete, dispatch_uid='audit_post_delete')
# def audit_post_delete(sender=None, instance=None, created=False, **kwargs):
#     if instance._meta.app_label in ['currencies']:
#         user = _get_actor()
#         if user:
#             verb = 'deleted'
#             for recipient in _get_recipients():
#                 notify.send(user, verb=verb, target=instance, recipient=recipient, public=False)


def _is_track(obj):
    # return obj._meta.label_lower in APP_LABELS
    return reversion.is_registered(obj)


def _to_set(fields):
    ret = set()
    for k, v in six.iteritems(fields):
        if isinstance(v, list):
            ret.add((k, tuple(v)))
        else:
            ret.add((k, v))
    return ret


def _tracker_init(sender, instance=None, **kwargs):
    if not _is_track(instance):
        return
    if instance.pk:
        instance._tracker_init_data = django_serializers.serialize('python', [instance])[0]
    else:
        instance._tracker_init_data = {'pk': None, 'fields': {}}


def _tracker_save(sender, instance=None, created=None, **kwargs):
    if not _is_track(instance):
        return

    # print('tracker_save: %s' % repr(instance))

    if created:
        # message = 'Added %(name)s "%(object)s". ' % {
        #     'name': force_text(instance._meta.verbose_name),
        #     'object': force_text(instance)
        # }
        message = _('Added %(name)s "%(object)s".') % {
            'name': force_text(instance._meta.verbose_name),
            'object': force_text(instance)
        }
        set_comment_safe(message)
    else:
        c = django_serializers.serialize('python', [instance])[0]
        i = instance._tracker_init_data

        if c['pk'] == i['pk']:
            cfields = _to_set(c['fields'])
            ifileds = _to_set(i['fields'])
            changed = ifileds - cfields
            if changed:
                attr_names = []
                for attr, v in changed:
                    f = instance._meta.get_field(attr)
                    attr_names.append(force_text(f.verbose_name))

                # message = 'Changed %(list)s for %(name)s "%(object)s". ' % {
                #     'list': ', '.join(attr_names),
                #     'name': force_text(instance._meta.verbose_name),
                #     'object': force_text(instance)
                # }
                message = _('Changed %(list)s for %(name)s "%(object)s".') % {
                    'list': get_text_list(attr_names, _('and')),
                    'name': force_text(instance._meta.verbose_name),
                    'object': force_text(instance)
                }
                set_comment_safe(message)


def _tracker_delete(sender, instance=None, **kwargs):
    if not _is_track(instance):
        return

    # message = 'Deleted %(name)s "%(object)s". ' % {
    #     'name': force_text(instance._meta.verbose_name),
    #     'object': force_text(instance)
    # }
    message = _('Deleted %(name)s "%(object)s".') % {
        'name': force_text(instance._meta.verbose_name),
        'object': force_text(instance)
    }
    set_comment_safe(message)


post_init.connect(_tracker_init, dispatch_uid='tracker_init')
post_save.connect(_tracker_save, dispatch_uid='tracker_save')
post_delete.connect(_tracker_delete, dispatch_uid='tracker_delete')
