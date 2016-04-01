from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeForeignKey, TreeManyToManyField
from mptt.models import MPTTModel

from poms.accounts.models import Account
from poms.audit import history
from poms.currencies.models import Currency
from poms.strategies.models import Strategy
from poms.users.models import MasterUser


@python_2_unicode_compatible
class PortfolioClassifier(MPTTModel):
    master_user = models.ForeignKey(MasterUser, related_name='portfolio_classifiers', verbose_name=_('master user'))
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)
    user_code = models.CharField(max_length=25, null=True, blank=True)
    name = models.CharField(max_length=255, verbose_name=_('name'))
    short_name = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('short name'))
    notes = models.TextField(null=True, blank=True)

    class MPTTMeta:
        order_insertion_by = ['master_user', 'name']

    class Meta:
        verbose_name = _('portfolio classifier')
        verbose_name_plural = _('portfolio classifiers')
        permissions = [
            ('view_portfolioclassifier', 'Can view portfolio classifier')
        ]

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Portfolio(models.Model):
    master_user = models.ForeignKey(MasterUser, related_name='portfolios', verbose_name=_('master user'))
    user_code = models.CharField(max_length=25, null=True, blank=True)
    name = models.CharField(max_length=255, verbose_name=_('name'))
    short_name = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('short name'))
    notes = models.TextField(null=True, blank=True)
    classifiers = TreeManyToManyField(PortfolioClassifier, blank=True)

    # inception_date = models.DateField(null=True, blank=True)
    # accounts = models.ManyToManyField(Account, blank=True, verbose_name=_('accounts'))
    # strategies = models.ManyToManyField(Strategy, blank=True, verbose_name=_('strategies'))
    # notes = models.TextField(null=True, blank=True, default='', verbose_name=_('description'))

    class Meta:
        verbose_name = _('portfolio')
        verbose_name_plural = _('portfolios')
        unique_together = [
            ['master_user', 'user_code']
        ]
        permissions = [
            ('view_portfolio', 'Can view portfolio')
        ]

    def __str__(self):
        return self.name


history.register(PortfolioClassifier)
history.register(Portfolio)
