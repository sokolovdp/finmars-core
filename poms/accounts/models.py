from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeForeignKey, TreeManyToManyField
from mptt.models import MPTTModel

from poms.audit import history
from poms.common.models import NamedModel, TagModelBase
from poms.currencies.models import Currency
from poms.users.models import MasterUser, UserObjectPermissionBase, GroupObjectPermissionBase


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


class AccountTag(TagModelBase):
    master_user = models.ForeignKey(MasterUser, related_name='account_tags', verbose_name=_('master user'))

    class Meta:
        verbose_name = _('account tag')
        verbose_name_plural = _('account tags')
        unique_together = [
            ['master_user', 'user_code'],
            ['master_user', 'name'],
        ]
        permissions = [
            ('view_accounttag', 'Can view account tag')
        ]


@python_2_unicode_compatible
class Account(NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='accounts', verbose_name=_('master user'))
    type = models.ForeignKey(AccountType, null=True, blank=True)
    classifiers = TreeManyToManyField(AccountClassifier, blank=True)
    tags = models.ManyToManyField(AccountTag, blank=True)

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


# class AccountTypeUserObjectPermission(UserObjectPermissionBase):
#     content_object = models.ForeignKey(Account)
#
#     class Meta:
#         verbose_name = _('account types - user permission')
#         verbose_name_plural = _('account types - user permissions')
#
#
# class AccountTypeGroupObjectPermission(GroupObjectPermissionBase):
#     content_object = models.ForeignKey(Account)
#
#     class Meta:
#         verbose_name = _('account types - group permission')
#         verbose_name_plural = _('account types - group permissions')
#
#
# class AccountClassifierUserObjectPermission(UserObjectPermissionBase):
#     content_object = models.ForeignKey(AccountClassifier)
#
#     class Meta:
#         verbose_name = _('account classifiers - user permission')
#         verbose_name_plural = _('account classifiers - user permissions')
#
#
# class AccountClassifierGroupObjectPermission(GroupObjectPermissionBase):
#     content_object = models.ForeignKey(AccountClassifier)
#
#     class Meta:
#         verbose_name = _('account classifiers - group permission')
#         verbose_name_plural = _('account classifiers - group permissions')
#
#
# class AccountUserObjectPermission(UserObjectPermissionBase):
#     content_object = models.ForeignKey(Account)
#
#     class Meta:
#         verbose_name = _('accounts - user permission')
#         verbose_name_plural = _('accounts - user permissions')
#
#
# class AccountGroupObjectPermission(GroupObjectPermissionBase):
#     content_object = models.ForeignKey(Account)
#
#     class Meta:
#         verbose_name = _('accounts - group permission')
#         verbose_name_plural = _('accounts - group permissions')


# AccountUserObjectPermission, AccountGroupObjectPermission = object_permissions.register_model(Account)

history.register(AccountClassifier)
history.register(AccountType)
history.register(Account)
