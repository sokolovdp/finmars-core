from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from poms.accounts.models import Account
from poms.audit import history
from poms.common.models import NamedModel, TagModelBase, ClassModelBase
from poms.counterparties.models import Responsible, Counterparty
from poms.currencies.models import Currency
from poms.instruments.models import Instrument
from poms.obj_attrs.models import AttributeTypeBase, AttributeBase, AttributeTypeOptionBase
from poms.obj_perms.models import GroupObjectPermissionBase, UserObjectPermissionBase
from poms.portfolios.models import Portfolio
from poms.strategies.models import Strategy1, Strategy2, Strategy3
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

    class Meta(ClassModelBase.Meta):
        verbose_name = _('transaction class')
        verbose_name_plural = _('transaction classes')


class ActionClass(ClassModelBase):
    CREATE_INSTRUMENT = 1
    CREATE_INSTRUMENT_PARAMETER = 2

    CLASSES = (
        (CREATE_INSTRUMENT, "Create instrument"),
        (CREATE_INSTRUMENT_PARAMETER, "Create instrument parameter"),
    )

    class Meta(ClassModelBase.Meta):
        verbose_name = _('action class')
        verbose_name_plural = _('action classes')


class EventClass(ClassModelBase):
    CLASSES = tuple()

    class Meta(ClassModelBase.Meta):
        verbose_name = _('event class')
        verbose_name_plural = _('event classes')


class NotificationClass(ClassModelBase):
    CLASSES = tuple()

    class Meta(ClassModelBase.Meta):
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

    class Meta(ClassModelBase.Meta):
        verbose_name = _('periodicity group')
        verbose_name_plural = _('periodicity group')


class TransactionType(NamedModel):
    master_user = models.ForeignKey(
        MasterUser,
        related_name='transaction_types',
        verbose_name=_('master user')
    )
    display_expr = models.CharField(
        max_length=255,
        blank=True,
        default='',
    )
    instrument_types = models.ManyToManyField(
        'instruments.InstrumentType',
        related_name='transaction_types',
        blank=True,
        verbose_name=_('instrument types')
    )

    class Meta(NamedModel.Meta):
        verbose_name = _('transaction type')
        verbose_name_plural = _('transaction types')
        unique_together = [
            ['master_user', 'user_code']
        ]
        permissions = [
            ('view_transactiontype', 'Can view transaction type')
        ]


class TransactionTypeUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(TransactionType, related_name='user_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(UserObjectPermissionBase.Meta):
        verbose_name = _('transaction types - user permission')
        verbose_name_plural = _('transaction types - user permissions')


class TransactionTypeGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(TransactionType, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(GroupObjectPermissionBase.Meta):
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
    # EXPRESSION = 30
    DATE = 40
    RELATION = 100

    # ACCOUNT = 110
    # INSTRUMENT = 120
    # CURRENCY = 130
    # COUNTERPARTY = 140
    # RESPONSIBLE = 150
    # STRATEGY1 = 161
    # STRATEGY2 = 162
    # STRATEGY3 = 163
    # DAILY_PRICING_MODEL = 170
    # PAYMENT_SIZE_DETAIL = 180
    # INSTRUMENT_TYPE = 190

    TYPES = (
        (NUMBER, _('Number')),
        (STRING, _('String')),
        (DATE, _('Date')),
        # (EXPRESSION, _('Expression')),
        (RELATION, _('Relation')),
        # (ACCOUNT, _('Account')),
        # (INSTRUMENT, _('Instrument')),
        # (CURRENCY, _('Currency')),
        # (COUNTERPARTY, _('Counterparty')),
        # (RESPONSIBLE, _('Responsible')),
        # (STRATEGY1, _('Strategy 1')),
        # (STRATEGY2, _('Strategy 2')),
        # (STRATEGY3, _('Strategy 3')),
        # (DAILY_PRICING_MODEL, _('Daily pricing model')),
        # (PAYMENT_SIZE_DETAIL, _('Payment size detail')),
        # (INSTRUMENT_TYPE, _('Instrument type'))
    )

    transaction_type = models.ForeignKey(
        TransactionType,
        related_name='inputs'
    )
    name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    verbose_name = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    value_type = models.PositiveSmallIntegerField(
        default=NUMBER,
        choices=TYPES,
        verbose_name=_('value type')
    )
    content_type = models.ForeignKey(
        ContentType,
        null=True,
        blank=True,
        verbose_name=_('content type')
    )
    order = models.IntegerField(
        default=0,
        verbose_name=_('order')
    )

    class Meta:
        verbose_name = _('transaction type input')
        verbose_name_plural = _('transaction type inputs')
        unique_together = [
            ['transaction_type', 'name'],
            ['transaction_type', 'order'],
        ]
        ordering = ['transaction_type', 'order']

    def __str__(self):
        return '%s: %s' % (self.name, self.get_value_type_display())

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.verbose_name:
            self.verbose_name = self.name
        super(TransactionTypeInput, self).save(force_insert=force_insert, force_update=force_update, using=using,
                                         update_fields=update_fields)


# @python_2_unicode_compatible
# class TransactionTypeItem(models.Model):
#     transaction_type = models.ForeignKey(TransactionType, related_name='items', on_delete=models.PROTECT)
#     order = models.IntegerField(default=0)
#
#     transaction_class = models.ForeignKey(TransactionClass, related_name='+', on_delete=models.PROTECT)
#
#     instrument = models.ForeignKey(Instrument, related_name='+', on_delete=models.PROTECT, null=True, blank=True)
#     transaction_currency = models.ForeignKey(Currency, related_name='+', on_delete=models.PROTECT, null=True,
#                                              blank=True)
#     position_size_with_sign = models.FloatField(null=True, blank=True)
#     settlement_currency = models.ForeignKey(Currency, related_name='+', on_delete=models.PROTECT, null=True, blank=True)
#     cash_consideration = models.FloatField(null=True, blank=True)
#     account_position = models.ForeignKey(Account, related_name='+', on_delete=models.PROTECT, null=True, blank=True)
#     account_cash = models.ForeignKey(Account, related_name='+', on_delete=models.PROTECT, null=True, blank=True)
#     account_interim = models.ForeignKey(Account, related_name='+', on_delete=models.PROTECT, blank=True, null=True)
#     accounting_date = models.DateField(null=True, blank=True)
#     cash_date = models.DateField(null=True, blank=True)
#
#     strategy1_position = models.ForeignKey(
#         Strategy1,
#         null=True,
#         blank=True,
#         related_name='+',
#         on_delete=models.PROTECT
#     )
#     strategy1_cash = models.ForeignKey(
#         Strategy1,
#         null=True,
#         blank=True,
#         related_name='+',
#         on_delete=models.PROTECT
#     )
#     strategy2_position = models.ForeignKey(
#         Strategy2,
#         null=True,
#         blank=True,
#         related_name='+',
#         on_delete=models.PROTECT
#     )
#     strategy2_cash = models.ForeignKey(
#         Strategy2,
#         null=True,
#         blank=True,
#         related_name='+',
#         on_delete=models.PROTECT
#     )
#     strategy3_position = models.ForeignKey(
#         Strategy3,
#         null=True,
#         blank=True,
#         related_name='+',
#         on_delete=models.PROTECT
#     )
#     strategy3_cash = models.ForeignKey(
#         Strategy3,
#         null=True,
#         blank=True,
#         on_delete=models.PROTECT,
#         related_name='+'
#     )
#
#     instrument_input = models.ForeignKey(TransactionTypeInput, related_name='+', on_delete=models.PROTECT, null=True,
#                                          blank=True)
#     transaction_currency_input = models.ForeignKey(TransactionTypeInput, related_name='+', on_delete=models.PROTECT,
#                                                    null=True, blank=True)
#
#     position_size_with_sign_expr = models.CharField(max_length=255, blank=True, default='')
#     settlement_currency_input = models.ForeignKey(TransactionTypeInput, related_name='+', on_delete=models.PROTECT,
#                                                   null=True, blank=True)
#     cash_consideration_expr = models.CharField(max_length=255, blank=True, default='')
#
#     account_position_input = models.ForeignKey(TransactionTypeInput, related_name='+', on_delete=models.PROTECT,
#                                                null=True, blank=True)
#     account_cash_input = models.ForeignKey(TransactionTypeInput, related_name='+', on_delete=models.PROTECT, null=True,
#                                            blank=True)
#     account_interim_input = models.ForeignKey(TransactionTypeInput, related_name='+', on_delete=models.PROTECT,
#                                               null=True, blank=True)
#     strategy1_position_input = models.ForeignKey(TransactionTypeInput, related_name='+', on_delete=models.PROTECT,
#                                                  null=True, blank=True)
#     strategy1_cash_input = models.ForeignKey(TransactionTypeInput, related_name='+', on_delete=models.PROTECT,
#                                              null=True, blank=True)
#     strategy2_position_input = models.ForeignKey(TransactionTypeInput, related_name='+', on_delete=models.PROTECT,
#                                                  null=True, blank=True)
#     strategy2_cash_input = models.ForeignKey(TransactionTypeInput, related_name='+', on_delete=models.PROTECT,
#                                              null=True, blank=True)
#     strategy3_position_input = models.ForeignKey(TransactionTypeInput, related_name='+', on_delete=models.PROTECT,
#                                                  null=True, blank=True)
#     strategy3_cash_input = models.ForeignKey(TransactionTypeInput, related_name='+', on_delete=models.PROTECT,
#                                              null=True, blank=True)
#
#     accounting_date_expr = models.CharField(max_length=255, blank=True, default='')
#     cash_date_expr = models.CharField(max_length=255, blank=True, default='')
#
#     class Meta:
#         verbose_name = _('transaction type item')
#         verbose_name_plural = _('transaction type tems')
#
#     def __str__(self):
#         return 'item #%s' % self.id

@python_2_unicode_compatible
class TransactionTypeAction(models.Model):
    transaction_type = models.ForeignKey(
        TransactionType,
        related_name='actions',
        on_delete=models.PROTECT
    )
    order = models.IntegerField(default=0)

    class Meta:
        verbose_name = _('action')
        verbose_name_plural = _('actions')
        unique_together = [
            ['transaction_type', 'order']
        ]
        ordering = ['transaction_type', 'order']

    def __str__(self):
        return 'Action #%s' % self.order


class TransactionTypeActionInstrument(TransactionTypeAction):
    user_code = models.CharField(
        max_length=255,
        blank=True,
        default='',
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        default='',
    )
    public_name = models.CharField(
        max_length=255,
        blank=True,
        default='',
    )
    short_name = models.CharField(
        max_length=255,
        blank=True,
        default='',
    )
    notes = models.CharField(
        max_length=255,
        blank=True,
        default='',
    )

    instrument_type = models.ForeignKey(
        'instruments.InstrumentType',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )
    instrument_type_input = models.ForeignKey(
        TransactionTypeInput,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+'
    )

    pricing_currency = models.ForeignKey(
        'currencies.Currency',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )
    pricing_currency_input = models.ForeignKey(
        TransactionTypeInput,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )

    price_multiplier = models.CharField(
        max_length=255,
        default='0.'
    )

    accrued_currency = models.ForeignKey(
        'currencies.Currency',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )
    accrued_currency_input = models.ForeignKey(
        TransactionTypeInput,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )

    accrued_multiplier = models.CharField(
        max_length=255,
        default='0.'
    )

    daily_pricing_model = models.ForeignKey(
        'instruments.DailyPricingModel',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )
    daily_pricing_model_input = models.ForeignKey(
        TransactionTypeInput,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )

    payment_size_detail = models.ForeignKey(
        'instruments.PaymentSizeDetail',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )
    payment_size_detail_input = models.ForeignKey(
        TransactionTypeInput,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )

    default_price = models.CharField(
        max_length=255,
        default='0.'
    )

    default_accrued = models.CharField(
        max_length=255,
        default='0.'
    )

    class Meta:
        verbose_name = _('action instrument')
        verbose_name_plural = _('action instruments')


class TransactionTypeActionTransaction(TransactionTypeAction):
    transaction_class = models.ForeignKey(
        TransactionClass,
        on_delete=models.PROTECT,
        related_name='+',
    )

    instrument = models.ForeignKey(
        Instrument,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )
    instrument_input = models.ForeignKey(
        TransactionTypeInput,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )

    transaction_currency = models.ForeignKey(
        Currency,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )
    transaction_currency_input = models.ForeignKey(
        TransactionTypeInput,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )

    position_size_with_sign = models.CharField(
        max_length=255,
        default='0.'
    )

    settlement_currency = models.ForeignKey(
        Currency,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )
    settlement_currency_input = models.ForeignKey(
        TransactionTypeInput,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )

    cash_consideration = models.CharField(
        max_length=255,
        default='0.'
    )
    principal_with_sign = models.CharField(
        max_length=255,
        default='0.'
    )
    carry_with_sign = models.CharField(
        max_length=255,
        default='0.'
    )
    overheads_with_sign = models.CharField(
        max_length=255,
        default='0.'
    )

    account_position = models.ForeignKey(
        Account,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )
    account_position_input = models.ForeignKey(
        TransactionTypeInput,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )

    account_cash = models.ForeignKey(
        Account,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )
    account_cash_input = models.ForeignKey(
        TransactionTypeInput,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )

    account_interim = models.ForeignKey(
        Account,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )
    account_interim_input = models.ForeignKey(
        TransactionTypeInput,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )

    accounting_date = models.CharField(
        max_length=255,
        blank=True,
        default=''
    )

    cash_date = models.CharField(
        max_length=255,
        blank=True,
        default=''
    )

    strategy1_position = models.ForeignKey(
        Strategy1,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )
    strategy1_position_input = models.ForeignKey(
        TransactionTypeInput,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )

    strategy1_cash = models.ForeignKey(
        Strategy1,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )
    strategy1_cash_input = models.ForeignKey(
        TransactionTypeInput,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )

    strategy2_position = models.ForeignKey(
        Strategy2,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )
    strategy2_position_input = models.ForeignKey(
        TransactionTypeInput,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )

    strategy2_cash = models.ForeignKey(
        Strategy2,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )
    strategy2_cash_input = models.ForeignKey(
        TransactionTypeInput,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )

    strategy3_position = models.ForeignKey(
        Strategy3,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )
    strategy3_position_input = models.ForeignKey(
        TransactionTypeInput,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )

    strategy3_cash = models.ForeignKey(
        Strategy3,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )
    strategy3_cash_input = models.ForeignKey(
        TransactionTypeInput,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )

    class Meta:
        verbose_name = _('action transaction')
        verbose_name_plural = _('action transactions')


class EventToHandle(NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='events_to_handle',
                                    verbose_name=_('master user'))
    transaction_type = models.ForeignKey(TransactionType, on_delete=models.PROTECT,
                                         verbose_name=_('transaction type'))
    notification_date = models.DateField(null=True, blank=True,
                                         verbose_name=_('notification date'))
    effective_date = models.DateField(null=True, blank=True,
                                      verbose_name=_('effective date'))

    class Meta(NamedModel.Meta):
        verbose_name = _('event to handle')
        verbose_name_plural = _('events to handle')


@python_2_unicode_compatible
class Transaction(models.Model):
    master_user = models.ForeignKey(MasterUser, related_name='transactions',
                                    verbose_name=_('master user'))
    transaction_code = models.IntegerField(default=0,
                                           verbose_name=_('transaction code'))
    transaction_class = models.ForeignKey(TransactionClass, on_delete=models.PROTECT,
                                          verbose_name=_("transaction class"))

    portfolio = models.ForeignKey(Portfolio, on_delete=models.PROTECT,
                                  verbose_name=_("portfolio"))

    # Position related
    instrument = models.ForeignKey(Instrument, on_delete=models.PROTECT, null=True, blank=True,
                                   verbose_name=_("instrument"))
    transaction_currency = models.ForeignKey(Currency, related_name='transactions_as_instrument',
                                             on_delete=models.PROTECT, null=True, blank=True,
                                             verbose_name=_("transaction currency"))
    position_size_with_sign = models.FloatField(null=True, blank=True,
                                                verbose_name=_("position size with sign"))

    # Cash related
    settlement_currency = models.ForeignKey(Currency, related_name='transactions', on_delete=models.PROTECT,
                                            verbose_name=_("settlement currency"))
    cash_consideration = models.FloatField(null=True, blank=True,
                                           verbose_name=_("cash consideration"))

    # P&L related
    principal_with_sign = models.FloatField(null=True, blank=True,
                                            verbose_name=_("principal with sign"))
    carry_with_sign = models.FloatField(null=True, blank=True,
                                        verbose_name=_("carry with sign"))
    overheads_with_sign = models.FloatField(null=True, blank=True,
                                            verbose_name=_("overheads with sign"))

    # accounting dates
    transaction_date = models.DateField(editable=False, default=timezone.now,
                                        verbose_name=_("transaction date"))
    accounting_date = models.DateField(default=timezone.now,
                                       verbose_name=_("accounting date"))
    cash_date = models.DateField(default=timezone.now,
                                 verbose_name=_("cash date"))

    account_position = models.ForeignKey(Account, related_name='account_positions', on_delete=models.PROTECT, null=True,
                                         blank=True,
                                         verbose_name=_("account position"))
    account_cash = models.ForeignKey(Account, related_name='transaction_cashs', on_delete=models.PROTECT, null=True,
                                     blank=True,
                                     verbose_name=_("account cash"))
    account_interim = models.ForeignKey(Account, related_name='account_interims', on_delete=models.PROTECT, null=True,
                                        blank=True,
                                        verbose_name=_("account interim"))

    strategy1_position = models.ForeignKey(
        Strategy1,
        null=True,
        blank=True,
        related_name='transaction_as_position',
        on_delete=models.PROTECT,
        verbose_name=_("strategy - 1 - cash")
    )
    strategy1_cash = models.ForeignKey(
        Strategy1,
        null=True,
        blank=True,
        related_name='transaction_as_cash',
        on_delete=models.PROTECT,
        verbose_name=_("strategy - 1 - position")
    )
    strategy2_position = models.ForeignKey(
        Strategy2,
        null=True,
        blank=True,
        related_name='transaction_as_position',
        on_delete=models.PROTECT,
        verbose_name=_("strategy - 2 - cash"),
    )
    strategy2_cash = models.ForeignKey(
        Strategy2,
        null=True,
        blank=True,
        related_name='transaction_as_cash',
        on_delete=models.PROTECT,
        verbose_name=_("strategy - 2 - position")
    )
    strategy3_position = models.ForeignKey(
        Strategy3,
        null=True,
        blank=True,
        related_name='transaction_as_position',
        on_delete=models.PROTECT,
        verbose_name=_("strategy - 3 - cash")
    )
    strategy3_cash = models.ForeignKey(
        Strategy3,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='transaction_as_cash',
        verbose_name=_("strategy - 3 - position")
    )

    reference_fx_rate = models.FloatField(null=True, blank=True,
                                          verbose_name=_("reference fx-rate"),
                                          help_text=_("FX rate to convert from Settlement ccy to Instrument "
                                                      "Ccy on Accounting Date (trade date)"))

    # other
    is_locked = models.BooleanField(default=False,
                                    verbose_name=_("is locked"),
                                    help_text=_('If checked - transaction cannot be changed'))
    is_canceled = models.BooleanField(default=False,
                                      verbose_name=_("is canceled"),
                                      help_text=_('If checked - transaction is cancelled'))
    factor = models.FloatField(null=True, blank=True,
                               verbose_name=_("factor"),
                               help_text=_('Multiplier (for calculations on the form)'))
    trade_price = models.FloatField(null=True, blank=True,
                                    verbose_name=_("trade price"),
                                    help_text=_('Price (for calculations on the form)'))
    principal_amount = models.FloatField(null=True, blank=True,
                                         verbose_name=_("principal amount"),
                                         help_text=_(
                                             'Absolute value of Principal with Sign (for calculations on the form)'))
    carry_amount = models.FloatField(null=True, blank=True,
                                     verbose_name=_("carry amount"),
                                     help_text=_('Absolute value of Carry with Sign (for calculations on the form)'))
    overheads = models.FloatField(null=True, blank=True,
                                  verbose_name=_("overheads"),
                                  help_text=_('Absolute value of Carry with Sign (for calculations on the form)'))

    # information
    # notes_front_office = models.TextField(null=True, blank=True,
    #                                       help_text=_('Notes front office'))
    # notes_middle_office = models.TextField(null=True, blank=True,
    #                                        help_text=_('Notes middle office'))
    responsible = models.ForeignKey(Responsible, on_delete=models.PROTECT, null=True, blank=True,
                                    verbose_name=_("responsible"),
                                    help_text=_("Trader or transaction executer"))
    # responsible_text = models.CharField(max_length=50, null=True, blank=True,
    #                                     help_text=_("Text for non-frequent responsible"))
    counterparty = models.ForeignKey(Counterparty, on_delete=models.PROTECT, null=True, blank=True,
                                     verbose_name=_("counterparty"))

    # counterparty_text = models.CharField(max_length=50, null=True, blank=True,
    #                                      help_text=_('Text for non-frequent counterparty'))

    # strategy_position = TreeForeignKey(Strategy, null=True, blank=True, related_name='+',
    #                                    verbose_name='temporary strategy position')
    # strategy_cash = TreeForeignKey(Strategy, null=True, blank=True, related_name='+',
    #                                verbose_name='temporary strategy cash')

    class Meta:
        verbose_name = _('transaction')
        verbose_name_plural = _('transactions')
        # permissions = [
        #     ('view_transaction', 'Can view transaction')
        # ]

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
    # strategy_position_root = models.ForeignKey(Strategy, related_name='strategy_transaction_attribute_types',
    #                                            on_delete=models.PROTECT, null=True, blank=True,
    #                                            verbose_name=_("strategy position (root)"))
    # strategy_cash_root = models.ForeignKey(Strategy, related_name='cash_transaction_attribute_types',
    #                                        on_delete=models.PROTECT, null=True, blank=True,
    #                                        verbose_name=_("strategy cash (root)"))

    class Meta(AttributeTypeBase.Meta):
        verbose_name = _('transaction attribute type')
        verbose_name_plural = _('transaction attribute types')


class TransactionAttributeTypeOption(AttributeTypeOptionBase):
    member = models.ForeignKey(Member, related_name='transaction_attribute_type_options',
                               verbose_name=_("member"))
    attribute_type = models.ForeignKey(TransactionAttributeType, related_name='options',
                                       verbose_name=_("attribute type"))

    class Meta(AttributeTypeOptionBase.Meta):
        verbose_name = _('transaction attribute types - option')
        verbose_name_plural = _('transaction attribute types - options')


class TransactionAttributeTypeUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(TransactionAttributeType, related_name='user_object_permissions',
                                       verbose_name=_("content object"))

    class Meta(UserObjectPermissionBase.Meta):
        verbose_name = _('transaction attribute types - user permission')
        verbose_name_plural = _('transaction attribute types - user permissions')


class TransactionAttributeTypeGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(TransactionAttributeType, related_name='group_object_permissions',
                                       verbose_name=_("content object"))

    class Meta(GroupObjectPermissionBase.Meta):
        verbose_name = _('transaction attribute types - group permission')
        verbose_name_plural = _('transaction attribute types - group permissions')


class TransactionAttribute(AttributeBase):
    attribute_type = models.ForeignKey(TransactionAttributeType, related_name='attributes', on_delete=models.PROTECT,
                                       verbose_name=_("attribute type"))
    content_object = models.ForeignKey(Transaction, related_name='attributes',
                                       verbose_name=_("content object"))
    # strategy_position = models.ForeignKey(Strategy, related_name='strategy_transaction_attributes',
    #                                       on_delete=models.PROTECT, null=True, blank=True,
    #                                       verbose_name=_("strategy position"))
    # strategy_cash = models.ForeignKey(Strategy, related_name='cash_transaction_attributes', on_delete=models.PROTECT,
    #                                   null=True, blank=True,
    #                                   verbose_name=_("strategy cash"))
    classifier = None

    class Meta(AttributeBase.Meta):
        verbose_name = _('transaction attribute')
        verbose_name_plural = _('transaction attributes')

        # def get_value(self):
        #     t = self.attribute_type.value_type
        #     if t == AttributeTypeBase.CLASSIFIER:
        #         return self.strategy_position, self.strategy_position
        #     else:
        #         return super(TransactionAttribute, self).get_value()
        #
        # def set_value(self, value):
        #     t = self.attribute_type.value_type
        #     if t == AttributeTypeBase.CLASSIFIER:
        #         self.strategy_position, self.strategy_position = value
        #     else:
        #         super(TransactionAttribute, self).set_value(value)


@python_2_unicode_compatible
class ExternalCashFlow(models.Model):
    master_user = models.ForeignKey(MasterUser, related_name='external_cash_flows',
                                    verbose_name=_('master user'))
    date = models.DateField(default=timezone.now, db_index=True,
                            verbose_name=_("date"))
    portfolio = models.ForeignKey(Portfolio, related_name='external_cash_flows', on_delete=models.PROTECT,
                                  verbose_name=_("portfolio"))
    account = models.ForeignKey(Account, related_name='external_cash_flows', on_delete=models.PROTECT,
                                verbose_name=_("account"))
    currency = models.ForeignKey(Currency, related_name='external_cash_flows', on_delete=models.PROTECT,
                                 verbose_name=_("currency"))
    amount = models.FloatField(default=0.,
                               verbose_name=_("amount"))

    class Meta:
        verbose_name = _('external cash flow')
        verbose_name_plural = _('external cash flows')

    def __str__(self):
        return '%s: %s - %s - %s - %s = %s' % (self.date, self.portfolio, self.account, list(self.strategies.all()),
                                               self.currency, self.amount)


@python_2_unicode_compatible
class ExternalCashFlowStrategy(models.Model):
    external_cash_flow = models.ForeignKey(
        ExternalCashFlow,
        related_name='strategies',
        verbose_name=_("external cash flow")
    )
    order = models.IntegerField(
        default=0,
        verbose_name=_("order")
    )
    strategy1 = models.ForeignKey(
        Strategy1,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="external_cash_flow_strategies",
        verbose_name=_("strategy1")
    )
    strategy2 = models.ForeignKey(
        Strategy2,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="external_cash_flow_strategies",
        verbose_name=_("strategy2")
    )
    strategy3 = models.ForeignKey(
        Strategy3,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="external_cash_flow_strategies",
        verbose_name=_("strategy3")
    )

    class Meta:
        verbose_name = _('external cash flow strategy')
        verbose_name_plural = _('external cash flow strtegies')
        ordering = ['external_cash_flow', 'order']

    def __str__(self):
        return '%s' % self.strategy


history.register(TransactionClass)
history.register(ActionClass)
history.register(EventClass)
history.register(NotificationClass)
history.register(PeriodicityGroup)

history.register(TransactionType)
history.register(TransactionAttributeType)
history.register(TransactionAttributeTypeOption)
history.register(TransactionAttribute)
history.register(ExternalCashFlow, follow=['strategies'])
history.register(ExternalCashFlowStrategy, follow=['external_cash_flow'])
