from __future__ import unicode_literals

from django.conf import settings
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.text import Truncator
from django.utils.translation import ugettext_lazy as _

from poms.users.models import MasterUser


@python_2_unicode_compatible
class Channel(models.Model):
    master_user = models.ForeignKey(MasterUser, related_name='channels', verbose_name=_('master user'))
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='channels', through='Member')
    name = models.CharField(max_length=255)
    create_date = models.DateTimeField(auto_now_add=True, db_index=True)
    is_direct = models.BooleanField(default=False)

    class Meta:
        unique_together = [
            ['master_user', 'name', 'is_direct']
        ]
        ordering = ['name']

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Member(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.PROTECT, related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='channel_members')
    join_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [
            ['channel', 'user']
        ]

    def __str__(self):
        return '%s@%s' % (self.user, self.channel)


@python_2_unicode_compatible
class Message(models.Model):
    channel = models.ForeignKey(Channel)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='out_messages')
    text = models.TextField()
    create_date = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        unique_together = [
            ['channel', 'create_date']
        ]
        ordering = ['-create_date']

    def __str__(self):
        return self.short_text

    @property
    def short_text(self):
        return Truncator(self.text).chars(50)
        # return self.text[:50] if self.text else None

#
# @python_2_unicode_compatible
# class Status(models.Model):
#     message = models.ForeignKey(Message, related_name='statuses')
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='message_statuses')
#     read_date = models.DateTimeField(auto_now_add=True)
#
#     class Meta:
#         unique_together = [
#             ['message', 'user']
#         ]
#
#     def __str__(self):
#         return '%s read %s at %s' % (self.user, self.message, self.read_date)
