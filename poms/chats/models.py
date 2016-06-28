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
from poms.obj_perms.models import GroupObjectPermissionBase, UserObjectPermissionBase
from poms.users.models import MasterUser, Member


class ThreadStatus(models.Model):
    master_user = models.ForeignKey(
        MasterUser,
        related_name='chat_thread_statuses',
        verbose_name=_('master user')
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_('name')
    )
    is_closed = models.BooleanField(
        default=False,
        verbose_name=_('is closed')
    )

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
    master_user = models.ForeignKey(
        MasterUser,
        related_name='chat_threads',
        verbose_name=_('master user')
    )
    subject = models.CharField(
        max_length=255,
        verbose_name=_('subject')
    )
    status = models.ForeignKey(
        ThreadStatus,
        on_delete=models.PROTECT,
        verbose_name=_('status')
    )

    class Meta(TimeStampedModel.Meta):
        verbose_name = _('thread')
        verbose_name_plural = _('threads')
        permissions = [
            ('view_thread', 'Can view thread'),
            # ('manage_thread', 'Can manage thread'),
        ]

    def __str__(self):
        return self.subject


class ThreadUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(
        Thread,
        related_name='user_object_permissions',
        verbose_name=_('content object')
    )

    class Meta(UserObjectPermissionBase.Meta):
        verbose_name = _('threads - user permission')
        verbose_name_plural = _('threads - user permissions')


class ThreadGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(
        Thread,
        related_name='group_object_permissions',
        verbose_name=_('content object')
    )

    class Meta(GroupObjectPermissionBase.Meta):
        verbose_name = _('threads - group permission')
        verbose_name_plural = _('threads - group permissions')


@python_2_unicode_compatible
class Message(TimeStampedModel):
    thread = models.ForeignKey(
        Thread,
        verbose_name=_('thread')
    )
    sender = models.ForeignKey(
        Member,
        related_name='chat_sent_messages',
        verbose_name=_('sender')
    )
    text = models.TextField(
        verbose_name=_('text')
    )

    class Meta(TimeStampedModel.Meta):
        verbose_name = _('message')
        verbose_name_plural = _('messages')

    def __str__(self):
        return '%s sent %s - %s' % (self.sender, self.timesince, self.short_text)

    @property
    def short_text(self):
        return Truncator(self.text).chars(50)

    @property
    def timesince(self):
        locale = Locale.parse(get_language() or settings.LANGUAGE_CODE, sep='-')
        return format_timedelta(self.created - timezone.now(), add_direction=True, locale=locale)


@python_2_unicode_compatible
class DirectMessage(TimeStampedModel):
    # recipient = models.ForeignKey(
    #     settings.AUTH_USER_MODEL,
    #     null=True,
    #     blank=True,
    #     related_name='chat_received_direct_messages',
    #     verbose_name=_('recipient')
    # )
    # sender = models.ForeignKey(
    #     settings.AUTH_USER_MODEL,
    #     null=True,
    #     blank=True,
    #     related_name='chat_sent_direct_messages',
    #     verbose_name=_('sender')
    # )
    recipient = models.ForeignKey(
        Member,
        # null=True,
        # blank=True,
        related_name='chat_received_direct_messages',
        verbose_name=_('recipient')
    )
    sender = models.ForeignKey(
        Member,
        # null=True,
        # blank=True,
        related_name='chat_sent_direct_messages',
        verbose_name=_('sender')
    )
    text = models.TextField(
        verbose_name=_('text')
    )

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
        locale = Locale.parse(get_language() or settings.LANGUAGE_CODE, sep='-')
        return format_timedelta(self.created - timezone.now(), add_direction=True, locale=locale)


# register_model(Thread)

history.register(ThreadStatus)
history.register(Thread)
history.register(ThreadUserObjectPermission)
history.register(ThreadGroupObjectPermission)
history.register(Message)
history.register(DirectMessage)
