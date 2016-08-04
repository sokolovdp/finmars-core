from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _
from mptt.models import MPTTModel

from poms.common.models import NamedModel
from poms.obj_perms.models import AbstractGroupObjectPermission, AbstractUserObjectPermission
from poms.users.models import MasterUser


# 1 --


class Strategy1Group(NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='strategy1_groups', verbose_name=_('master user'))

    class Meta(NamedModel.Meta):
        verbose_name = _('strategy1 group')
        verbose_name_plural = _('strategy1 groups')
        permissions = [
            ('view_strategy1group', 'Can view strategy1 group'),
            ('manage_strategy1group', 'Can manage strategy1 group'),
        ]
        unique_together = [
            ['master_user', 'user_code']
        ]

    @property
    def is_default(self):
        return self.master_user.strategy1_group_id == self.id if self.master_user_id else False


class Strategy1GroupUserObjectPermission(AbstractUserObjectPermission):
    content_object = models.ForeignKey(Strategy1Group, related_name='user_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractUserObjectPermission.Meta):
        verbose_name = _('strategy1 groups - user permission')
        verbose_name_plural = _('strategy1 groups - user permissions')


class Strategy1GroupGroupObjectPermission(AbstractGroupObjectPermission):
    content_object = models.ForeignKey(Strategy1Group, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractGroupObjectPermission.Meta):
        verbose_name = _('strategy1 groups - group permission')
        verbose_name_plural = _('strategy1 groups - group permissions')


class Strategy1Subgroup(NamedModel):
    group = models.ForeignKey(Strategy1Group, null=True, blank=True, on_delete=models.PROTECT, related_name='subgroups')

    class Meta(NamedModel.Meta):
        verbose_name = _('strategy1 subgroup')
        verbose_name_plural = _('strategy1 subgroups')
        permissions = [
            ('view_strategy1subgroup', 'Can view strategy1 subgroup'),
            ('manage_strategy1subgroup', 'Can manage strategy1 subgroup'),
        ]
        unique_together = [
            ['group', 'user_code']
        ]

    @property
    def is_default(self):
        return self.master_user.strategy1_subgroup_id == self.id if self.master_user_id else False


class Strategy1SubgroupUserObjectPermission(AbstractUserObjectPermission):
    content_object = models.ForeignKey(Strategy1Subgroup, related_name='user_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractUserObjectPermission.Meta):
        verbose_name = _('strategy1 subgroups - user permission')
        verbose_name_plural = _('strategy1 subgroups - user permissions')


class Strategy1SubgroupGroupObjectPermission(AbstractGroupObjectPermission):
    content_object = models.ForeignKey(Strategy1Subgroup, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractGroupObjectPermission.Meta):
        verbose_name = _('strategy1 subgroups - group permission')
        verbose_name_plural = _('strategy1 subgroups - group permissions')


class Strategy1(NamedModel):
    subgroup = models.ForeignKey(Strategy1Subgroup, null=True, blank=True, on_delete=models.PROTECT,
                                 related_name='strategies')

    class Meta(NamedModel.Meta):
        verbose_name = _('strategy1')
        verbose_name_plural = _('strategies1')
        permissions = [
            ('view_strategy1', 'Can view strategy1'),
            ('manage_strategy1', 'Can manage strategy1'),
        ]
        unique_together = [
            ['subgroup', 'user_code']
        ]

    @property
    def is_default(self):
        return self.master_user.strategy1_id == self.id if self.master_user_id else False


class Strategy1UserObjectPermission(AbstractUserObjectPermission):
    content_object = models.ForeignKey(Strategy1, related_name='user_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractUserObjectPermission.Meta):
        verbose_name = _('strategies - user permission')
        verbose_name_plural = _('strategies - user permissions')


class Strategy1GroupObjectPermission(AbstractGroupObjectPermission):
    content_object = models.ForeignKey(Strategy1, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractGroupObjectPermission.Meta):
        verbose_name = _('strategies - group permission')
        verbose_name_plural = _('strategies - group permissions')


# 2 --


class Strategy2Group(NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='strategy2_groups', verbose_name=_('master user'))

    class Meta(NamedModel.Meta):
        verbose_name = _('strategy2 group')
        verbose_name_plural = _('strategy2 groups')
        permissions = [
            ('view_strategy2group', 'Can view strategy2 group'),
            ('manage_strategy2group', 'Can manage strategy2 group'),
        ]
        unique_together = [
            ['master_user', 'user_code']
        ]

    @property
    def is_default(self):
        return self.master_user.strategy2_group_id == self.id if self.master_user_id else False


class Strategy2GroupUserObjectPermission(AbstractUserObjectPermission):
    content_object = models.ForeignKey(Strategy2Group, related_name='user_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractUserObjectPermission.Meta):
        verbose_name = _('strategy2 groups - user permission')
        verbose_name_plural = _('strategy2 groups - user permissions')


class Strategy2GroupGroupObjectPermission(AbstractGroupObjectPermission):
    content_object = models.ForeignKey(Strategy2Group, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractGroupObjectPermission.Meta):
        verbose_name = _('strategy2 groups - group permission')
        verbose_name_plural = _('strategy2 groups - group permissions')


class Strategy2Subgroup(NamedModel):
    group = models.ForeignKey(Strategy2Group, null=True, blank=True, on_delete=models.PROTECT, related_name='subgroups')

    class Meta(NamedModel.Meta):
        verbose_name = _('strategy2 subgroup')
        verbose_name_plural = _('strategy2 subgroups')
        permissions = [
            ('view_strategy2subgroup', 'Can view strategy2 subgroup'),
            ('manage_strategy2subgroup', 'Can manage strategy2 subgroup'),
        ]
        unique_together = [
            ['group', 'user_code']
        ]

    @property
    def is_default(self):
        return self.master_user.strategy2_subgroup_id == self.id if self.master_user_id else False


class Strategy2SubgroupUserObjectPermission(AbstractUserObjectPermission):
    content_object = models.ForeignKey(Strategy2Subgroup, related_name='user_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractUserObjectPermission.Meta):
        verbose_name = _('strategy2 subgroups - user permission')
        verbose_name_plural = _('strategy2 subgroups - user permissions')


class Strategy2SubgroupGroupObjectPermission(AbstractGroupObjectPermission):
    content_object = models.ForeignKey(Strategy2Subgroup, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractGroupObjectPermission.Meta):
        verbose_name = _('strategy2 subgroups - group permission')
        verbose_name_plural = _('strategy2 subgroups - group permissions')


class Strategy2(NamedModel):
    subgroup = models.ForeignKey(Strategy2Subgroup, null=True, blank=True, on_delete=models.PROTECT,
                                 related_name='strategies')

    class Meta(NamedModel.Meta):
        verbose_name = _('strategy2')
        verbose_name_plural = _('strategies2')
        permissions = [
            ('view_strategy2', 'Can view strategy2'),
            ('manage_strategy2', 'Can manage strategy2'),
        ]
        unique_together = [
            ['subgroup', 'user_code']
        ]

    @property
    def is_default(self):
        return self.master_user.strategy2_id == self.id if self.master_user_id else False


class Strategy2UserObjectPermission(AbstractUserObjectPermission):
    content_object = models.ForeignKey(Strategy2, related_name='user_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractUserObjectPermission.Meta):
        verbose_name = _('strategies - user permission')
        verbose_name_plural = _('strategies - user permissions')


class Strategy2GroupObjectPermission(AbstractGroupObjectPermission):
    content_object = models.ForeignKey(Strategy2, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractGroupObjectPermission.Meta):
        verbose_name = _('strategies - group permission')
        verbose_name_plural = _('strategies - group permissions')


# 3 --


class Strategy3Group(NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='strategy3_groups', verbose_name=_('master user'))

    class Meta(NamedModel.Meta):
        verbose_name = _('strategy3 group')
        verbose_name_plural = _('strategy3 groups')
        permissions = [
            ('view_strategy3group', 'Can view strategy3 group'),
            ('manage_strategy3group', 'Can manage strategy3 group'),
        ]
        unique_together = [
            ['master_user', 'user_code']
        ]

    @property
    def is_default(self):
        return self.master_user.strategy3_group_id == self.id if self.master_user_id else False


class Strategy3GroupUserObjectPermission(AbstractUserObjectPermission):
    content_object = models.ForeignKey(Strategy3Group, related_name='user_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractUserObjectPermission.Meta):
        verbose_name = _('strategy3 groups - user permission')
        verbose_name_plural = _('strategy3 groups - user permissions')


class Strategy3GroupGroupObjectPermission(AbstractGroupObjectPermission):
    content_object = models.ForeignKey(Strategy3Group, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractGroupObjectPermission.Meta):
        verbose_name = _('strategy3 groups - group permission')
        verbose_name_plural = _('strategy3 groups - group permissions')


class Strategy3Subgroup(NamedModel):
    group = models.ForeignKey(Strategy3Group, null=True, blank=True, on_delete=models.PROTECT, related_name='subgroups')

    class Meta(NamedModel.Meta):
        verbose_name = _('strategy3 subgroup')
        verbose_name_plural = _('strategy3 subgroups')
        permissions = [
            ('view_strategy3subgroup', 'Can view strategy3 subgroup'),
            ('manage_strategy3subgroup', 'Can manage strategy3 subgroup'),
        ]
        unique_together = [
            ['group', 'user_code']
        ]

    @property
    def is_default(self):
        return self.master_user.strategy3_subgroup_id == self.id if self.master_user_id else False


class Strategy3SubgroupUserObjectPermission(AbstractUserObjectPermission):
    content_object = models.ForeignKey(Strategy3Subgroup, related_name='user_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractUserObjectPermission.Meta):
        verbose_name = _('strategy3 subgroups - user permission')
        verbose_name_plural = _('strategy3 subgroups - user permissions')


class Strategy3SubgroupGroupObjectPermission(AbstractGroupObjectPermission):
    content_object = models.ForeignKey(Strategy3Subgroup, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractGroupObjectPermission.Meta):
        verbose_name = _('strategy3 subgroups - group permission')
        verbose_name_plural = _('strategy3 subgroups - group permissions')


class Strategy3(NamedModel):
    subgroup = models.ForeignKey(Strategy3Subgroup, null=True, blank=True, on_delete=models.PROTECT,
                                 related_name='strategies')

    class Meta(NamedModel.Meta):
        verbose_name = _('strategy3')
        verbose_name_plural = _('strategies3')
        permissions = [
            ('view_strategy3', 'Can view strategy3'),
            ('manage_strategy3', 'Can manage strategy3'),
        ]
        unique_together = [
            ['subgroup', 'user_code']
        ]

    @property
    def is_default(self):
        return self.master_user.strategy3_id == self.id if self.master_user_id else False


class Strategy3UserObjectPermission(AbstractUserObjectPermission):
    content_object = models.ForeignKey(Strategy3, related_name='user_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractUserObjectPermission.Meta):
        verbose_name = _('strategies - user permission')
        verbose_name_plural = _('strategies - user permissions')


class Strategy3GroupObjectPermission(AbstractGroupObjectPermission):
    content_object = models.ForeignKey(Strategy3, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractGroupObjectPermission.Meta):
        verbose_name = _('strategies - group permission')
        verbose_name_plural = _('strategies - group permissions')
