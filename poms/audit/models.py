from __future__ import unicode_literals

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _


@python_2_unicode_compatible
class AuthLogEntry(models.Model):
    date = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('user'))
    user_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)
    is_success = models.BooleanField(default=False, db_index=True)

    class Meta:
        verbose_name = _('authenticate log')
        verbose_name_plural = _('authenticate logs')

    def __str__(self):
        if self.is_success:
            msg = 'User %s logged in from %s at %s using "%s"'
        else:
            msg = 'User %s login failed from %s at %s using "%s"'
        return msg % (self.user, self.user_ip, self.date, self.user_agent)


# class VersionInfo(models.Model):
#     revision = models.ForeignKey(Revision, related_name='info')
#     master_user = models.ForeignKey('users.MasterUser')
#     member = models.ForeignKey('users.Member', null=True, blank=True)
#     username = models.CharField(max_length=255, null=True, blank=True)


@python_2_unicode_compatible
class ObjectHistoryEntry(models.Model):
    ADDITION = 1
    CHANGE = 2
    DELETION = 3
    FLAG_CHOICES = (
        (ADDITION, 'Added'),
        (CHANGE, 'Changed'),
        (DELETION, 'Deleted'),
    )

    master_user = models.ForeignKey('users.MasterUser', related_name='histories')
    member = models.ForeignKey('users.Member', related_name='histories', null=True, blank=None,
                               on_delete=models.SET_NULL)

    created = models.DateTimeField(auto_now_add=True, db_index=True)
    version = models.IntegerField(default=0)
    action_flag = models.PositiveSmallIntegerField(choices=FLAG_CHOICES)
    message = models.TextField(null=True, blank=True)

    content_type = models.ForeignKey(ContentType, related_name='histories', blank=True, null=True)
    object_id = models.BigIntegerField(blank=True, null=True)
    content_object = GenericForeignKey()

    class Meta:
        verbose_name = _('object history')
        verbose_name_plural = _('object histories')
        index_together = (
            ('master_user', 'created')
        )
        ordering = [
            '-created'
        ]

    def __str__(self):
        return self.message

    @property
    def comment(self):
        from poms.audit.history import make_comment
        return make_comment(self.message)
