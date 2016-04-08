from __future__ import unicode_literals

from babel import Locale
from babel.dates import format_timedelta
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.text import Truncator
from django.utils.translation import ugettext_lazy as _, get_language

from poms.audit import history
from poms.common.models import TimeStampedModel
from poms.obj_perms.utils import register_model
from poms.users.models import MasterUser, Member


class ThreadStatus(models.Model):
    master_user = models.ForeignKey(MasterUser, related_name='chat_thread_statuses', verbose_name=_('master user'))
    name = models.CharField(max_length=255)
    is_closed = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('thread status')
        verbose_name_plural = _('thread statuses')
        unique_together = [
            ['master_user', 'name']
        ]

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Thread(TimeStampedModel):
    master_user = models.ForeignKey(MasterUser, related_name='chat_threads', verbose_name=_('master user'))
    subject = models.CharField(max_length=255)
    status = models.ForeignKey(ThreadStatus)

    class Meta(TimeStampedModel.Meta):
        verbose_name = _('thread')
        verbose_name_plural = _('threads')
        permissions = [
            ('view_thread', 'Can view thread'),
            ('manage_thread', 'Can manage thread'),
        ]

    def __str__(self):
        return self.subject

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super(Thread, self).save(force_insert=force_insert, force_update=force_update, using=using,
                                 update_fields=update_fields)


@python_2_unicode_compatible
class Message(TimeStampedModel):
    thread = models.ForeignKey(Thread)
    sender = models.ForeignKey(Member, related_name='chat_sent_messages')
    text = models.TextField()

    class Meta(TimeStampedModel.Meta):
        verbose_name = _('message')
        verbose_name_plural = _('messages')

    def __str__(self):
        return '%s sent %s - %s' % (self.sender, self.timesince, self.short_text)

    @property
    def short_text(self):
        return Truncator(self.text).chars(50)
        # return self.text[:50] if self.text else None

    @property
    def timesince(self):
        locale = Locale.parse(get_language(), sep='-')
        return format_timedelta(self.created - timezone.now(), add_direction=True, locale=locale)


@python_2_unicode_compatible
class DirectMessage(TimeStampedModel):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='chat_received_direct_messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='chat_sent_direct_messages')
    text = models.TextField()

    class Meta(TimeStampedModel.Meta):
        verbose_name = _('direct message')
        verbose_name_plural = _('direct messages')

    def __str__(self):
        return '%s sent to %s %s - %s' % (self.sender, self.recipient, self.timesince, self.short_text)

    @property
    def short_text(self):
        return Truncator(self.text).chars(50)

    @property
    def timesince(self):
        locale = Locale.parse(get_language(), sep='-')
        return format_timedelta(self.created - timezone.now(), add_direction=True, locale=locale)


register_model(Thread)

history.register(ThreadStatus)
history.register(Thread)
history.register(Message)
history.register(DirectMessage)
