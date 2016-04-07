from __future__ import unicode_literals

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
        return '%s - %s - %s' % (self.member, self.content_object, self.permission)


@python_2_unicode_compatible
class GroupObjectPermissionBase(ObjectPermissionBase):
    group = models.ForeignKey('users.Group')

    class Meta:
        abstract = True
        unique_together = [
            ['group', 'content_object', 'permission']
        ]

    def __str__(self):
        return '%s - %s - %s' % (self.group, self.content_object, self.permission)


class ThreadUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(Thread, related_name='user_object_permissions')

    class Meta(UserObjectPermissionBase.Meta):
        verbose_name = _('thread user permission')
        verbose_name_plural = _('thread user permissions')


class ThreadGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(Thread, related_name='group_object_permissions')

    class Meta(GroupObjectPermissionBase.Meta):
        verbose_name = _('thread group permission')
        verbose_name_plural = _('thread group permissions')

# @receiver(post_save, dispatch_uid='obj_perms_thread_saved', sender=Thread)
# def obj_perms_thread_saved(sender, instance=None, created=None, **kwargs):
#     if created:
