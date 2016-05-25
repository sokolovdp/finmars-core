from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from poms.audit import history
from poms.common.models import NamedModel, TagModelBase
from poms.currencies.models import Currency
from poms.obj_attrs.models import AttributeTypeBase, AttributeBase, AttributeTypeOptionBase
from poms.obj_perms.models import GroupObjectPermissionBase
from poms.users.models import MasterUser, Member


@python_2_unicode_compatible
class AccountType(NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='account_types',
                                    verbose_name=_('master user'))
    show_transaction_details = models.BooleanField(default=False,
                                                   verbose_name=_('show transaction details'))
    transaction_details_expr = models.CharField(max_length=255, null=True, blank=True,
                                                verbose_name=_('transaction details expr'))

    class Meta(NamedModel.Meta):
        verbose_name = _('account type')
        verbose_name_plural = _('account types')
        permissions = [
            ('view_accounttype', 'Can view account type')
        ]

    def __str__(self):
        return self.name


# class AccountTypeUserObjectPermission(UserObjectPermissionBase):
#     content_object = models.ForeignKey(AccountType, related_name='user_object_permissions',
#                                        verbose_name=_('content object'))
#
#     class Meta(UserObjectPermissionBase.Meta):
#         verbose_name = _('account types - user permission')
#         verbose_name_plural = _('account types - user permissions')


class AccountTypeGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(AccountType, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(GroupObjectPermissionBase.Meta):
        verbose_name = _('account types - group permission')
        verbose_name_plural = _('account types - group permissions')


@python_2_unicode_compatible
class Account(NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='accounts',
                                    verbose_name=_('master user'))
    type = models.ForeignKey(AccountType, on_delete=models.PROTECT, null=True, blank=True,
                             verbose_name=_('account type'))

    class Meta(NamedModel.Meta):
        verbose_name = _('account')
        verbose_name_plural = _('accounts')
        permissions = [
            ('view_account', 'Can view account')
        ]

    def __str__(self):
        return self.name


# class AccountUserObjectPermission(UserObjectPermissionBase):
#     content_object = models.ForeignKey(Account, related_name='user_object_permissions',
#                                        verbose_name=_('content object'))
#
#     class Meta(UserObjectPermissionBase.Meta):
#         verbose_name = _('accounts - user permission')
#         verbose_name_plural = _('accounts - user permissions')


class AccountGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(Account, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(GroupObjectPermissionBase.Meta):
        verbose_name = _('accounts - group permission')
        verbose_name_plural = _('accounts - group permissions')


class AccountAttributeType(AttributeTypeBase):
    # classifier_root = models.OneToOneField(
    #     AccountClassifier,
    #     null=True,
    #     blank=True,
    #     on_delete=models.PROTECT,
    #     verbose_name=_('classifier')
    # )

    class Meta(AttributeTypeBase.Meta):
        verbose_name = _('account attribute type')
        verbose_name_plural = _('account attribute types')
        permissions = [
            ('view_accountattributetype', 'Can view account attribute type')
        ]


class AccountAttributeTypeGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(AccountAttributeType, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(GroupObjectPermissionBase.Meta):
        verbose_name = _('account attribute types - group permission')
        verbose_name_plural = _('account attribute types - group permissions')


class AccountClassifier(MPTTModel, NamedModel):
    # master_user = models.ForeignKey(
    #     MasterUser,
    #     null=True,
    #     blank=True,
    #     related_name='account_classifiers',
    #     verbose_name=_('master user')
    # )
    attribute_type = models.ForeignKey(
        AccountAttributeType,
        null=True,
        blank=True,
        related_name='classifiers',
        verbose_name=_('attribute type')
    )
    parent = TreeForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='children',
        db_index=True,
        verbose_name=_('parent')
    )

    class MPTTMeta:
        order_insertion_by = ['attribute_type', 'name']

    class Meta(NamedModel.Meta):
        verbose_name = _('account classifier')
        verbose_name_plural = _('account classifiers')
        unique_together = [
            ['attribute_type', 'user_code']
        ]


class AccountAttributeTypeOption(AttributeTypeOptionBase):
    member = models.ForeignKey(Member, related_name='account_attribute_type_options',
                               verbose_name=_('member'))
    attribute_type = models.ForeignKey(AccountAttributeType, related_name='options',
                                       verbose_name=_('attribute type'))

    class Meta(AttributeTypeOptionBase.Meta):
        verbose_name = _('account attribute types - option')
        verbose_name_plural = _('account attribute types - options')


# class AccountAttributeTypeUserObjectPermission(UserObjectPermissionBase):
#     content_object = models.ForeignKey(AccountAttributeType, related_name='user_object_permissions',
#                                        verbose_name=_('content object'))
#
#     class Meta(UserObjectPermissionBase.Meta):
#         verbose_name = _('account attribute types - user permission')
#         verbose_name_plural = _('account attribute types - user permissions')

class AccountAttribute(AttributeBase):
    attribute_type = models.ForeignKey(AccountAttributeType, on_delete=models.PROTECT, related_name='attributes',
                                       verbose_name=_('attribute type'))
    content_object = models.ForeignKey(Account, related_name='attributes',
                                       verbose_name=_('content object'))
    classifier = models.ForeignKey(AccountClassifier, on_delete=models.PROTECT, null=True, blank=True,
                                   verbose_name=_('classifier'))

    class Meta(AttributeBase.Meta):
        verbose_name = _('account attribute')
        verbose_name_plural = _('account attributes')


history.register(AccountType)
history.register(AccountClassifier)
history.register(Account)
history.register(AccountAttributeType)
history.register(AccountAttributeTypeOption)
history.register(AccountAttribute)
