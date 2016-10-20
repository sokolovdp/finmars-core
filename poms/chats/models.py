from __future__ import unicode_literals

from babel import Locale
from babel.dates import format_timedelta
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.text import Truncator
from django.utils.translation import get_language, ugettext_lazy

from poms.common.models import TimeStampedModel, NamedModel, FakeDeletableModel
from poms.obj_perms.models import GenericObjectPermission
from poms.tags.models import TagLink
from poms.users.models import MasterUser, Member


@python_2_unicode_compatible
class ThreadGroup(FakeDeletableModel, models.Model):
    master_user = models.ForeignKey(MasterUser, related_name='chat_thread_groups')
    name = models.CharField(max_length=255, verbose_name=ugettext_lazy('name'))

    object_permissions = GenericRelation(GenericObjectPermission)
    tags = GenericRelation(TagLink)

    class Meta(FakeDeletableModel.Meta):
        verbose_name = ugettext_lazy('thread group')
        verbose_name_plural = ugettext_lazy('thread groups')
        ordering = ['name', ]
        permissions = [
            ('view_threadgroup', 'Can view thread group'),
            ('manage_threadgroup', 'Can manage thread group'),
        ]

    def __str__(self):
        return self.name


# class ThreadGroupUserObjectPermission(AbstractUserObjectPermission):
#     content_object = models.ForeignKey(ThreadGroup, related_name='user_object_permissions',
#                                        verbose_name=ugettext_lazy('content object'))
#
#     class Meta(AbstractUserObjectPermission.Meta):
#         verbose_name = ugettext_lazy('thread groups - user permission')
#         verbose_name_plural = ugettext_lazy('thread groups - user permissions')
#
#
# class ThreadGroupGroupObjectPermission(AbstractGroupObjectPermission):
#     content_object = models.ForeignKey(ThreadGroup, related_name='group_object_permissions',
#                                        verbose_name=ugettext_lazy('content object'))
#
#     class Meta(AbstractGroupObjectPermission.Meta):
#         verbose_name = ugettext_lazy('thread groups - group permission')
#         verbose_name_plural = ugettext_lazy('thread groups - group permissions')


@python_2_unicode_compatible
class Thread(TimeStampedModel, FakeDeletableModel):
    master_user = models.ForeignKey(MasterUser, related_name='chat_threads')
    thread_group = models.ForeignKey(ThreadGroup, related_name='groups', null=True, blank=True)
    subject = models.CharField(max_length=255)
    is_closed = models.BooleanField(default=False, db_index=True)
    closed = models.DateTimeField(null=True, blank=True, db_index=True)

    object_permissions = GenericRelation(GenericObjectPermission)
    tags = GenericRelation(TagLink)

    class Meta(TimeStampedModel.Meta, FakeDeletableModel.Meta):
        verbose_name = ugettext_lazy('thread')
        verbose_name_plural = ugettext_lazy('threads')
        ordering = ['subject', ]
        permissions = [
            ('view_thread', 'Can view thread'),
            ('manage_thread', 'Can manage thread'),
        ]

    def __str__(self):
        return self.subject


# class ThreadUserObjectPermission(AbstractUserObjectPermission):
#     content_object = models.ForeignKey(Thread, related_name='user_object_permissions',
#                                        verbose_name=ugettext_lazy('content object'))
#
#     class Meta(AbstractUserObjectPermission.Meta):
#         verbose_name = ugettext_lazy('threads - user permission')
#         verbose_name_plural = ugettext_lazy('threads - user permissions')
#
#
# class ThreadGroupObjectPermission(AbstractGroupObjectPermission):
#     content_object = models.ForeignKey(Thread, related_name='group_object_permissions',
#                                        verbose_name=ugettext_lazy('content object'))
#
#     class Meta(AbstractGroupObjectPermission.Meta):
#         verbose_name = ugettext_lazy('threads - group permission')
#         verbose_name_plural = ugettext_lazy('threads - group permissions')


@python_2_unicode_compatible
class Message(TimeStampedModel):
    thread = models.ForeignKey(Thread, related_name='messages', verbose_name=ugettext_lazy('thread'))
    sender = models.ForeignKey(Member, related_name='chat_sent_messages', verbose_name=ugettext_lazy('sender'))
    text = models.TextField(verbose_name=ugettext_lazy('text'))

    class Meta(TimeStampedModel.Meta):
        verbose_name = ugettext_lazy('message')
        verbose_name_plural = ugettext_lazy('messages')
        index_together = [
            ['thread', 'created']
        ]
        ordering = ['created']

    def __str__(self):
        return self.short_text

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
    #     verbose_name=ugettext_lazy('recipient')
    # )
    # sender = models.ForeignKey(
    #     settings.AUTH_USER_MODEL,
    #     null=True,
    #     blank=True,
    #     related_name='chat_sent_direct_messages',
    #     verbose_name=ugettext_lazy('sender')
    # )
    recipient = models.ForeignKey(Member, on_delete=models.PROTECT, related_name='chat_received_direct_messages',
                                  verbose_name=ugettext_lazy('recipient'))
    sender = models.ForeignKey(Member, on_delete=models.PROTECT, related_name='chat_sent_direct_messages',
                               verbose_name=ugettext_lazy('sender'))
    text = models.TextField(verbose_name=ugettext_lazy('text'))

    class Meta(TimeStampedModel.Meta):
        verbose_name = ugettext_lazy('direct message')
        verbose_name_plural = ugettext_lazy('direct messages')
        ordering = ['created']

    def __str__(self):
        return self.short_text

    @property
    def short_text(self):
        return Truncator(self.text).chars(50)

    @property
    def timesince(self):
        locale = Locale.parse(get_language() or settings.LANGUAGE_CODE, sep='-')
        return format_timedelta(self.created - timezone.now(), add_direction=True, locale=locale)
