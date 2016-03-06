from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeForeignKey, TreeManyToManyField
from mptt.models import MPTTModel

from poms.currencies.models import Currency
from poms.users.models import MasterUser


@python_2_unicode_compatible
class AccountType(models.Model):
    code = models.CharField(max_length=20, verbose_name=_('code'), help_text=_('system wide value'))
    name = models.CharField(max_length=255, verbose_name=_('name'))

    class Meta:
        verbose_name = _('account type')
        verbose_name_plural = _('account types')

    def __str__(self):
        return '%s' % (self.name,)


@python_2_unicode_compatible
class AccountClassifier(MPTTModel):
    master_user = models.ForeignKey(MasterUser, related_name='account_classifiers', verbose_name=_('master user'))
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)
    user_code = models.CharField(max_length=25, null=True, blank=True)
    name = models.CharField(max_length=255, verbose_name=_('name'))
    short_name = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('short name'))

    class MPTTMeta:
        order_insertion_by = ['master_user', 'name']

    class Meta:
        verbose_name = _('account classifier')
        verbose_name_plural = _('account classifiers')

    def __str__(self):
        return '%s (%s)' % (self.name, self.master_user.user.username)


@python_2_unicode_compatible
class Account(models.Model):
    master_user = models.ForeignKey(MasterUser, related_name='accounts', verbose_name=_('master user'))
    user_code = models.CharField(max_length=25, null=True, blank=True)
    name = models.CharField(max_length=255, verbose_name=_('name'))
    short_name = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('short name'))
    type = models.ForeignKey(AccountType, null=True, blank=True)
    # is_active = models.BooleanField(default=True)
    # is_cash_or_custody = models.BooleanField(default=False, verbose_name=_('Is Cash/Custody Account'))  # rename or ?
    # is_specify_account = models.BooleanField(default=False)
    # is_show_transaction_details = models.BooleanField(default=False)
    classifiers = TreeManyToManyField(AccountClassifier, blank=True)

    # notes = models.TextField(null=True, blank=True, default='', verbose_name=_('description'))

    class Meta:
        verbose_name = _('account')
        verbose_name_plural = _('accounts')
        unique_together = [
            ['master_user', 'user_code']
        ]

    def __str__(self):
        return '%s' % self.name
