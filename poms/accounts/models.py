from __future__ import unicode_literals, print_function

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from poms.common.models import NamedModel, FakeDeletableModel
from poms.currencies.models import Currency
from poms.obj_attrs.models import AbstractAttributeType, AbstractAttribute, AbstractAttributeTypeOption, \
    AbstractClassifier
from poms.obj_perms.models import AbstractGroupObjectPermission, AbstractUserObjectPermission
from poms.users.models import MasterUser, Member


@python_2_unicode_compatible
class AccountType(NamedModel, FakeDeletableModel):
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
            ('view_accounttype', 'Can view account type'),
            ('manage_accounttype', 'Can manage account type'),
        ]

    def __str__(self):
        return self.user_code

    @property
    def is_default(self):
        return self.master_user.account_type_id == self.id if self.master_user_id else False


class AccountTypeUserObjectPermission(AbstractUserObjectPermission):
    content_object = models.ForeignKey(AccountType, related_name='user_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractUserObjectPermission.Meta):
        verbose_name = _('account types - user permission')
        verbose_name_plural = _('account types - user permissions')


class AccountTypeGroupObjectPermission(AbstractGroupObjectPermission):
    content_object = models.ForeignKey(AccountType, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractGroupObjectPermission.Meta):
        verbose_name = _('account types - group permission')
        verbose_name_plural = _('account types - group permissions')


@python_2_unicode_compatible
class Account(NamedModel, FakeDeletableModel):
    master_user = models.ForeignKey(MasterUser, related_name='accounts',
                                    verbose_name=_('master user'))
    type = models.ForeignKey(AccountType, on_delete=models.PROTECT, null=True, blank=True,
                             verbose_name=_('account type'))
    is_valid_for_all_portfolios = models.BooleanField(default=True)

    class Meta(NamedModel.Meta):
        verbose_name = _('account')
        verbose_name_plural = _('accounts')
        permissions = [
            ('view_account', 'Can view account'),
            ('manage_account', 'Can manage account'),
        ]

    def __str__(self):
        return self.user_code

    @property
    def is_default(self):
        return self.master_user.account_id == self.id if self.master_user_id else False


class AccountUserObjectPermission(AbstractUserObjectPermission):
    content_object = models.ForeignKey(Account, related_name='user_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractUserObjectPermission.Meta):
        verbose_name = _('accounts - user permission')
        verbose_name_plural = _('accounts - user permissions')


class AccountGroupObjectPermission(AbstractGroupObjectPermission):
    content_object = models.ForeignKey(Account, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractGroupObjectPermission.Meta):
        verbose_name = _('accounts - group permission')
        verbose_name_plural = _('accounts - group permissions')


class AccountAttributeType(AbstractAttributeType):
    # classifier_root = models.OneToOneField(
    #     AccountClassifier,
    #     null=True,
    #     blank=True,
    #     on_delete=models.PROTECT,
    #     verbose_name=_('classifier')
    # )

    class Meta(AbstractAttributeType.Meta):
        verbose_name = _('account attribute type')
        verbose_name_plural = _('account attribute types')
        permissions = [
            ('view_accountattributetype', 'Can view account attribute type'),
            ('manage_accountattributetype', 'Can manage account attribute type'),
        ]


class AccountAttributeTypeUserObjectPermission(AbstractUserObjectPermission):
    content_object = models.ForeignKey(AccountAttributeType, related_name='user_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractUserObjectPermission.Meta):
        verbose_name = _('account attribute types - user permission')
        verbose_name_plural = _('account attribute types - user permissions')


class AccountAttributeTypeGroupObjectPermission(AbstractGroupObjectPermission):
    content_object = models.ForeignKey(AccountAttributeType, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractGroupObjectPermission.Meta):
        verbose_name = _('account attribute types - group permission')
        verbose_name_plural = _('account attribute types - group permissions')


class AccountClassifier(AbstractClassifier):
    attribute_type = models.ForeignKey(AccountAttributeType, related_name='classifiers',
                                       verbose_name=_('attribute type'))
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True,
                            verbose_name=_('parent'))

    class Meta(AbstractClassifier.Meta):
        verbose_name = _('account classifier')
        verbose_name_plural = _('account classifiers')


class AccountAttributeTypeOption(AbstractAttributeTypeOption):
    member = models.ForeignKey(Member, related_name='account_attribute_type_options',
                               verbose_name=_('member'))
    attribute_type = models.ForeignKey(AccountAttributeType, related_name='options',
                                       verbose_name=_('attribute type'))

    class Meta(AbstractAttributeTypeOption.Meta):
        verbose_name = _('account attribute types - option')
        verbose_name_plural = _('account attribute types - options')


class AccountAttribute(AbstractAttribute):
    attribute_type = models.ForeignKey(AccountAttributeType, related_name='attributes',
                                       verbose_name=_('attribute type'))
    content_object = models.ForeignKey(Account, related_name='attributes',
                                       verbose_name=_('content object'))
    classifier = models.ForeignKey(AccountClassifier, on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name=_('classifier'))

    class Meta(AbstractAttribute.Meta):
        verbose_name = _('account attribute')
        verbose_name_plural = _('account attributes')
