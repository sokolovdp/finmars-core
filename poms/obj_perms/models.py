from __future__ import unicode_literals

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from poms.chats.models import Thread


class ObjectPermissionBase(models.Model):
    permission = models.ForeignKey('auth.Permission')

    class Meta:
        abstract = True


@python_2_unicode_compatible
class UserObjectPermissionBase(ObjectPermissionBase):
    member = models.ForeignKey('users.Member')

    class Meta:
        abstract = True
        unique_together = [
            ['member', 'content_object', 'permission']
        ]

    def __str__(self):
        return '%s %s %s' % (self.member, self.permission.name, self.content_object)


@python_2_unicode_compatible
class GroupObjectPermissionBase(ObjectPermissionBase):
    group = models.ForeignKey('users.Group')

    class Meta:
        abstract = True
        unique_together = [
            ['group', 'content_object', 'permission']
        ]

    def __str__(self):
        return '%s %s %s' % (self.group, self.permission.name, self.content_object)


class UserObjectPermission(UserObjectPermissionBase):
    content_type = models.ForeignKey(ContentType, related_name='user_object_permissions')
    object_id = models.BigIntegerField()
    content_object = GenericForeignKey()

    class Meta:
        verbose_name = _('generic user object permission')
        verbose_name_plural = _('generic user object permissions')
        unique_together = [
            ['member', 'content_type', 'object_id', 'permission']
        ]


class GroupObjectPermission(GroupObjectPermissionBase):
    content_type = models.ForeignKey(ContentType, related_name='group_object_permissions')
    object_id = models.BigIntegerField()
    content_object = GenericForeignKey()

    class Meta:
        verbose_name = _('generic group object permission')
        verbose_name_plural = _('generic group object permissions')
        unique_together = [
            ['group', 'content_type', 'object_id', 'permission']
        ]


# class ThreadUserObjectPermission(UserObjectPermissionBase):
#     content_object = models.ForeignKey(Thread, related_name='user_object_permissions')
#
#     class Meta(UserObjectPermissionBase.Meta):
#         verbose_name = _('thread user permission')
#         verbose_name_plural = _('thread user permissions')
#
#
# class ThreadGroupObjectPermission(GroupObjectPermissionBase):
#     content_object = models.ForeignKey(Thread, related_name='group_object_permissions')
#
#     class Meta(GroupObjectPermissionBase.Meta):
#         verbose_name = _('thread group permission')
#         verbose_name_plural = _('thread group permissions')

# @receiver(post_save, dispatch_uid='obj_perms_thread_saved', sender=Thread)
# def obj_perms_thread_saved(sender, instance=None, created=None, **kwargs):
#     if created:
