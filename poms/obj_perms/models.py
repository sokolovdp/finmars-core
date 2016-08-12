from __future__ import unicode_literals

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from poms.users.models import Member, Group


class AbstractObjectPermission(models.Model):
    # in child object: content_object -> actual object
    permission = models.ForeignKey(Permission, verbose_name=_('permission'))

    class Meta:
        abstract = True


@python_2_unicode_compatible
class AbstractUserObjectPermission(AbstractObjectPermission):
    # in child object: content_object -> actual object
    member = models.ForeignKey(Member, verbose_name=_('member'))

    class Meta(AbstractObjectPermission.Meta):
        abstract = True
        unique_together = [
            ['content_object', 'member', 'permission']
        ]
        verbose_name = _('user permission')
        verbose_name_plural = _('user permissions')

    def __str__(self):
        return 'Member "%s" %s "%s"' % (self.member, self.permission.name.lower(), self.content_object)


@python_2_unicode_compatible
class AbstractGroupObjectPermission(AbstractObjectPermission):
    # in child object: content_object -> actual object
    group = models.ForeignKey(Group, verbose_name=_('group'))

    class Meta(AbstractObjectPermission.Meta):
        abstract = True
        unique_together = [
            ['content_object', 'group', 'permission']
        ]
        verbose_name = _('group permission')
        verbose_name_plural = _('group permissions')

    def __str__(self):
        return 'Group "%s" %s "%s"' % (self.group, self.permission.name.lower(), self.content_object)
