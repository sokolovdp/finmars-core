from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeManyToManyField

from poms.accounts.models import Account
from poms.audit import history
from poms.common.models import TagModelBase
from poms.counterparties.models import Responsible, Counterparty
from poms.currencies.models import Currency
from poms.instruments.models import Instrument, InstrumentType
from poms.portfolios.models import Portfolio
from poms.strategies.models import Strategy
from poms.transactions.models import TransactionType
from poms.users.models import MasterUser


class AccountTag(TagModelBase):
    master_user = models.ForeignKey(MasterUser, related_name='account_tags', verbose_name=_('master user'))
    accounts = models.ManyToManyField(Account, blank=True, related_name='tags')

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


class CurrencyTag(TagModelBase):
    master_user = models.ForeignKey(MasterUser, related_name='currency_tags', verbose_name=_('master user'))
    currencies = models.ManyToManyField(Currency, blank=True, related_name='tags')

    class Meta:
        verbose_name = _('currency tag')
        verbose_name_plural = _('currency tags')
        unique_together = [
            ['master_user', 'user_code'],
            ['master_user', 'name'],
        ]
        permissions = [
            ('view_currencytag', 'Can view currency tag')
        ]


class InstrumentTypeTag(TagModelBase):
    master_user = models.ForeignKey(MasterUser, related_name='instrumenttype_tags', verbose_name=_('master user'))
    instrument_types = models.ManyToManyField(InstrumentType, blank=True, related_name='tags')

    class Meta:
        verbose_name = _('instrument type tag')
        verbose_name_plural = _('instrument type tags')
        unique_together = [
            ['master_user', 'user_code'],
            ['master_user', 'name'],
        ]
        permissions = [
            ('view_instrumenttypetag', 'Can view instrument type tag')
        ]


class InstrumentTag(TagModelBase):
    master_user = models.ForeignKey(MasterUser, related_name='instrument_tags', verbose_name=_('master user'))
    instruments = models.ManyToManyField(Instrument, blank=True, related_name='tags')

    class Meta:
        verbose_name = _('instrument tag')
        verbose_name_plural = _('instrument tags')
        unique_together = [
            ['master_user', 'user_code'],
            ['master_user', 'name'],
        ]
        permissions = [
            ('view_instrumenttag', 'Can view instrument tag')
        ]


class CounterpartyTag(TagModelBase):
    master_user = models.ForeignKey(MasterUser, related_name='counterparty_tags', verbose_name=_('master user'))
    counterparties = models.ManyToManyField(Counterparty, blank=True, related_name='tags')

    class Meta:
        verbose_name = _('counterparty tag')
        verbose_name_plural = _('counterparty tags')
        unique_together = [
            ['master_user', 'user_code'],
            ['master_user', 'name'],
        ]
        permissions = [
            ('view_counterpartytag', 'Can view counterparty tag')
        ]


class ResponsibleTag(TagModelBase):
    master_user = models.ForeignKey(MasterUser, related_name='responsible_tags', verbose_name=_('master user'))
    responsibles = models.ManyToManyField(Responsible, blank=True, related_name='tags')

    class Meta:
        verbose_name = _('responsible tag')
        verbose_name_plural = _('responsible tags')
        unique_together = [
            ['master_user', 'user_code'],
            ['master_user', 'name'],
        ]
        permissions = [
            ('view_responsibletag', 'Can view responsible tag')
        ]


class PortfolioTag(TagModelBase):
    master_user = models.ForeignKey(MasterUser, related_name='portfolio_tags', verbose_name=_('master user'))
    portfolios = models.ManyToManyField(Portfolio, blank=True, related_name='tags')

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


class StrategyTag(TagModelBase):
    master_user = models.ForeignKey(MasterUser, related_name='strategy_tags', verbose_name=_('master user'))
    strategies = TreeManyToManyField(Strategy, blank=True, related_name='tags')

    class Meta:
        verbose_name = _('strategy tag')
        verbose_name_plural = _('strategy tags')
        unique_together = [
            ['master_user', 'user_code'],
            ['master_user', 'name'],
        ]
        permissions = [
            ('view_strategytag', 'Can view strategy tag')
        ]


class TransactionTypeTag(TagModelBase):
    master_user = models.ForeignKey(MasterUser, related_name='transactiontype_tags', verbose_name=_('master user'))
    transaction_types = models.ManyToManyField(TransactionType, blank=True, related_name='tags')

    class Meta:
        verbose_name = _('transaction type tag')
        verbose_name_plural = _('transaction type tags')
        unique_together = [
            ['master_user', 'user_code'],
            ['master_user', 'name'],
        ]
        permissions = [
            ('view_transactiontypetag', 'Can view instrument type tag')
        ]


class CommonTag(TagModelBase):
    master_user = models.ForeignKey(MasterUser, related_name='common_tags', verbose_name=_('master user'))

    accounts = models.ManyToManyField(Account, blank=True, related_name='common_tags')
    currencies = models.ManyToManyField(Currency, blank=True, related_name='common_tags')
    instrument_types = models.ManyToManyField(InstrumentType, blank=True, related_name='common_tags')
    instruments = models.ManyToManyField(Instrument, blank=True, related_name='common_tags')
    counterparties = models.ManyToManyField(Counterparty, blank=True, related_name='common_tags')
    responsibles = models.ManyToManyField(Responsible, blank=True, related_name='common_tags')
    strategies = TreeManyToManyField(Strategy, blank=True, related_name='common_tags')
    portfolios = models.ManyToManyField(Portfolio, blank=True, related_name='common_tags')
    transaction_types = models.ManyToManyField(TransactionType, blank=True, related_name='common_tags')


history.register(AccountTag)
history.register(CurrencyTag)
history.register(InstrumentTypeTag)
history.register(InstrumentTag)
history.register(CounterpartyTag)
history.register(ResponsibleTag)
history.register(StrategyTag)
history.register(PortfolioTag)
history.register(TransactionTypeTag)
history.register(CommonTag)
