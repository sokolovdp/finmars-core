from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from poms.accounts.models import Account
from poms.audit import history
from poms.common.models import NamedModel, TagModelBase, ClassModelBase
from poms.counterparties.models import Responsible, Counterparty
from poms.currencies.models import Currency
from poms.instruments.models import Instrument
from poms.obj_attrs.models import AttributeTypeBase, AttributeBase, AttributeTypeOptionBase
from poms.obj_perms.models import UserObjectPermissionBase, GroupObjectPermissionBase
from poms.portfolios.models import Portfolio
from poms.strategies.models import Strategy
from poms.users.models import MasterUser, Member


class TransactionClass(ClassModelBase):
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

    class Meta:
        verbose_name = _('transaction class')
        verbose_name_plural = _('transaction classes')


@python_2_unicode_compatible
class TransactionType(NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='transaction_types', verbose_name=_('master user'))

    instrument_types = models.ManyToManyField('instruments.InstrumentType', blank=True,
                                              related_name='transaction_types')

    class Meta:
        verbose_name = _('transaction type')
        verbose_name_plural = _('transaction types')
        unique_together = [
            ['master_user', 'user_code']
        ]
        permissions = [
            ('view_transactiontype', 'Can view transaction type')
        ]


class TransactionTypeUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(TransactionType, related_name='user_object_permissions')

    class Meta:
        verbose_name = _('transaction types - user permission')
        verbose_name_plural = _('transaction types - user permissions')


class TransactionTypeGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(TransactionType, related_name='group_object_permissions')

    class Meta:
        verbose_name = _('transaction types - group permission')
        verbose_name_plural = _('transaction types - group permissions')


# name - expr
# instr - content_type:instrument
# sccy - content_type:currency
# pos - number
# price - number
# acc - content_type:account
class TransactionTypeInput(models.Model):
    STRING = 10
    NUMBER = 20
    EXPRESSION = 30
    RELATION = 100
    # ACCOUNT = 110
    # INSTRUMENT = 120
    # CURRENCY = 130
    # COUNTERPARTY = 140
    # RESPONSIBLE = 150
    # STRATEGY = 150

    TYPES = (
        (NUMBER, _('Number')),
        (STRING, _('String')),
        (EXPRESSION, _('Expression')),
        (RELATION, _('Relation')),
        # (ACCOUNT, _('Account')),
        # (INSTRUMENT, _('Instrument')),
        # (CURRENCY, _('Currency')),
        # (COUNTERPARTY, _('Counterparty')),
        # (RESPONSIBLE, _('Responsible')),
        # (STRATEGY, _('Strategy')),
    )

    transaction_type = models.ForeignKey(TransactionType, related_name='inputs')
    value_type = models.PositiveSmallIntegerField(default=NUMBER, choices=TYPES)
    name = models.CharField(max_length=255, null=True, blank=True)
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    order = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class TransactionTypeItem(models.Model):
    transaction_type = models.ForeignKey(TransactionType, related_name='items')
    order = models.IntegerField(default=0)

    transaction_class = models.ForeignKey(TransactionClass, related_name='+')

    instrument = models.ForeignKey(Instrument, null=True, blank=True, related_name='+')
    transaction_currency = models.ForeignKey(Currency, null=True, blank=True, related_name='+')
    position_size_with_sign = models.FloatField(null=True, blank=True)
    settlement_currency = models.ForeignKey(Currency, null=True, blank=True, related_name='+')
    cash_consideration = models.FloatField(null=True, blank=True)
    account_position = models.ForeignKey(Account, null=True, blank=True, related_name='+')
    account_cash = models.ForeignKey(Account, null=True, blank=True, related_name='+')
    account_interim = models.ForeignKey(Account, null=True, blank=True, related_name='+')

    instrument_input = models.ForeignKey(TransactionTypeInput, null=True, blank=True, related_name='+')
    transaction_currency_input = models.ForeignKey(TransactionTypeInput, null=True, blank=True, related_name='+')
    position_size_with_sign_expr = models.CharField(max_length=255, blank=True)
    settlement_currency_input = models.ForeignKey(TransactionTypeInput, null=True, blank=True, related_name='+')
    cash_consideration_expr = models.CharField(max_length=255, blank=True)
    account_position_input = models.ForeignKey(TransactionTypeInput, null=True, blank=True, related_name='+')
    account_cash_input = models.ForeignKey(TransactionTypeInput, null=True, blank=True, related_name='+')
    account_interim_input = models.ForeignKey(TransactionTypeInput, null=True, blank=True, related_name='+')

    # instrument_expr = models.CharField(max_length=255, blank=True)
    # transaction_currency_expr = models.CharField(max_length=255, blank=True)
    # position_size_with_sign_expr = models.CharField(max_length=255, blank=True)
    # settlement_currency_expr = models.CharField(max_length=255, blank=True)
    # cash_consideration_expr = models.CharField(max_length=255, blank=True)
    # account_position_expr = models.CharField(max_length=255, blank=True)
    # account_cash_expr = models.CharField(max_length=255, blank=True)
    # account_interim_expr = models.CharField(max_length=255, blank=True)


