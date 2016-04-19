from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
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


class ActionClass(ClassModelBase):
    CREATE_INSTRUMENT = 1
    CREATE_INSTRUMENT_PARAMETER = 2

    CLASSES = (
        (CREATE_INSTRUMENT, "Create instrument"),
        (CREATE_INSTRUMENT_PARAMETER, "Create instrument parameter"),
    )

    class Meta:
        verbose_name = _('action class')
        verbose_name_plural = _('action classes')


class EventClass(ClassModelBase):
    CLASSES = tuple()

    class Meta:
        verbose_name = _('event class')
        verbose_name_plural = _('event classes')


class NotificationClass(ClassModelBase):
    CLASSES = tuple()

    class Meta:
        verbose_name = _('notification class')
        verbose_name_plural = _('notification classes')


class PeriodicityGroup(ClassModelBase):
    DAILY = 1
    WEEKLY = 2
    WEEKLY_EOW = 3
    BE_WEEKLY = 4
    BE_WEEKLY_EOW = 5
    MONTHLY = 6
    MONTHLY_EOM = 7
    QUARTERLY = 8
    QUARTERLY_CALENDAR = 9
    SEMI_ANUALLY = 10
    SEMI_ANUALLY_CALENDAR = 11
    ANUALLY = 12
    ANUALLY_CALENDAR = 13
    CLASSES = (
        (DAILY, "daily"),
        (WEEKLY, "weekly (+7d)"),
        (WEEKLY_EOW, "weekly (eow)"),
        (BE_WEEKLY, "bi-weekly (+14d)"),
        (BE_WEEKLY_EOW, "bi-weekly (eow)"),
        (MONTHLY, "monthly (+1m)"),
        (MONTHLY_EOM, "monthly (eom)"),
        (QUARTERLY, "quarterly (+3m)"),
        (QUARTERLY_CALENDAR, "quarterly (calendar)"),
        (SEMI_ANUALLY, "semi-anually (+6m)"),
        (SEMI_ANUALLY_CALENDAR, "semi-anually (calendar)"),
        (ANUALLY, "anually (+12m)"),
        (ANUALLY_CALENDAR, "anually (eoy)"),
    )

    class Meta:
        verbose_name = _('periodicity group')
        verbose_name_plural = _('periodicity group')


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
@python_2_unicode_compatible
class TransactionTypeInput(models.Model):
    STRING = 10
    NUMBER = 20
    EXPRESSION = 30
    DATE = 40
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
        (DATE, _('Date')),
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


@python_2_unicode_compatible
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
    accounting_date = models.DateField(null=True, blank=True)
    cash_date = models.DateField(null=True, blank=True)

    instrument_input = models.ForeignKey(TransactionTypeInput, null=True, blank=True, related_name='+')
    transaction_currency_input = models.ForeignKey(TransactionTypeInput, null=True, blank=True, related_name='+')
    position_size_with_sign_expr = models.CharField(max_length=255, blank=True, default='')
    settlement_currency_input = models.ForeignKey(TransactionTypeInput, null=True, blank=True, related_name='+')
    cash_consideration_expr = models.CharField(max_length=255, blank=True, default='')
    account_position_input = models.ForeignKey(TransactionTypeInput, null=True, blank=True, related_name='+')
    account_cash_input = models.ForeignKey(TransactionTypeInput, null=True, blank=True, related_name='+')
    account_interim_input = models.ForeignKey(TransactionTypeInput, null=True, blank=True, related_name='+')
    accounting_date_expr = models.CharField(max_length=255, blank=True, default='')
    cash_date_expr = models.CharField(max_length=255, blank=True, default='')

    # instrument_expr = models.CharField(max_length=255, blank=True)
    # transaction_currency_expr = models.CharField(max_length=255, blank=True)
    # position_size_with_sign_expr = models.CharField(max_length=255, blank=True)
    # settlement_currency_expr = models.CharField(max_length=255, blank=True)
    # cash_consideration_expr = models.CharField(max_length=255, blank=True)
    # account_position_expr = models.CharField(max_length=255, blank=True)
    # account_cash_expr = models.CharField(max_length=255, blank=True)
    # account_interim_expr = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return 'item #%s' % self.id


class EventToHandle(NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='events_to_handle')
    transaction_type = models.ForeignKey(TransactionType)
    notification_date = models.DateField(null=True, blank=True)
    effective_date = models.DateField(null=True, blank=True)


@python_2_unicode_compatible
class Transaction(models.Model):
    master_user = models.ForeignKey(MasterUser, related_name='transactions', verbose_name=_('master user'))
    transaction_code = models.IntegerField(default=0)
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
    # notes_front_office = models.TextField(null=True, blank=True,
    #                                       help_text=_('Notes front office'))
    # notes_middle_office = models.TextField(null=True, blank=True,
    #                                        help_text=_('Notes middle office'))
    responsible = models.ForeignKey(Responsible, null=True, blank=True,
                                    help_text=_("Trader or transaction executer"))
    # responsible_text = models.CharField(max_length=50, null=True, blank=True,
    #                                     help_text=_("Text for non-frequent responsible"))
    counterparty = models.ForeignKey(Counterparty, null=True, blank=True,
                                     help_text=_('Transaction counterparty'))
    # counterparty_text = models.CharField(max_length=50, null=True, blank=True,
    #                                      help_text=_('Text for non-frequent counterparty'))

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

    class Meta(AttributeBase.Meta):
        verbose_name = _('transaction attribute')
        verbose_name_plural = _('transaction attributes')

    def get_value(self):
        t = self.attribute_type.value_type
        if t == AttributeTypeBase.CLASSIFIER:
            return self.strategy_position, self.strategy_position
        else:
            return super(TransactionAttribute, self).get_value()

    def set_value(self, value):
        t = self.attribute_type.value_type
        if t == AttributeTypeBase.CLASSIFIER:
            self.strategy_position, self.strategy_position = value
        else:
            super(TransactionAttribute, self).set_value(value)


@python_2_unicode_compatible
class ExternalCashFlow(models.Model):
    date = models.DateField(default=timezone.now)
    portfolio = models.ForeignKey(Portfolio)
    account = models.ForeignKey(Account)
    currency = models.ForeignKey(Currency)
    amount = models.FloatField(default=0.)

    def __str__(self):
        return '%s: %s - %s - %s - %s = %s' % (self.date, self.portfolio, self.account, list(self.strategies.all()),
                                               self.currency, self.amount)


@python_2_unicode_compatible
class ExternalCashFlowStrategy(models.Model):
    external_cash_flow = models.ForeignKey(ExternalCashFlow, related_name='strategies')
    order = models.IntegerField(default=0)
    strategy = models.ForeignKey(Strategy)

    class Meta:
        ordering = ['external_cash_flow', 'order']

    def __str__(self):
        return '%s' % self.strategy


history.register(TransactionClass)
history.register(TransactionType)
history.register(Transaction)
