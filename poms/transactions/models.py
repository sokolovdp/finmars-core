from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from mptt.models import MPTTModel

from poms.accounts.models import Account
from poms.counterparties.models import Responsible, Counterparty
from poms.currencies.models import Currency
from poms.instruments.models import Instrument
from poms.portfolios.models import Portfolio
from poms.strategies.models import Strategy
from poms.users.models import MasterUser


@python_2_unicode_compatible
class TransactionClass(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name=_('system code'))
    name = models.CharField(max_length=255, verbose_name=_('name'))
    description = models.TextField(null=True, blank=True, default='', verbose_name=_('description'))

    class Meta:
        verbose_name = _('transaction class')
        verbose_name_plural = _('transaction classes')

    def __str__(self):
        return '%s' % (self.name,)


# тип транзакции это псмотри на комплексные транзакции...

@python_2_unicode_compatible
class Transaction(models.Model):
    master_user = models.ForeignKey(MasterUser, related_name='transactions', verbose_name=_('master user'))
    portfolio = models.ForeignKey(Portfolio)
    transaction_class = models.ForeignKey(TransactionClass)
    # strategy = models.ManyToManyField(Strategy, blank=True)

    # Position related
    instrument = models.ForeignKey(Instrument)
    position_size_with_sign = models.FloatField(null=True, blank=True)

    # Cash related
    settlement_currency = models.ForeignKey(Currency)
    cash_consideration = models.FloatField(null=True, blank=True)

    # P&L related
    principal_with_sign = models.FloatField(null=True, blank=True)
    carry_with_sign = models.FloatField(null=True, blank=True)
    overheads_with_sign = models.FloatField(null=True, blank=True)

    # accounting dates
    accounting_date = models.DateField(default=timezone.now)
    cash_date = models.DateField(default=timezone.now)
    transaction_date = models.DateField(default=timezone.now, help_text=_("Min of accounting_date and cash_date"))
    account_cash = models.ForeignKey(Account, null=True, blank=True, related_name='transaction_caches')
    account_position = models.ForeignKey(Account, null=True, blank=True, related_name='account_positions')
    account_interim = models.ForeignKey(Account, null=True, blank=True, related_name='account_interims')

    reference_fx_rate = models.FloatField(null=True, blank=True, help_text=_(
        "FX rate to convert from Settlement ccy to Instrument Ccy on Accounting Date (trade date)"))

    # other
    is_locked = models.BooleanField(default=False)
    is_canceled = models.BooleanField(default=False)
    factor = models.FloatField(null=True, blank=True)
    trade_price = models.FloatField(null=True, blank=True)
    principal_amount = models.FloatField(null=True, blank=True)
    carry_amount = models.FloatField(null=True, blank=True)
    overheads = models.FloatField(null=True, blank=True)

    # information
    notes_front_office = models.TextField(null=True, blank=True)
    notes_middle_office = models.TextField(null=True, blank=True)
    responsible = models.ForeignKey(Responsible, null=True, blank=True, help_text=_("Trader or transaction executer"))
    responsible_text = models.CharField(max_length=50, null=True, blank=True,
                                        help_text=_("Text for non-frequent responsible"))
    counterparty = models.ForeignKey(Counterparty, null=True, blank=True)
    counterparty_text = models.CharField(max_length=50, null=True, blank=True)

    # classifiers = TreeManyToManyField(TransactionClassifier, blank=True)

    class Meta:
        verbose_name = _('transaction')
        verbose_name_plural = _('transactions')

    def __str__(self):
        return '%s' % self.id
