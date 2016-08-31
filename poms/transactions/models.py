from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from poms.accounts.models import Account
from poms.common.models import NamedModel, AbstractClassModel
from poms.common.utils import date_now
from poms.counterparties.models import Responsible, Counterparty
from poms.currencies.models import Currency
from poms.instruments.models import Instrument
from poms.obj_attrs.models import AbstractAttributeType, AbstractAttribute, AbstractAttributeTypeOption, \
    AbstractClassifier
from poms.obj_perms.models import AbstractGroupObjectPermission, AbstractUserObjectPermission
from poms.portfolios.models import Portfolio
from poms.strategies.models import Strategy1, Strategy2, Strategy3
from poms.users.models import MasterUser, Member, FakeSequence


class TransactionClass(AbstractClassModel):
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
        (BUY, 'BUY', _("Buy")),
        (SELL, 'SELL', _("Sell")),
        (FX_TRADE, 'FX_TRADE', _("FX Trade")),
        (INSTRUMENT_PL, 'INSTRUMENT_PL', _("Instrument PL")),
        (TRANSACTION_PL, 'TRANSACTION_PL', _("Transaction PL")),
        (TRANSFER, 'TRANSFER', _("Transfer")),
        (FX_TRANSFER, 'FX_TRANSFER', _("FX Transfer")),
        (CASH_INFLOW, 'CASH_INFLOW', _("Cash-Inflow")),
        (CASH_OUTFLOW, 'CASH_OUTFLOW', _("Cash-Outflow")),
    )

    class Meta(AbstractClassModel.Meta):
        verbose_name = _('transaction class')
        verbose_name_plural = _('transaction classes')


class ActionClass(AbstractClassModel):
    CREATE_INSTRUMENT = 1
    CREATE_INSTRUMENT_PARAMETER = 2

    CLASSES = (
        (CREATE_INSTRUMENT, 'CREATE_INSTRUMENT', _("Create instrument")),
        (CREATE_INSTRUMENT_PARAMETER, 'CREATE_INSTRUMENT_PARAMETER', _("Create instrument parameter")),
    )

    class Meta(AbstractClassModel.Meta):
        verbose_name = _('action class')
        verbose_name_plural = _('action classes')


class EventClass(AbstractClassModel):
    ONE_OFF = 1
    REGULAR = 2

    CLASSES = (
        (ONE_OFF, 'ONE_OFF', _('One-off')),
        (REGULAR, 'REGULAR', _('Regular')),
    )

    class Meta(AbstractClassModel.Meta):
        verbose_name = _('event class')
        verbose_name_plural = _('event classes')


