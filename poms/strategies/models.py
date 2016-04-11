from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from poms.audit import history
from poms.common.models import NamedModel
from poms.obj_perms.models import UserObjectPermissionBase, GroupObjectPermissionBase
from poms.users.models import MasterUser


class Strategy(NamedModel, MPTTModel):
    master_user = models.ForeignKey(MasterUser, related_name='strategy_classifiers', verbose_name=_('master user'))
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)

    class MPTTMeta:
        order_insertion_by = ['master_user', 'name']

    class Meta:
        verbose_name = _('strategy')
        verbose_name_plural = _('strategies')
        unique_together = [
            ['master_user', 'user_code']
        ]
        permissions = [
            ('view_strategy', 'Can view strategy')
        ]


class StrategyUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(Strategy, related_name='user_object_permissions')

    class Meta:
        verbose_name = _('strategies - user permission')
        verbose_name_plural = _('strategies - user permissions')


class StrategyGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(Strategy, related_name='group_object_permissions')

    class Meta:
        verbose_name = _('strategies - group permission')
        verbose_name_plural = _('strategies - group permissions')


history.register(Strategy)
