from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeForeignKey, TreeManyToManyField
from mptt.models import MPTTModel

from poms.accounts.models import Account
from poms.audit import history
from poms.common.models import NamedModel, TagModelBase
from poms.counterparties.models import Counterparty, Responsible
from poms.currencies.models import Currency
from poms.strategies.models import Strategy
from poms.users.models import MasterUser, AttrBase, AttrValueBase


@python_2_unicode_compatible
class PortfolioClassifier(NamedModel, MPTTModel):
    master_user = models.ForeignKey(MasterUser, related_name='portfolio_classifiers', verbose_name=_('master user'))
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)

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


class PortfolioTag(TagModelBase):
    master_user = models.ForeignKey(MasterUser, related_name='portfolio_tags', verbose_name=_('master user'))

    class Meta:
        verbose_name = _('portfolio tag')
        verbose_name_plural = _('portfolio tags')
        unique_together = [
            ['master_user', 'user_code'],
            ['master_user', 'name'],
        ]
        permissions = [
            ('view_portfoliotag', 'Can view portfolio tag')
        ]


@python_2_unicode_compatible
class Portfolio(NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='portfolios', verbose_name=_('master user'))
    # classifiers = TreeManyToManyField(PortfolioClassifier, blank=True)
    tags = models.ManyToManyField(PortfolioTag, blank=True)

    accounts = models.ManyToManyField(Account, blank=True, related_name='portfolios', verbose_name=_('accounts'))
    counterparties = models.ManyToManyField(Counterparty, blank=True, related_name='portfolios',
                                            verbose_name=_('counterparties'))
    responsibles = models.ManyToManyField(Responsible, blank=True, related_name='portfolios',
                                          verbose_name=_('responsibles'))

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


class PortfolioAttr(AttrBase):
    classifier_root = TreeForeignKey(PortfolioClassifier, null=True, blank=True)

    class Meta:
        pass


class PortfolioAttrValue(AttrValueBase):
    portfolio = models.ForeignKey(Portfolio)
    attr = models.ForeignKey(PortfolioAttr)
    classifier = TreeForeignKey(PortfolioClassifier, null=True, blank=True)

    class Meta:
        unique_together = [
            ['portfolio', 'attr']
        ]


history.register(PortfolioClassifier)
history.register(PortfolioTag)
history.register(Portfolio)
