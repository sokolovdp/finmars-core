from __future__ import unicode_literals

from babel import Locale
from babel.dates import format_timedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import Group
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _, get_language

from poms.notifications import LEVELS


@python_2_unicode_compatible
class NotificationConfig(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)

    # TODO: !!!
    content_type = models.ForeignKey(ContentType, related_name='notificatins_config', null=True, blank=True)
    type = models.CharField(max_length=30, null=True, blank=True)

    level = models.PositiveSmallIntegerField(choices=LEVELS, default=messages.INFO)
    is_enabled = models.BooleanField(default=True)
    is_email_enabled = models.BooleanField(default=True)
    is_web_enabled = models.BooleanField(default=True)

    class Meta:
        abstract = True

    def __str__(self):
        return '%s - %s: %s' % (self.user, self.level, self.is_send_email)


@python_2_unicode_compatible
class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='notifications', blank=False)

    # TODO: !!!

    level = models.PositiveSmallIntegerField(choices=LEVELS, default=messages.INFO)
    type = models.CharField(max_length=30, null=True, blank=True)
    message = models.TextField(blank=True, null=True)

    actor_content_type = models.ForeignKey(ContentType, related_name='notify_actor', null=True, blank=True)
    actor_object_id = models.CharField(max_length=255, null=True, blank=True)
    actor = GenericForeignKey('actor_content_type', 'actor_object_id')

    verb = models.CharField(max_length=255, null=True, blank=True)

    target_content_type = models.ForeignKey(ContentType, related_name='notify_target', blank=True, null=True)
    target_object_id = models.CharField(max_length=255, blank=True, null=True)
    target = GenericForeignKey('target_content_type', 'target_object_id')

    action_object_content_type = models.ForeignKey(ContentType, blank=True, null=True,
                                                   related_name='notify_action_object')
    action_object_object_id = models.CharField(max_length=255, blank=True, null=True)
    action_object = GenericForeignKey('action_object_content_type', 'action_object_object_id')

    create_date = models.DateTimeField(default=timezone.now, db_index=True)
    read_date = models.DateTimeField(null=True, blank=True, db_index=True)

    data = models.TextField(blank=True, null=True)

    # objects = NotificationQuerySet.as_manager()

    class Meta:
        ordering = ['-create_date']

    def __str__(self):
        if self.verb and self.actor_object_id:
            ctx = {
                'actor': self.actor,
                'verb': self.verb,
                'action_object': self.action_object,
                'target': self.target,
                'timesince': self.timesince()
            }
            if self.target:
                if self.action_object:
                    return _('%(actor)s %(verb)s %(action_object)s on %(target)s %(timesince)s') % ctx
                return _('%(actor)s %(verb)s %(target)s %(timesince)s') % ctx
            if self.action_object:
                return _('%(actor)s %(verb)s %(action_object)s %(timesince)s') % ctx
            return _('%(actor)s %(verb)s %(timesince)s') % ctx
        else:
            return self.message

    def timesince(self, now=None):
        locale = Locale.parse(get_language(), sep='-')
        return format_timedelta(self.create_date - timezone.now(), add_direction=True, locale=locale)
        # return timesince(self.create_date, now)

    def mark_as_read(self):
        if self.read_date is None:
            self.read_date = timezone.now()
            self.save(update_fields=['read_date'])

    def mark_as_unread(self):
        if self.read_date is not None:
            self.read_date = None
            self.save(update_fields=['read_date'])

#
# def notify_handler(sender=None, recipient=None, nf_type=None, message=None, verb=None, action_object=None, target=None,
#                    create_date=None, level=None, data=None, **kwargs):
#     # Check if User or Group
#     if isinstance(recipient, Group):
#         recipients = recipient.user_set.all()
#     elif isinstance(recipient, (list, tuple, models.QuerySet, models.Manager)):
#         recipients = recipient
#     else:
#         recipients = [recipient]
#
#     ret = []
#     for recipient in recipients:
#         # profile = getattr(recipient, 'profile', None)
#         # language = getattr(profile, 'language', settings.LANGUAGE_CODE)
#         # with override(language):
#         n = Notification.objects.create(
#             recipient=recipient,
#             level=level or LEVEL_INFO,
#             type=nf_type,
#             message=message,
#             actor=sender,
#             verb=force_text(verb),
#             target=target,
#             action_object=action_object,
#             data=json.dumps(data, sort_keys=True) if data else None,
#             create_date=create_date or timezone.now()
#         )
#         ret.append(n)
#     return ret


# connect the signal