# # instrument = instr
# # position_size_with_sign = pos
# # settlement_currency = sccy
# # cash_consideration = pos * price
# # account_position = acc
# # account_cash = acc
# # account_interim = acc
# class TransactionTypeItemValue(models.Model):
#     # NAMES = (
#     #     ('instrument', 'instrument'),
#     #     ('transaction_currency', 'transaction_currency'),
#     #     ('position_size_with_sign', 'position_size_with_sign'),
#     #     ('settlement_currency', 'settlement_currency'),
#     #     ('cash_consideration', 'cash_consideration'),
#     #     ('account_position', 'account_position'),
#     #     ('account_cash', 'account_cash'),
#     #     ('account_interim', 'account_interim'),
#     # )
#     item = models.ForeignKey(TransactionTypeItem)
#     name = models.CharField(max_length=255, help_text="transaction basic attribute name or any dynamic attribute")
#     expr = models.CharField(max_length=255, null=True, blank=True)


# class EventType(NamedModel):
#     SECONDS = 1
#     DAYS = 2
#     INTERVALS = (
#         (SECONDS, 'Seconds'),
#         (DAYS, 'Days'),
#     )
#     transaction_type = models.ForeignKey(TransactionType)
#     interval = models.PositiveIntegerField(default=DAYS, choices=INTERVALS)
#     duration = models.PositiveIntegerField(default=1)
#
#
# @python_2_unicode_compatible
# class ComplexTransaction(NamedModel):
#     master_user = models.ForeignKey(MasterUser, related_name='complex_transactions', verbose_name=_('master user'))
#     type = models.ForeignKey(TransactionType)
#
#     class Meta:
#         verbose_name = _('complex transaction')
#         verbose_name_plural = _('complex transactions')
#         unique_together = [
#             ['master_user', 'user_code']
#         ]
#
#
# @python_2_unicode_compatible
# class ComplexTransactionItem(models.Model):
#     complex_transaction = models.ForeignKey(ComplexTransaction)
#     order = models.PositiveIntegerField(default=0)
#
#     transaction = models.OneToOneField('Transaction', null=True, blank=True)
#     event_type = models.ForeignKey(EventType, null=True, blank=True)
#
#     trigger_date = models.DateTimeField(default=timezone.now)
#     trigger_count = models.PositiveIntegerField(default=0)
#
#     class Meta:
#         verbose_name = _('item')
#         verbose_name_plural = _('items')
#
#     def __str__(self):
#         return 'Item %s#%s' % (self.complex_transaction, self.pk)


@python_2_unicode_compatible
class Transaction(models.Model):
    master_user = models.ForeignKey(MasterUser, related_name='transactions', verbose_name=_('master user'))
    transaction_class = models.ForeignKey(TransactionClass, verbose_name="class")

    portfolio = models.ForeignKey(Portfolio, verbose_name="portfolio")

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
                                          help_text=_('Notes front office'))
    notes_middle_office = models.TextField(null=True, blank=True,
                                           help_text=_('Notes middle office'))
    responsible = models.ForeignKey(Responsible, null=True, blank=True,
                                    help_text=_("Trader or transaction executer"))
    responsible_text = models.CharField(max_length=50, null=True, blank=True,
                                        help_text=_("Text for non-frequent responsible"))
    counterparty = models.ForeignKey(Counterparty, null=True, blank=True,
                                     help_text=_('Transaction counterparty'))
    counterparty_text = models.CharField(max_length=50, null=True, blank=True,
                                         help_text=_('Text for non-frequent counterparty'))

    # strategy_position = TreeForeignKey(Strategy, null=True, blank=True, related_name='+',
    #                                    verbose_name='temporary strategy position')
    # strategy_cash = TreeForeignKey(Strategy, null=True, blank=True, related_name='+',
    #                                verbose_name='temporary strategy cash')

    class Meta:
        verbose_name = _('transaction')
        verbose_name_plural = _('transactions')
        permissions = [
            ('view_transaction', 'Can view transaction')
        ]

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

    # @property
    # def strategies_position(self):
    #     return [self.strategy_position] if self.strategy_position_id else []

    # @property
    # def strategies_cash(self):
    #     return [self.strategy_cash] if self.strategy_cash_id else []


class TransactionAttributeType(AttributeTypeBase):
    strategy_position_root = models.ForeignKey(Strategy, null=True, blank=True, related_name='+')
    strategy_cash_root = models.ForeignKey(Strategy, null=True, blank=True, related_name='+')

    class Meta:
        verbose_name = _('transaction attribute type')
        verbose_name_plural = _('transaction attribute types')


class TransactionAttributeTypeOption(AttributeTypeOptionBase):
    member = models.ForeignKey(Member, related_name='transaction_attribute_type_options')
    attribute_type = models.ForeignKey(TransactionAttributeType, related_name='attribute_type_options')

    class Meta:
        verbose_name = _('transaction attribute types - option')
        verbose_name_plural = _('transaction attribute types - options')


class TransactionAttributeTypeUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(TransactionAttributeType, related_name='user_object_permissions')

    class Meta:
        verbose_name = _('transaction attribute types - user permission')
        verbose_name_plural = _('transaction attribute types - user permissions')


class TransactionAttributeTypeGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(TransactionAttributeType, related_name='group_object_permissions')

    class Meta:
        verbose_name = _('transaction attribute types - group permission')
        verbose_name_plural = _('transaction attribute types - group permissions')


class TransactionAttribute(AttributeBase):
    attribute_type = models.ForeignKey(TransactionAttributeType, related_name='attributes')
    content_object = models.ForeignKey(Transaction)
    strategy_position = models.ForeignKey(Strategy, null=True, blank=True, related_name='+')
    strategy_cash = models.ForeignKey(Strategy, null=True, blank=True, related_name='+')

    class Meta:
        verbose_name = _('transaction attribute')
        verbose_name_plural = _('transaction attributes')


history.register(TransactionClass)
history.register(TransactionType)
history.register(Transaction)
