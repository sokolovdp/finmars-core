from __future__ import unicode_literals

from django.conf import settings
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.text import Truncator
from django.utils.translation import ugettext_lazy as _

from poms.users.models import MasterUser


@python_2_unicode_compatible
class Thread(models.Model):
    OPENED = 1
    CLOSED = 2
    STATUSES = [
        (OPENED, 'Opened'),
        (CLOSED, 'Closed'),
    ]

    master_user = models.ForeignKey(MasterUser, related_name='chat_threads', verbose_name=_('master user'))
    # users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='channels')
    create_date = models.DateTimeField(auto_now_add=True, db_index=True)
    subject = models.CharField(max_length=255)
    status = models.PositiveSmallIntegerField(choices=STATUSES, default=OPENED)
    status_date = models.DateTimeField()

    class Meta:
        ordering = ['-create_date']

    def __str__(self):
        return self.subject


@python_2_unicode_compatible
class Message(models.Model):
    thread = models.ForeignKey(Thread)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='chat_send_messages')
    text = models.TextField()
    create_date = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-create_date']

    def __str__(self):
        return self.short_text

    @property
    def short_text(self):
        return Truncator(self.text).chars(50)
        # return self.text[:50] if self.text else None


@python_2_unicode_compatible
class DirectMessage(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='chat_incoming_direct_messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='chat_outgoing_direct_messages')
    text = models.TextField()
    create_date = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-create_date']

    def __str__(self):
        return self.short_text

    @property
    def short_text(self):
        return Truncator(self.text).chars(50)
