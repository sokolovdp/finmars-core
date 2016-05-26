from __future__ import unicode_literals

from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from poms.audit import history
from poms.common.models import NamedModel
from poms.obj_perms.models import GroupObjectPermissionBase
from poms.users.models import MasterUser


class Strategy(MPTTModel, NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='strategies',
                                    verbose_name=_('master user'))
    parent = TreeForeignKey('self', related_name='children', null=True, blank=True, db_index=True,
                            verbose_name=_('parent'))

    class MPTTMeta:
        order_insertion_by = ['master_user', 'name']

    class Meta(NamedModel.Meta):
        verbose_name = _('strategy')
        verbose_name_plural = _('strategies')
        permissions = [
            ('view_strategy', 'Can view strategy')
        ]


# class StrategyUserObjectPermission(UserObjectPermissionBase):
#     content_object = models.ForeignKey(Strategy, related_name='user_object_permissions',
#                                        verbose_name=_('content object'))
#
#     class Meta(UserObjectPermissionBase.Meta):
#         verbose_name = _('strategies - user permission')
#         verbose_name_plural = _('strategies - user permissions')


class StrategyGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(Strategy, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(GroupObjectPermissionBase.Meta):
        verbose_name = _('strategies - group permission')
        verbose_name_plural = _('strategies - group permissions')


class Strategy1(MPTTModel, NamedModel):
    master_user = models.ForeignKey(
        MasterUser,
        related_name='strategies1',
        verbose_name=_('master user')
    )
    parent = TreeForeignKey(
        'self',
        related_name='children',
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_('parent')
    )

    class MPTTMeta:
        order_insertion_by = ['master_user', 'name']

    class Meta(NamedModel.Meta):
        verbose_name = _('strategy - 1')
        verbose_name_plural = _('strategies - 1')


# class Strategy1UserObjectPermission(UserObjectPermissionBase):
#     content_object = models.ForeignKey(
#         Strategy1,
#         related_name='user_object_permissions',
#         verbose_name=_('content object')
#     )
#
#     class Meta(UserObjectPermissionBase.Meta):
#         verbose_name = _('strategies - 1 - user permission')
#         verbose_name_plural = _('strategies - 1 - user permissions')


class Strategy1GroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(
        Strategy1,
        related_name='group_object_permissions',
        verbose_name=_('content object')
    )

    class Meta(GroupObjectPermissionBase.Meta):
        verbose_name = _('strategies - 1 - group permission')
        verbose_name_plural = _('strategies - 1 - group permissions')


class Strategy2(MPTTModel, NamedModel):
    master_user = models.ForeignKey(
        MasterUser,
        related_name='strategies2',
        verbose_name=_('master user')
    )
    parent = TreeForeignKey(
        'self',
        related_name='children',
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_('parent')
    )

    class MPTTMeta:
        order_insertion_by = ['master_user', 'name']

    class Meta(NamedModel.Meta):
        verbose_name = _('strategy - 2')
        verbose_name_plural = _('strategies - 2')


# class Strategy2UserObjectPermission(UserObjectPermissionBase):
#     content_object = models.ForeignKey(
#         Strategy2,
#         related_name='user_object_permissions',
#         verbose_name=_('content object')
#     )
#
#     class Meta(UserObjectPermissionBase.Meta):
#         verbose_name = _('strategies - 2 - user permission')
#         verbose_name_plural = _('strategies - 2 - user permissions')


class Strategy2GroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(
        Strategy2,
        related_name='group_object_permissions',
        verbose_name=_('content object')
    )

    class Meta(GroupObjectPermissionBase.Meta):
        verbose_name = _('strategies - 2 - group permission')
        verbose_name_plural = _('strategies - 2 - group permissions')


class Strategy3(MPTTModel, NamedModel):
    master_user = models.ForeignKey(
        MasterUser,
        related_name='strategies3',
        verbose_name=_('master user')
    )
    parent = TreeForeignKey(
        'self',
        related_name='children',
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_('parent')
    )

    class MPTTMeta:
        order_insertion_by = ['master_user', 'name']

    class Meta(NamedModel.Meta):
        verbose_name = _('strategy - 3')
        verbose_name_plural = _('strategies - 3')


# class Strategy3UserObjectPermission(UserObjectPermissionBase):
#     content_object = models.ForeignKey(
#         Strategy3,
#         related_name='user_object_permissions',
#         verbose_name=_('content object')
#     )
#
#     class Meta(UserObjectPermissionBase.Meta):
#         verbose_name = _('strategies - 3 - user permission')
#         verbose_name_plural = _('strategies - 3 - user permissions')


class Strategy3GroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(
        Strategy3,
        related_name='group_object_permissions',
        verbose_name=_('content object')
    )

    class Meta(GroupObjectPermissionBase.Meta):
        verbose_name = _('strategies - 3 - group permission')
        verbose_name_plural = _('strategies - 3 - group permissions')


def _strategy_post_save(instance, created, group_object_permission_model):
    if created and not instance.is_root_node():
        root = instance.get_root()
        perms = []
        for gop in root.group_object_permissions.all():
            perms.append(group_object_permission_model(content_object=instance,
                                                       group=gop.group,
                                                       permission=gop.permission))
        # group_object_permission_model.objects.filter(content_object=instance).delete()
        group_object_permission_model.objects.bulk_create(perms)


def _strategy_group_object_permission_post_save(instance, created, group_object_permission_model):
    if instance.content_object.is_root_node():
        if created:
            perms = []
            for o in instance.content_object.get_family():
                if o.is_root_node():
                    continue
                perms.append(group_object_permission_model(content_object=o,
                                                           group=instance.group,
                                                           permission=instance.permission))
            group_object_permission_model.objects.bulk_create(perms)
        else:
            group_object_permission_model.objects.filter(
                id__in=instance.content_object.get_family().exclude(id=instance.content_object_id)).update(
                group=instance.group,
                permission=instance.permission
            )


def _strategy_group_object_permission_post_delete(instance, group_object_permission_model):
    if instance.content_object.is_root_node():
        group_object_permission_model.objects.filter(content_object__in=instance.content_object.get_family()).delete()


@receiver(post_save, sender=Strategy1, dispatch_uid='strategy1_post_save')
def strategy1_post_save(sender, instance=None, created=None, **kwargs):
    _strategy_post_save(instance, created, Strategy1GroupObjectPermission)


@receiver(post_save, sender=Strategy1GroupObjectPermission,
          dispatch_uid='strategy1_group_object_permission_post_save')
def strategy1_group_object_permission_post_save(sender, instance=None, created=None, **kwargs):
    _strategy_group_object_permission_post_save(instance, created, Strategy1GroupObjectPermission)


@receiver(post_delete, sender=Strategy1GroupObjectPermission,
          dispatch_uid='strategy1_group_object_permission_post_delete')
def strategy1_group_object_permission_post_delete(sender, instance=None, **kwargs):
    _strategy_group_object_permission_post_delete(instance, Strategy1GroupObjectPermission)


@receiver(post_save, sender=Strategy2, dispatch_uid='strategy2_post_save')
def strategy2_post_save(sender, instance=None, created=None, **kwargs):
    _strategy_post_save(instance, created, Strategy2GroupObjectPermission)


@receiver(post_save, sender=Strategy2GroupObjectPermission,
          dispatch_uid='strategy2_group_object_permission_post_save')
def strategy2_group_object_permission_post_save(sender, instance=None, created=None, **kwargs):
    _strategy_group_object_permission_post_save(instance, created, Strategy2GroupObjectPermission)


@receiver(post_delete, sender=Strategy2GroupObjectPermission,
          dispatch_uid='strategy2_group_object_permission_post_delete')
def strategy2_group_object_permission_post_delete(sender, instance=None, **kwargs):
    _strategy_group_object_permission_post_delete(instance, Strategy2GroupObjectPermission)


@receiver(post_save, sender=Strategy3, dispatch_uid='strategy3_post_save')
def strategy3_post_save(sender, instance=None, created=None, **kwargs):
    _strategy_post_save(instance, created, Strategy3GroupObjectPermission)


@receiver(post_save, sender=Strategy3GroupObjectPermission,
          dispatch_uid='strategy3_group_object_permission_post_save')
def strategy3_group_object_permission_post_save(sender, instance=None, created=None, **kwargs):
    _strategy_group_object_permission_post_save(instance, created, Strategy3GroupObjectPermission)


@receiver(post_delete, sender=Strategy3GroupObjectPermission,
          dispatch_uid='strategy3_group_object_permission_post_delete')
def strategy3_group_object_permission_post_delete(sender, instance=None, **kwargs):
    _strategy_group_object_permission_post_delete(instance, Strategy3GroupObjectPermission)


# history.register(Strategy)
history.register(Strategy1)
history.register(Strategy2)
history.register(Strategy3)
