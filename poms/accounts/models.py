from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from poms.audit import history
from poms.common.models import NamedModel, TagModelBase
from poms.currencies.models import Currency
from poms.obj_attrs.models import AttributeTypeBase, AttributeBase
from poms.obj_perms.models import UserObjectPermissionBase, GroupObjectPermissionBase
from poms.users.models import MasterUser


@python_2_unicode_compatible
class AccountType(NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='account_types', verbose_name=_('master user'))
    show_transaction_details = models.BooleanField(default=False)
    transaction_details_expr = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = _('account type')
        verbose_name_plural = _('account types')
        unique_together = [
            ['master_user', 'user_code']
        ]
        permissions = [
            ('view_accounttype', 'Can view account type')
        ]

    def __str__(self):
        return self.name


class AccountTypeUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(AccountType, related_name='user_object_permissions')


class AccountTypeGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(AccountType, related_name='group_object_permissions')


@python_2_unicode_compatible
class AccountClassifier(NamedModel, MPTTModel):
    master_user = models.ForeignKey(MasterUser, related_name='account_classifiers', verbose_name=_('master user'))
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)

    class MPTTMeta:
        order_insertion_by = ['master_user', 'name']

    class Meta:
        verbose_name = _('account classifier')
        verbose_name_plural = _('account classifiers')
        unique_together = [
            ['master_user', 'user_code']
        ]
        permissions = [
            ('view_accountclassifier', 'Can view account classifier')
        ]

    def __str__(self):
        return self.name


class AccountClassifierUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(AccountClassifier, related_name='user_object_permissions')


class AccountClassifierGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(AccountClassifier, related_name='group_object_permissions')


@python_2_unicode_compatible
class Account(NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='accounts', verbose_name=_('master user'))
    type = models.ForeignKey(AccountType, null=True, blank=True)

    class Meta:
        verbose_name = _('account')
        verbose_name_plural = _('accounts')
        unique_together = [
            ['master_user', 'user_code']
        ]
        permissions = [
            ('view_account', 'Can view account')
        ]

    def __str__(self):
        return self.name


class AccountUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(Account, related_name='user_object_permissions')


class AccountGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(Account, related_name='group_object_permissions')


class AccountAttributeType(AttributeTypeBase):
    classifier_root = models.ForeignKey(AccountClassifier, null=True, blank=True)


class AccountAttributeTypeUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(AccountAttributeType, related_name='user_object_permissions')


class AccountAttributeTypeGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(AccountAttributeType, related_name='group_object_permissions')


class AccountAttribute(AttributeBase):
    attribute_type = models.ForeignKey(AccountAttributeType, related_name='attributes')
    content_object = models.ForeignKey(Account)
    classifier = models.ForeignKey(AccountClassifier, null=True, blank=True)


history.register(AccountType)
history.register(AccountClassifier)
history.register(Account)
history.register(AccountAttributeType)
history.register(AccountAttribute)
