from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from mptt.models import MPTTModel
from reversion import revisions as reversion

from poms.accounts.models import Account
from poms.counterparties.models import Responsible, Counterparty
from poms.currencies.models import Currency
from poms.instruments.models import Instrument
from poms.portfolios.models import Portfolio
from poms.strategies.models import Strategy
from poms.users.models import MasterUser


@python_2_unicode_compatible
class TransactionClass(models.Model):
    # BUY = "Buy"  # 1
    # CASH_INFLOW = "Cash-Inflow"  # 8
    # CASH_OUTFLOW = "Cash-Outflow"  # 9
    # FX_TRADE = "FX Trade"  # 3
    # FX_TRANSFER = "FX Transfer"  # 7
    # INSTRUMENT_PL = "Instrument PL"  # 4
    # SELL = "Sell"  # 2
    # TRANSACTION_PL = "Transaction PL"  # 5
    # TRANSFER = "Transfer"  # 6

    BUY = 1
    SELL = 2
    FX_TRADE = 3
    INSTRUMENT_PL = 4
    TRANSACTION_PL = 5
    TRANSFER = 6
    FX_TRANSFER = 7
    CASH_INFLOW = 8
    CASH_OUTFLOW = 9

    CLASSES = (
        (BUY, "Buy"),
        (SELL, "Sell"),
        (FX_TRADE, "FX Trade"),
        (INSTRUMENT_PL, "Instrument PL"),
        (TRANSACTION_PL, "Transaction PL"),
        (TRANSFER, "Transfer"),
        (FX_TRANSFER, "FX Transfer"),
        (CASH_INFLOW, "Cash-Inflow"),
        (CASH_OUTFLOW, "Cash-Outflow"),
    )

    id = models.PositiveSmallIntegerField(primary_key=1)
    system_code = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('system code'))
    name = models.CharField(max_length=255, verbose_name=_('name'))
    description = models.TextField(null=True, blank=True, default='', verbose_name=_('description'))

    class Meta:
        verbose_name = _('transaction class')
        verbose_name_plural = _('transaction classes')

    def __str__(self):
        return '%s' % (self.name,)


@python_2_unicode_compatible
class Transaction(models.Model):
    master_user = models.ForeignKey(MasterUser, related_name='transactions', verbose_name=_('master user'))
    portfolio = models.ForeignKey(Portfolio)
    transaction_class = models.ForeignKey(TransactionClass)
    # strategy = models.ManyToManyField(Strategy, blank=True)

    # Position related
    instrument = models.ForeignKey(Instrument, null=True, blank=True)
    transaction_currency = models.ForeignKey(Currency, null=True, blank=True, related_name='transactions_as_instrument')
    position_size_with_sign = models.FloatField(null=True, blank=True)

    # Cash related
    settlement_currency = models.ForeignKey(Currency, related_name='transactions')
    cash_consideration = models.FloatField(null=True, blank=True)

    # P&L related
    principal_with_sign = models.FloatField(null=True, blank=True)
    carry_with_sign = models.FloatField(null=True, blank=True)
    overheads_with_sign = models.FloatField(null=True, blank=True)

    # accounting dates
    transaction_date = models.DateField(editable=False, default=timezone.now,
                                        help_text=_("Min of accounting_date and cash_date"))
    accounting_date = models.DateField(default=timezone.now)
    cash_date = models.DateField(default=timezone.now)

    account_position = models.ForeignKey(Account, null=True, blank=True, related_name='account_positions')
    account_cash = models.ForeignKey(Account, null=True, blank=True, related_name='transaction_cashs')
    account_interim = models.ForeignKey(Account, null=True, blank=True, related_name='account_interims')

    reference_fx_rate = models.FloatField(null=True, blank=True,
                                          help_text=_("FX rate to convert from Settlement ccy to Instrument "
                                                      "Ccy on Accounting Date (trade date)"))

    # other
    is_locked = models.BooleanField(default=False,
                                    help_text=_('If checked - transaction cannot be changed'))
    is_canceled = models.BooleanField(default=False,
                                      help_text=_('If checked - transaction is cancelled'))
    factor = models.FloatField(null=True, blank=True,
                               help_text=_('Multiplier (for calculations on the form)'))
    trade_price = models.FloatField(null=True, blank=True,
                                    help_text=_('Price (for calculations on the form)'))
    principal_amount = models.FloatField(null=True, blank=True,
                                         help_text=_(
                                             'Absolute value of Principal with Sign (for calculations on the form)'))
    carry_amount = models.FloatField(null=True, blank=True,
                                     help_text=_('Absolute value of Carry with Sign (for calculations on the form)'))
    overheads = models.FloatField(null=True, blank=True,
                                  help_text=_('Absolute value of Carry with Sign (for calculations on the form)'))

    # information
    notes_front_office = models.TextField(null=True, blank=True,
                                          help_text=_('text'))
    notes_middle_office = models.TextField(null=True, blank=True,
                                           help_text=_('text'))
    responsible = models.ForeignKey(Responsible, null=True, blank=True,
                                    help_text=_("Trader or transaction executer"))
    responsible_text = models.CharField(max_length=50, null=True, blank=True,
                                        help_text=_("Text for non-frequent responsible"))
    counterparty = models.ForeignKey(Counterparty, null=True, blank=True,
                                     help_text=_('Transaction Counterparty'))
    counterparty_text = models.CharField(max_length=50, null=True, blank=True,
                                         help_text=_('Text for non-frequent Counterparty'))

    # classifiers = TreeManyToManyField(TransactionClassifier, blank=True)

    class Meta:
        verbose_name = _('transaction')
        verbose_name_plural = _('transactions')

    def __str__(self):
        return '%s #%s' % (self.master_user, self.id)

        # @property
        # def cash_flow(self):
        #     return self.principal_with_sign + self.carry_with_sign + self.overheads_with_sign

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.transaction_date = min(self.accounting_date, self.cash_date)
        if update_fields is not None:
            if isinstance(update_fields, tuple):
                update_fields = update_fields + ('transaction_date',)
            if isinstance(update_fields, list):
                update_fields = update_fields + ['transaction_date', ]
        super(Transaction, self).save(force_insert=force_insert, force_update=force_update, using=using,
                                      update_fields=update_fields)


reversion.register(TransactionClass)
reversion.register(Transaction)