class NotificationClass(AbstractClassModel):
    # NDATE -> notification_date
    # EDATE -> effective_date

    DONT_REACT = 1
    APPLY_DEF_ON_EDATE = 2
    APPLY_DEF_ON_NDATE = 3

    INFORM_ON_NDATE_WITH_REACT = 4
    INFORM_ON_NDATE_APPLY_DEF = 5
    INFORM_ON_NDATE_DONT_REACT = 6
    INFORM_ON_EDATE_WITH_REACT = 7
    INFORM_ON_EDATE_APPLY_DEF = 8
    INFORM_ON_EDATE_DONT_REACT = 9

    INFORM_ON_NDATE_AND_EDATE_WITH_REACT_ON_EDATE = 10
    INFORM_ON_NDATE_AND_EDATE_WITH_REACT_ON_NDATE = 11
    INFORM_ON_NDATE_AND_EDATE_APPLY_DEF_ON_EDATE = 12
    INFORM_ON_NDATE_AND_EDATE_APPLY_DEF_ON_NDATE = 13
    INFORM_ON_NDATE_AND_EDATE_DONT_REACT = 14

    CLASSES = (
        (DONT_REACT, 'DONT_REACT',
         _("Don't inform (don't react)")),
        (APPLY_DEF_ON_EDATE, 'APPLY_DEF_ON_EDATE',
         _("Don't inform (apply default on effective date)")),
        (APPLY_DEF_ON_NDATE, 'APPLY_DEF_ON_NDATE',
         _("Don't inform (apply default on notification date)")),
        (INFORM_ON_NDATE_WITH_REACT, 'INFORM_ON_NDATE_WITH_REACT',
         _("Inform on notification date (with reaction)")),
        (INFORM_ON_NDATE_APPLY_DEF, 'INFORM_ON_NDATE_APPLY_DEF',
         _("Inform on notification date (apply default)")),
        (INFORM_ON_NDATE_DONT_REACT, 'INFORM_ON_NDATE_DONT_REACT',
         _("Inform on notification date (don't react)")),
        (INFORM_ON_EDATE_WITH_REACT, 'INFORM_ON_EDATE_WITH_REACT',
         _("Inform on effective date (with reaction)")),
        (INFORM_ON_EDATE_APPLY_DEF, 'INFORM_ON_EDATE_APPLY_DEF',
         _("Inform on effective date (apply default)")),
        (INFORM_ON_EDATE_DONT_REACT, 'INFORM_ON_EDATE_DONT_REACT',
         _("Inform on effective date (don't react)")),
        (INFORM_ON_NDATE_AND_EDATE_WITH_REACT_ON_EDATE, 'INFORM_ON_NDATE_AND_EDATE_WITH_REACT_ON_EDATE',
         _("Inform on notification date & effective date (with reaction on effective date)")),
        (INFORM_ON_NDATE_AND_EDATE_WITH_REACT_ON_NDATE, 'INFORM_ON_NDATE_AND_EDATE_WITH_REACT_ON_NDATE',
         _("Inform on notification date & effective date (with reaction on notification date)")),
        (INFORM_ON_NDATE_AND_EDATE_APPLY_DEF_ON_EDATE, 'INFORM_ON_NDATE_AND_EDATE_APPLY_DEF_ON_EDATE',
         _("Inform on notification date & effective date (apply default on effective date)")),
        (INFORM_ON_NDATE_AND_EDATE_APPLY_DEF_ON_NDATE, 'INFORM_ON_NDATE_AND_EDATE_APPLY_DEF_ON_NDATE',
         _("Inform on notification date & effective date (apply default on notification date)")),
        (INFORM_ON_NDATE_AND_EDATE_DONT_REACT, 'INFORM_ON_NDATE_AND_EDATE_DONT_REACT',
         _("Inform on notification date & effective date (don't react)")),
    )

    class Meta(AbstractClassModel.Meta):
        verbose_name = _('notification class')
        verbose_name_plural = _('notification classes')


class PeriodicityGroup(AbstractClassModel):
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
        (DAILY, 'DAILY', _("daily")),
        (WEEKLY, 'WEEKLY', _("weekly (+7d)")),
        (WEEKLY_EOW, 'WEEKLY_EOW', _("weekly (eow)")),
        (BE_WEEKLY, 'BE_WEEKLY', _("bi-weekly (+14d)")),
        (BE_WEEKLY_EOW, 'BE_WEEKLY_EOW', _("bi-weekly (eow)")),
        (MONTHLY, 'MONTHLY', _("monthly (+1m)")),
        (MONTHLY_EOM, 'MONTHLY_EOM', _("monthly (eom)")),
        (QUARTERLY, 'QUARTERLY', _("quarterly (+3m)")),
        (QUARTERLY_CALENDAR, 'QUARTERLY_CALENDAR', _("quarterly (calendar)")),
        (SEMI_ANUALLY, 'SEMI_ANUALLY', _("semi-anually (+6m)")),
        (SEMI_ANUALLY_CALENDAR, 'SEMI_ANUALLY_CALENDAR', _("semi-anually (calendar)")),
        (ANUALLY, 'ANUALLY', _("anually (+12m)")),
        (ANUALLY_CALENDAR, 'ANUALLY_CALENDAR', _("anually (eoy)")),
    )

    class Meta(AbstractClassModel.Meta):
        verbose_name = _('periodicity group')
        verbose_name_plural = _('periodicity group')


