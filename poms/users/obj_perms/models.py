from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible


class ObjectPermissionBase(models.Model):
    permission = models.ForeignKey('auth.Permission')

    class Meta:
        abstract = True


@python_2_unicode_compatible
class UserObjectPermissionBase(ObjectPermissionBase):
    member = models.ForeignKey('users.Member')

    class Meta:
        abstract = True

    def __str__(self):
        return '%s - %s - %s' % (self.content_object, self.member, self.permission)


@python_2_unicode_compatible
class GroupObjectPermissionBase(ObjectPermissionBase):
    group = models.ForeignKey('users.Group')

    class Meta:
        abstract = True

    def __str__(self):
        return '%s - %s - %s' % (self.content_object, self.group, self.permission)
