from __future__ import unicode_literals

import json

from babel import Locale
from babel.dates import format_timedelta
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible, force_text
from django.utils.translation import ugettext_lazy as _, get_language


# Create your models here.


@python_2_unicode_compatible
class Notification(models.Model):
    SUCCESS = 1
    INFO = 2
    WARNING = 3
    ERROR = 4
    LEVELS = (
        (SUCCESS, _('success')),
        (INFO, _('info')),
        (WARNING, _('warning')),
        (ERROR, _('error'))
    )
    level = models.PositiveSmallIntegerField(choices=LEVELS, default=INFO)

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, blank=False, related_name='notifications')
    create_date = models.DateTimeField(default=timezone.now, db_index=True)
    read_date = models.DateTimeField(null=True, blank=True, db_index=True)

    actor_content_type = models.ForeignKey(ContentType, related_name='notify_actor')
    actor_object_id = models.CharField(max_length=255)
    actor = GenericForeignKey('actor_content_type', 'actor_object_id')

    verb = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    target_content_type = models.ForeignKey(ContentType, related_name='notify_target', blank=True, null=True)
    target_object_id = models.CharField(max_length=255, blank=True, null=True)
    target = GenericForeignKey('target_content_type', 'target_object_id')

    action_object_content_type = models.ForeignKey(ContentType, blank=True, null=True,
                                                   related_name='notify_action_object')
    action_object_object_id = models.CharField(max_length=255, blank=True, null=True)
    action_object = GenericForeignKey('action_object_content_type', 'action_object_object_id')

    public = models.BooleanField(default=True)
    deleted = models.BooleanField(default=False)
    emailed = models.BooleanField(default=False)

    data = models.TextField(blank=True, null=True)

    # objects = NotificationQuerySet.as_manager()

    class Meta:
        ordering = ['-create_date']

    def __str__(self):  # Adds support for Python 3
        ctx = {
            'actor': self.actor,
            'verb': self.verb,
            'action_object': self.action_object,
            'target': self.target,
            'timesince': self.timesince()
        }
        if self.target:
            if self.action_object:
                return '%(actor)s %(verb)s %(action_object)s on %(target)s %(timesince)s ago' % ctx
            return '%(actor)s %(verb)s %(target)s %(timesince)s ago' % ctx
        if self.action_object:
            return '%(actor)s %(verb)s %(action_object)s %(timesince)s ago' % ctx
        return '%(actor)s %(verb)s %(timesince)s ago' % ctx

    def timesince(self, now=None):
        # from django.utils.timesince import timesince as timesince_
        # return timesince_(self.create_date, now)
        locale = Locale.parse(get_language(), sep='-')
        return format_timedelta(self.create_date - timezone.now(), add_direction=True, locale=locale)

    def mark_as_read(self):
        if self.read_date is None:
            self.read_date = timezone.now()
            self.save(update_fields=['read_date'])

    def mark_as_unread(self):
        if self.read_date is not None:
            self.read_date = None
            self.save(update_fields=['read_date'])


def notify_handler(verb, **kwargs):
    kwargs.pop('signal', None)
    recipient = kwargs.pop('recipient')
    actor = kwargs.pop('sender')
    optional_objs = [(kwargs.pop(opt, None), opt) for opt in ('target', 'action_object')]
    public = bool(kwargs.pop('public', True))
    description = kwargs.pop('description', None)
    create_date = kwargs.pop('create_date', timezone.now())
    level = kwargs.pop('level', Notification.INFO)

    # Check if User or Group
    if isinstance(recipient, Group):
        recipients = recipient.user_set.all()
    else:
        recipients = [recipient]

    for recipient in recipients:
        n = Notification(
            recipient=recipient,
            actor_content_type=ContentType.objects.get_for_model(actor),
            actor_object_id=actor.pk,
            verb=force_text(verb),
            public=public,
            description=description,
            create_date=create_date,
            level=level,
        )

        # Set optional objects
        for obj, opt in optional_objs:
            if obj is not None:
                setattr(n, '%s_object_id' % opt, obj.pk)
                setattr(n, '%s_content_type' % opt,
                        ContentType.objects.get_for_model(obj))

        n.data = json.dumps(kwargs, sort_keys=True, indent=2)

        n.save()

# connect the signal
