from __future__ import unicode_literals

import json

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from reversion.models import Revision


@python_2_unicode_compatible
class AuthLogEntry(models.Model):
    date = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name=_('create date')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('user')
    )
    user_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_('user ip')
    )
    user_agent = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_('user agent')
    )
    is_success = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name=_('is_success')
    )

    class Meta:
        verbose_name = _('authenticate log')
        verbose_name_plural = _('authenticate logs')

    def __str__(self):
        if self.is_success:
            msg = 'User %s logged in from %s at %s using "%s"'
        else:
            msg = 'User %s login failed from %s at %s using "%s"'
        return msg % (self.user, self.user_ip, self.date, self.user_agent)


class VersionInfo(models.Model):
    # There must be a relationship with Revision called `revision`.
    revision = models.ForeignKey(Revision, related_name='info')
    master_user = models.ForeignKey('users.MasterUser')
    username = models.CharField(max_length=255, null=True, blank=True)


@python_2_unicode_compatible
class HistoryEntry(models.Model):
    ADDITION = 1
    CHANGE = 2
    DELETION = 3
    FLAG_CHOICES = (
        (ADDITION, 'Added'),
        (CHANGE, 'Changed'),
        (DELETION, 'Deleted'),
    )

    master_user = models.ForeignKey(
        'users.MasterUser'
    )
    member = models.ForeignKey(
        'users.Member',
    )
    created = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )
    content_type = models.ForeignKey(
        ContentType,
        related_name='histories',
    )
    object_id = models.BigIntegerField()
    content_object = GenericForeignKey()
    action_flag = models.PositiveSmallIntegerField(
        choices=FLAG_CHOICES
    )
    message = models.TextField(
        null=True,
        blank=True
    )
    json_version = models.IntegerField(default=0)
    json = models.TextField(
        null=True,
        blank=True
    )

    class Meta:
        # abstract = True
        verbose_name = _('history')
        verbose_name_plural = _('histories')
        index_together = (
            ('master_user', 'created')
        )
        ordering = [
            '-created'
        ]

    def __str__(self):
        return self.message

    def get_data(self):
        return json.loads(self.json) if self.json else None

    def set_data(self, data):
        self.json = json.dumps(data, sort_keys=True) if data else None

    data = property(get_data, set_data)
