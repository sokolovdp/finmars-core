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
from django.utils.text import Truncator
from django.utils.translation import get_language, ugettext_lazy

from poms.notifications import LEVELS


@python_2_unicode_compatible
class NotificationSetting(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='notification_settings')
    member = models.ForeignKey('users.Member', related_name='notification_settings', null=True)

    actor_content_type = models.ForeignKey(ContentType, related_name='notify_actor', null=True, blank=True)
    target_content_type = models.ForeignKey(ContentType, related_name='notify_actor', null=True, blank=True)
    action_object_content_type = models.ForeignKey(ContentType, related_name='notify_actor', null=True, blank=True)

    level = models.PositiveSmallIntegerField(choices=LEVELS, default=messages.INFO)
    is_email_enabled = models.BooleanField(default=True)

    class Meta:
        abstract = True

    def __str__(self):
        return '%s - %s: %s' % (self.member, self.level, self.is_send_email)


# Actor         :  The object that performed the activity.
# Verb          :  The verb phrase that identifies the action of the activity.
# Action Object :  The object linked to the action itself.
# Target        :  The object to which the activity was performed.
@python_2_unicode_compatible
class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='notifications', blank=False,
                                  verbose_name=ugettext_lazy('recipient'))
    recipient_member = models.ForeignKey('users.Member', related_name='notifications', null=True,
                                         verbose_name=ugettext_lazy('recipient member'))

    # level = models.PositiveSmallIntegerField(choices=LEVELS, default=messages.INFO)
    # type = models.CharField(max_length=30, null=True, blank=True)

    message = models.TextField(blank=True, null=True, verbose_name=ugettext_lazy('message'))

    actor_content_type = models.ForeignKey(ContentType, related_name='+', null=True, blank=True,
                                           verbose_name=ugettext_lazy('actor content type'))
    actor_object_id = models.CharField(max_length=255, null=True, blank=True,
                                       verbose_name=ugettext_lazy('actor object id'))
    actor = GenericForeignKey('actor_content_type', 'actor_object_id')

    verb = models.CharField(max_length=255, null=True, blank=True, verbose_name=ugettext_lazy('verb'))

    action_object_content_type = models.ForeignKey(ContentType, blank=True, null=True, related_name='+',
                                                   verbose_name=ugettext_lazy('action object content type'))
    action_object_object_id = models.CharField(max_length=255, blank=True, null=True,
                                               verbose_name=ugettext_lazy('action object object id'))
    action_object = GenericForeignKey('action_object_content_type', 'action_object_object_id')

    target_content_type = models.ForeignKey(ContentType, blank=True, null=True, related_name='+',
                                            verbose_name=ugettext_lazy('target content type'))
    target_object_id = models.CharField(max_length=255, blank=True, null=True,
                                        verbose_name=ugettext_lazy('target object id'))
    target = GenericForeignKey('target_content_type', 'target_object_id')

    create_date = models.DateTimeField(default=timezone.now, db_index=True, verbose_name=ugettext_lazy('create date'))
    read_date = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name=ugettext_lazy('read date'))

    data = models.TextField(blank=True, null=True, verbose_name=ugettext_lazy('data'))

    # objects = NotificationQuerySet.as_manager()

    class Meta:
        ordering = ['create_date']

    def __str__(self):
        if self.message:
            return self.message
        elif self.verb and self.actor_object_id:
            ctx = {
                'actor': self.actor,
                'verb': self.verb,
                'action_object': self.action_object,
                'target': self.target,
                'timesince': self.timesince()
            }
            if self.target:
                if self.action_object:
                    return ugettext_lazy('%(actor)s %(verb)s %(action_object)s on %(target)s %(timesince)s') % ctx
                return ugettext_lazy('%(actor)s %(verb)s %(target)s %(timesince)s') % ctx
            if self.action_object:
                return ugettext_lazy('%(actor)s %(verb)s %(action_object)s %(timesince)s') % ctx
            return ugettext_lazy('%(actor)s %(verb)s %(timesince)s') % ctx
        else:
            return ugettext_lazy("Invalid notification message")

    @property
    def subject(self):
        message = str(self)
        if message:
            return Truncator(self.name).chars(25)
        return ''

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


# v4 ---

@python_2_unicode_compatible
class Notification4Class(models.Model):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=255)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Notification4Setting(models.Model):
    member = models.ForeignKey('users.Member', related_name='notification4_settings')
    notification_class = models.ForeignKey(Notification4Class)

    is_email_enabled = models.BooleanField(default=True)

    class Meta:
        abstract = True
        unique_together = (
            ('member', 'notification_class')
        )

    def __str__(self):
        return '%s[%s]->%s' % (self.notification_type, self.member, self.is_email_enabled)

    @classmethod
    def can_send_email(cls, member, notification_class):
        try:
            obj = cls.objects.get(member=member, notification_class__code=notification_class)
        except models.ObjectDoesNotExist:
            return False
        else:
            return obj.is_email_enabled


@python_2_unicode_compatible
class Notification4(models.Model):
    recipient = models.ForeignKey('users.Member', related_name='notifications4')
    notification_class = models.ForeignKey(Notification4Class, related_name='notifications4', on_delete=models.PROTECT)
    message = models.TextField(blank=True, null=True)
    create_date = models.DateTimeField(default=timezone.now, db_index=True)
    read_date = models.DateTimeField(null=True, blank=True, db_index=True)
    email_sent = models.DateTimeField(null=True, blank=True, db_index=True)
    data = models.TextField(blank=True, null=True)

    # linked object
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.IntegerField(max_length=255, null=True, blank=True)
    content_object = GenericForeignKey()

    class Meta:
        abstract = True
        ordering = ['-create_date']

    def __str__(self):
        return self.message

    def mark_as_read(self):
        if self.read_date is None:
            self.read_date = timezone.now()
            self.save(update_fields=['read_at'])

    def mark_as_unread(self):
        if self.read_date is not None:
            self.read_date = None
            self.save(update_fields=['read_at'])