class TransactionTypeGroup(NamedModel):
    master_user = models.ForeignKey(
        MasterUser,
        related_name='transaction_type_groups',
        verbose_name=_('master user')
    )

    class Meta(NamedModel.Meta):
        verbose_name = _('transaction type group')
        verbose_name_plural = _('transaction type groups')
        unique_together = [
            ['master_user', 'user_code']
        ]
        permissions = [
            ('view_transactiontypegroup', 'Can view transaction type group'),
            ('manage_transactiontypegroup', 'Can manage transaction type group'),
        ]


class TransactionTypeGroupUserObjectPermission(AbstractUserObjectPermission):
    content_object = models.ForeignKey(TransactionTypeGroup, related_name='user_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractUserObjectPermission.Meta):
        verbose_name = _('transaction type groups - user permission')
        verbose_name_plural = _('transaction type groups - user permissions')


class TransactionTypeGroupGroupObjectPermission(AbstractGroupObjectPermission):
    content_object = models.ForeignKey(TransactionTypeGroup, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractGroupObjectPermission.Meta):
        verbose_name = _('transaction type groups - group permission')
        verbose_name_plural = _('transaction type groups - group permissions')


class TransactionType(NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='transaction_types', verbose_name=_('master user'))
    group = models.ForeignKey(TransactionTypeGroup, null=True, blank=True, on_delete=models.PROTECT)
    display_expr = models.CharField(max_length=255, blank=True, default='')
    instrument_types = models.ManyToManyField('instruments.InstrumentType', related_name='transaction_types',
                                              blank=True, verbose_name=_('instrument types'))

    # portfolios = models.ManyToManyField(
    #     'portfolios.Portfolio',
    #     related_name='transaction_types',
    #     blank=True,
    #     verbose_name=_('portfolios')
    # )

    class Meta(NamedModel.Meta):
        verbose_name = _('transaction type')
        verbose_name_plural = _('transaction types')
        unique_together = [
            ['master_user', 'user_code']
        ]
        permissions = [
            ('view_transactiontype', 'Can view transaction type'),
            ('manage_transactiontype', 'Can manage transaction type'),
        ]


class TransactionTypeUserObjectPermission(AbstractUserObjectPermission):
    content_object = models.ForeignKey(TransactionType, related_name='user_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractUserObjectPermission.Meta):
        verbose_name = _('transaction types - user permission')
        verbose_name_plural = _('transaction types - user permissions')


class TransactionTypeGroupObjectPermission(AbstractGroupObjectPermission):
    content_object = models.ForeignKey(TransactionType, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractGroupObjectPermission.Meta):
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

    transaction_type = models.ForeignKey(TransactionType, related_name='inputs')
    name = models.CharField(max_length=255, null=True, blank=True)
    verbose_name = models.CharField(max_length=255, null=True, blank=True)
    value_type = models.PositiveSmallIntegerField(default=NUMBER, choices=TYPES, verbose_name=_('value type'))
    content_type = models.ForeignKey(ContentType, null=True, blank=True, verbose_name=_('content type'))
    order = models.IntegerField(default=0, verbose_name=_('order'))

    class Meta:
        verbose_name = _('transaction type input')
        verbose_name_plural = _('transaction type inputs')
        unique_together = [
            ['transaction_type', 'name'],
        ]
        index_together = [
            ['transaction_type', 'order'],
        ]
        ordering = ['transaction_type', 'order']

    def __str__(self):
        if self.value_type == self.RELATION:
            return '%s: %s' % (self.name, self.content_type)
        else:
            return '%s: %s' % (self.name, self.get_value_type_display())

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.verbose_name:
            self.verbose_name = self.name
        super(TransactionTypeInput, self).save(force_insert=force_insert, force_update=force_update, using=using,
                                               update_fields=update_fields)


@python_2_unicode_compatible
class TransactionTypeAction(models.Model):
    transaction_type = models.ForeignKey(TransactionType, related_name='actions', on_delete=models.PROTECT)
    order = models.IntegerField(default=0)

    class Meta:
        verbose_name = _('action')
        verbose_name_plural = _('actions')
        # unique_together = [
        #     ['transaction_type', 'order']
        # ]
        index_together = [
            ['transaction_type', 'order'],
        ]
        ordering = ['transaction_type', 'order']

    def __str__(self):
        return 'Action #%s' % self.order


class TransactionTypeActionInstrument(TransactionTypeAction):
    user_code = models.CharField(max_length=255, blank=True, default='')
    name = models.CharField(max_length=255, blank=True, default='')
    public_name = models.CharField(max_length=255, blank=True, default='')
    short_name = models.CharField(max_length=255, blank=True, default='')
    notes = models.CharField(max_length=255, blank=True, default='')

    instrument_type = models.ForeignKey('instruments.InstrumentType', null=True, blank=True, on_delete=models.PROTECT,
                                        related_name='+')
    instrument_type_input = models.ForeignKey(TransactionTypeInput, null=True, blank=True, on_delete=models.PROTECT,
                                              related_name='+')

    pricing_currency = models.ForeignKey('currencies.Currency', null=True, blank=True, on_delete=models.PROTECT,
                                         related_name='+')
    pricing_currency_input = models.ForeignKey(TransactionTypeInput, null=True, blank=True, on_delete=models.PROTECT,
                                               related_name='+')

    price_multiplier = models.CharField(max_length=255, default='0.')

    accrued_currency = models.ForeignKey('currencies.Currency', null=True, blank=True, on_delete=models.PROTECT,
                                         related_name='+')
    accrued_currency_input = models.ForeignKey(TransactionTypeInput, null=True, blank=True, on_delete=models.PROTECT,
                                               related_name='+')

    accrued_multiplier = models.CharField(max_length=255, default='0.')

    payment_size_detail = models.ForeignKey('instruments.PaymentSizeDetail', null=True, blank=True,
                                            on_delete=models.PROTECT, related_name='+')
    payment_size_detail_input = models.ForeignKey(TransactionTypeInput, null=True, blank=True, on_delete=models.PROTECT,
                                                  related_name='+')

    default_price = models.CharField(max_length=255, default='0.')
    default_accrued = models.CharField(max_length=255, default='0.')

    user_text_1 = models.CharField(max_length=255, blank=True, default='')
    user_text_2 = models.CharField(max_length=255, blank=True, default='')
    user_text_3 = models.CharField(max_length=255, blank=True, default='')

    reference_for_pricing = models.CharField(max_length=100, blank=True, default='',
                                             verbose_name=_('reference for pricing'))
    daily_pricing_model = models.ForeignKey('instruments.DailyPricingModel', null=True, blank=True,
                                            on_delete=models.PROTECT, related_name='+')
    daily_pricing_model_input = models.ForeignKey(TransactionTypeInput, null=True, blank=True, on_delete=models.PROTECT,
                                                  related_name='+')
    price_download_scheme = models.ForeignKey('integrations.PriceDownloadScheme', on_delete=models.PROTECT, null=True,
                                              blank=True, verbose_name=_('price download scheme'))
    price_download_scheme_input = models.ForeignKey(TransactionTypeInput, null=True, blank=True,
                                                    on_delete=models.PROTECT, related_name='+')
    maturity_date = models.CharField(max_length=255, default='now()')

    class Meta:
        verbose_name = _('transaction type action instrument')
        verbose_name_plural = _('transaction type action instruments')

    def __str__(self):
        return 'Instrument action #%s' % self.order


class TransactionTypeActionTransaction(TransactionTypeAction):
    transaction_class = models.ForeignKey(TransactionClass, on_delete=models.PROTECT, related_name='+')

    portfolio = models.ForeignKey(Portfolio, null=True, blank=True, on_delete=models.PROTECT, related_name='+')
    portfolio_input = models.ForeignKey(TransactionTypeInput, null=True, blank=True, on_delete=models.PROTECT,
                                        related_name='+')

    instrument = models.ForeignKey(Instrument, null=True, blank=True, on_delete=models.PROTECT, related_name='+')
    instrument_input = models.ForeignKey(TransactionTypeInput, null=True, blank=True, on_delete=models.PROTECT,
                                         related_name='+')
    instrument_phantom = models.ForeignKey(TransactionTypeActionInstrument, null=True, blank=True,
                                           on_delete=models.PROTECT, related_name='+')

    transaction_currency = models.ForeignKey(Currency, null=True, blank=True, on_delete=models.PROTECT,
                                             related_name='+')
    transaction_currency_input = models.ForeignKey(TransactionTypeInput, null=True, blank=True,
                                                   on_delete=models.PROTECT, related_name='+')

    position_size_with_sign = models.CharField(max_length=255, default='0.')

    settlement_currency = models.ForeignKey(Currency, null=True, blank=True, on_delete=models.PROTECT,
                                            related_name='+')
    settlement_currency_input = models.ForeignKey(TransactionTypeInput, null=True, blank=True, on_delete=models.PROTECT,
                                                  related_name='+')

    cash_consideration = models.CharField(max_length=255, default='0.')
    principal_with_sign = models.CharField(max_length=255, default='0.')
    carry_with_sign = models.CharField(max_length=255, default='0.')
    overheads_with_sign = models.CharField(max_length=255, default='0.')

    account_position = models.ForeignKey(Account, null=True, blank=True, on_delete=models.PROTECT, related_name='+')
    account_position_input = models.ForeignKey(TransactionTypeInput, null=True, blank=True, on_delete=models.PROTECT,
                                               related_name='+')

    account_cash = models.ForeignKey(Account, null=True, blank=True, on_delete=models.PROTECT, related_name='+')
    account_cash_input = models.ForeignKey(TransactionTypeInput, null=True, blank=True, on_delete=models.PROTECT,
                                           related_name='+')

    account_interim = models.ForeignKey(Account, null=True, blank=True, on_delete=models.PROTECT, related_name='+')
    account_interim_input = models.ForeignKey(TransactionTypeInput, null=True, blank=True, on_delete=models.PROTECT,
                                              related_name='+')

    accounting_date = models.CharField(max_length=255, blank=True, default='')

    cash_date = models.CharField(max_length=255, blank=True, default='')

    strategy1_position = models.ForeignKey(Strategy1, null=True, blank=True, on_delete=models.PROTECT,
                                           related_name='+')
    strategy1_position_input = models.ForeignKey(TransactionTypeInput, null=True, blank=True, on_delete=models.PROTECT,
                                                 related_name='+')

    strategy1_cash = models.ForeignKey(Strategy1, null=True, blank=True, on_delete=models.PROTECT, related_name='+')
    strategy1_cash_input = models.ForeignKey(TransactionTypeInput, null=True, blank=True, on_delete=models.PROTECT,
                                             related_name='+')

    strategy2_position = models.ForeignKey(Strategy2, null=True, blank=True, on_delete=models.PROTECT,
                                           related_name='+')
    strategy2_position_input = models.ForeignKey(TransactionTypeInput, null=True, blank=True, on_delete=models.PROTECT,
                                                 related_name='+')

    strategy2_cash = models.ForeignKey(Strategy2, null=True, blank=True, on_delete=models.PROTECT, related_name='+')
    strategy2_cash_input = models.ForeignKey(TransactionTypeInput, null=True, blank=True, on_delete=models.PROTECT,
                                             related_name='+')

    strategy3_position = models.ForeignKey(Strategy3, null=True, blank=True, on_delete=models.PROTECT,
                                           related_name='+')
    strategy3_position_input = models.ForeignKey(TransactionTypeInput, null=True, blank=True, on_delete=models.PROTECT,
                                                 related_name='+')

    strategy3_cash = models.ForeignKey(Strategy3, null=True, blank=True, on_delete=models.PROTECT, related_name='+')
    strategy3_cash_input = models.ForeignKey(TransactionTypeInput, null=True, blank=True, on_delete=models.PROTECT,
                                             related_name='+')

    reference_fx_rate = models.CharField(max_length=255, default='0.')

    factor = models.CharField(max_length=255, default='0.')
    trade_price = models.CharField(max_length=255, default='0.')
    principal_amount = models.CharField(max_length=255, default='0.')
    carry_amount = models.CharField(max_length=255, default='0.')
    overheads = models.CharField(max_length=255, default='0.')

    responsible = models.ForeignKey(Responsible, null=True, blank=True, on_delete=models.PROTECT, related_name='+')
    responsible_input = models.ForeignKey(TransactionTypeInput, null=True, blank=True, on_delete=models.PROTECT,
                                          related_name='+')

    counterparty = models.ForeignKey(Counterparty, null=True, blank=True, on_delete=models.PROTECT, related_name='+')
    counterparty_input = models.ForeignKey(TransactionTypeInput, null=True, blank=True, on_delete=models.PROTECT,
                                           related_name='+')

    class Meta:
        verbose_name = _('transaction type action transaction')
        verbose_name_plural = _('transaction type action transactions')

    def __str__(self):
        return 'Transaction action #%s' % self.order


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
class ComplexTransaction(models.Model):
    transaction_type = models.ForeignKey(TransactionType, on_delete=models.PROTECT)
    code = models.IntegerField(default=0)

    class Meta:
        verbose_name = _('complex transaction')
        verbose_name_plural = _('complex transactions')
        index_together = [
            ['transaction_type', 'code']
        ]

    def __str__(self):
        return "ComplexTransaction #%s" % self.code

    def save(self, *args, **kwargs):
        if self.code is None or self.code == 0:
            self.code = FakeSequence.next_value(self.transaction_type.master_user, 'complex_transaction')
        super(ComplexTransaction, self).save(*args, **kwargs)


@python_2_unicode_compatible
class Transaction(models.Model):
    master_user = models.ForeignKey(MasterUser, related_name='transactions',
                                    verbose_name=_('master user'))
    complex_transaction = models.ForeignKey(ComplexTransaction, on_delete=models.PROTECT, null=True, blank=True,
                                            related_name='transactions')
    complex_transaction_order = models.PositiveSmallIntegerField(default=0.)
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
    transaction_date = models.DateField(editable=False, default=date_now,
                                        verbose_name=_("transaction date"))
    accounting_date = models.DateField(default=date_now,
                                       verbose_name=_("accounting date"))
    cash_date = models.DateField(default=date_now,
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

    strategy1_position = models.ForeignKey(Strategy1, null=True, blank=True, related_name='transaction_as_position1',
                                           on_delete=models.PROTECT, verbose_name=_("strategy - 1 - cash"))
    strategy1_cash = models.ForeignKey(Strategy1, null=True, blank=True, related_name='transaction_as_cash1',
                                       on_delete=models.PROTECT, verbose_name=_("strategy - 1 - position"))
    strategy2_position = models.ForeignKey(Strategy2, null=True, blank=True, related_name='transaction_as_position2',
                                           on_delete=models.PROTECT, verbose_name=_("strategy - 2 - cash"))
    strategy2_cash = models.ForeignKey(Strategy2, null=True, blank=True, related_name='transaction_as_cash2',
                                       on_delete=models.PROTECT, verbose_name=_("strategy - 2 - position"))
    strategy3_position = models.ForeignKey(Strategy3, null=True, blank=True, related_name='transaction_as_position3',
                                           on_delete=models.PROTECT, verbose_name=_("strategy - 3 - cash"))
    strategy3_cash = models.ForeignKey(Strategy3, null=True, blank=True, on_delete=models.PROTECT,
                                       related_name='transaction_as_cash3', verbose_name=_("strategy - 3 - position"))

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

    responsible = models.ForeignKey(Responsible, on_delete=models.PROTECT, null=True, blank=True,
                                    verbose_name=_("responsible"),
                                    help_text=_("Trader or transaction executer"))
    counterparty = models.ForeignKey(Counterparty, on_delete=models.PROTECT, null=True, blank=True,
                                     verbose_name=_("counterparty"))

    class Meta:
        verbose_name = _('transaction')
        verbose_name_plural = _('transactions')
        index_together = [
            ['master_user', 'transaction_code']
        ]

    def __str__(self):
        return 'Transaction #%s' % (self.transaction_code)

    def save(self, *args, **kwargs):
        self.transaction_date = min(self.accounting_date, self.cash_date)
        if self.transaction_code is None or self.transaction_code == 0:
            self.transaction_code = FakeSequence.next_value(self.master_user, 'transaction')
        super(Transaction, self).save(*args, **kwargs)


class TransactionAttributeType(AbstractAttributeType):
    class Meta(AbstractAttributeType.Meta):
        verbose_name = _('transaction attribute type')
        verbose_name_plural = _('transaction attribute types')
        permissions = [
            ('view_transactionattributetype', 'Can view transaction attribute type'),
            ('manage_transactionattributetype', 'Can manage transaction attribute type'),
        ]


class TransactionAttributeTypeUserObjectPermission(AbstractUserObjectPermission):
    content_object = models.ForeignKey(TransactionAttributeType, related_name='user_object_permissions',
                                       verbose_name=_("content object"))

    class Meta(AbstractUserObjectPermission.Meta):
        verbose_name = _('transaction attribute types - user permission')
        verbose_name_plural = _('transaction attribute types - user permissions')


class TransactionAttributeTypeGroupObjectPermission(AbstractGroupObjectPermission):
    content_object = models.ForeignKey(TransactionAttributeType, related_name='group_object_permissions',
                                       verbose_name=_("content object"))

    class Meta(AbstractGroupObjectPermission.Meta):
        verbose_name = _('transaction attribute types - group permission')
        verbose_name_plural = _('transaction attribute types - group permissions')


class TransactionClassifier(AbstractClassifier):
    attribute_type = models.ForeignKey(TransactionAttributeType, null=True, blank=True, related_name='classifiers',
                                       verbose_name=_('attribute type'))
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True,
                            verbose_name=_('parent'))

    class Meta(AbstractClassifier.Meta):
        verbose_name = _('transaction classifier')
        verbose_name_plural = _('transaction classifiers')


class TransactionAttributeTypeOption(AbstractAttributeTypeOption):
    member = models.ForeignKey(Member, related_name='transaction_attribute_type_options',
                               verbose_name=_("member"))
    attribute_type = models.ForeignKey(TransactionAttributeType, related_name='options',
                                       verbose_name=_("attribute type"))

    class Meta(AbstractAttributeTypeOption.Meta):
        verbose_name = _('transaction attribute types - option')
        verbose_name_plural = _('transaction attribute types - options')


class TransactionAttribute(AbstractAttribute):
    attribute_type = models.ForeignKey(TransactionAttributeType, related_name='attributes', on_delete=models.PROTECT,
                                       verbose_name=_("attribute type"))
    content_object = models.ForeignKey(Transaction, related_name='attributes',
                                       verbose_name=_("content object"))
    classifier = models.ForeignKey(TransactionClassifier, on_delete=models.PROTECT, null=True, blank=True,
                                   verbose_name=_('classifier'))

    class Meta(AbstractAttribute.Meta):
        verbose_name = _('transaction attribute')
        verbose_name_plural = _('transaction attributes')


@python_2_unicode_compatible
class ExternalCashFlow(models.Model):
    master_user = models.ForeignKey(MasterUser, related_name='external_cash_flows',
                                    verbose_name=_('master user'))
    date = models.DateField(default=date_now, db_index=True,
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
    external_cash_flow = models.ForeignKey(ExternalCashFlow, related_name='strategies',
                                           verbose_name=_("external cash flow"))
    order = models.IntegerField(default=0, verbose_name=_("order"))
    strategy1 = models.ForeignKey(Strategy1, on_delete=models.PROTECT, null=True, blank=True,
                                  related_name="external_cash_flow_strategies1", verbose_name=_("strategy1"))
    strategy2 = models.ForeignKey(Strategy2, on_delete=models.PROTECT, null=True, blank=True,
                                  related_name="external_cash_flow_strategies2", verbose_name=_("strategy2"))
    strategy3 = models.ForeignKey(Strategy3, on_delete=models.PROTECT, null=True, blank=True,
                                  related_name="external_cash_flow_strategies3", verbose_name=_("strategy3"))

    class Meta:
        verbose_name = _('external cash flow strategy')
        verbose_name_plural = _('external cash flow strtegies')
        ordering = ['external_cash_flow', 'order']

    def __str__(self):
        return '%s' % self.strategy
