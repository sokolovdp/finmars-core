from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeForeignKey, TreeManyToManyField
from mptt.models import MPTTModel

from poms.audit import history
from poms.currencies.models import Currency
from poms.users.models import MasterUser, UserObjectPermissionBase, GroupObjectPermissionBase


@python_2_unicode_compatible
class AccountType(models.Model):
    master_user = models.ForeignKey(MasterUser, related_name='account_types', verbose_name=_('master user'))
    user_code = models.CharField(max_length=25, null=True, blank=True)
    name = models.CharField(max_length=255, verbose_name=_('name'))
    short_name = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('short name'))
    notes = models.TextField(null=True, blank=True)
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
class AccountClassifier(MPTTModel):
    master_user = models.ForeignKey(MasterUser, related_name='account_classifiers', verbose_name=_('master user'))
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)
    user_code = models.CharField(max_length=25, null=True, blank=True)
    name = models.CharField(max_length=255, verbose_name=_('name'))
    short_name = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('short name'))
    notes = models.TextField(null=True, blank=True)

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


@python_2_unicode_compatible
class Account(models.Model):
    master_user = models.ForeignKey(MasterUser, related_name='accounts', verbose_name=_('master user'))
    user_code = models.CharField(max_length=25, null=True, blank=True)
    name = models.CharField(max_length=255, verbose_name=_('name'))
    short_name = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('short name'))
    notes = models.TextField(null=True, blank=True)
    type = models.ForeignKey(AccountType, null=True, blank=True)
    classifiers = TreeManyToManyField(AccountClassifier, blank=True)

    # notes = models.TextField(null=True, blank=True, default='', verbose_name=_('description'))

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
