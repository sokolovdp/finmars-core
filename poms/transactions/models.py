from __future__ import unicode_literals

import json

from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from poms.accounts.models import Account
from poms.common.models import NamedModel, AbstractClassModel, FakeDeletableModel
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
        (BUY, 'BUY', ugettext_lazy("Buy")),
        (SELL, 'SELL', ugettext_lazy("Sell")),
        (FX_TRADE, 'FX_TRADE', ugettext_lazy("FX Trade")),
        (INSTRUMENT_PL, 'INSTRUMENT_PL', ugettext_lazy("Instrument PL")),
        (TRANSACTION_PL, 'TRANSACTION_PL', ugettext_lazy("Transaction PL")),
        (TRANSFER, 'TRANSFER', ugettext_lazy("Transfer")),
        (FX_TRANSFER, 'FX_TRANSFER', ugettext_lazy("FX Transfer")),
        (CASH_INFLOW, 'CASH_INFLOW', ugettext_lazy("Cash-Inflow")),
        (CASH_OUTFLOW, 'CASH_OUTFLOW', ugettext_lazy("Cash-Outflow")),
    )

    class Meta(AbstractClassModel.Meta):
        verbose_name = ugettext_lazy('transaction class')
        verbose_name_plural = ugettext_lazy('transaction classes')


class ActionClass(AbstractClassModel):
    CREATE_INSTRUMENT = 1
    CREATE_INSTRUMENT_PARAMETER = 2

    CLASSES = (
        (CREATE_INSTRUMENT, 'CREATE_INSTRUMENT', ugettext_lazy("Create instrument")),
        (CREATE_INSTRUMENT_PARAMETER, 'CREATE_INSTRUMENT_PARAMETER', ugettext_lazy("Create instrument parameter")),
    )

    class Meta(AbstractClassModel.Meta):
        verbose_name = ugettext_lazy('action class')
        verbose_name_plural = ugettext_lazy('action classes')


class EventClass(AbstractClassModel):
    ONE_OFF = 1
    REGULAR = 2

    CLASSES = (
        (ONE_OFF, 'ONE_OFF', ugettext_lazy('One-off')),
        (REGULAR, 'REGULAR', ugettext_lazy('Regular')),
    )

    class Meta(AbstractClassModel.Meta):
        verbose_name = ugettext_lazy('event class')
        verbose_name_plural = ugettext_lazy('event classes')


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
         ugettext_lazy("Don't inform (don't react)")),
        (APPLY_DEF_ON_EDATE, 'APPLY_DEF_ON_EDATE',
         ugettext_lazy("Don't inform (apply default on effective date)")),
        (APPLY_DEF_ON_NDATE, 'APPLY_DEF_ON_NDATE',
         ugettext_lazy("Don't inform (apply default on notification date)")),
        (INFORM_ON_NDATE_WITH_REACT, 'INFORM_ON_NDATE_WITH_REACT',
         ugettext_lazy("Inform on notification date (with reaction)")),
        (INFORM_ON_NDATE_APPLY_DEF, 'INFORM_ON_NDATE_APPLY_DEF',
         ugettext_lazy("Inform on notification date (apply default)")),
        (INFORM_ON_NDATE_DONT_REACT, 'INFORM_ON_NDATE_DONT_REACT',
         ugettext_lazy("Inform on notification date (don't react)")),
        (INFORM_ON_EDATE_WITH_REACT, 'INFORM_ON_EDATE_WITH_REACT',
         ugettext_lazy("Inform on effective date (with reaction)")),
        (INFORM_ON_EDATE_APPLY_DEF, 'INFORM_ON_EDATE_APPLY_DEF',
         ugettext_lazy("Inform on effective date (apply default)")),
        (INFORM_ON_EDATE_DONT_REACT, 'INFORM_ON_EDATE_DONT_REACT',
         ugettext_lazy("Inform on effective date (don't react)")),
        (INFORM_ON_NDATE_AND_EDATE_WITH_REACT_ON_EDATE, 'INFORM_ON_NDATE_AND_EDATE_WITH_REACT_ON_EDATE',
         ugettext_lazy("Inform on notification date & effective date (with reaction on effective date)")),
        (INFORM_ON_NDATE_AND_EDATE_WITH_REACT_ON_NDATE, 'INFORM_ON_NDATE_AND_EDATE_WITH_REACT_ON_NDATE',
         ugettext_lazy("Inform on notification date & effective date (with reaction on notification date)")),
        (INFORM_ON_NDATE_AND_EDATE_APPLY_DEF_ON_EDATE, 'INFORM_ON_NDATE_AND_EDATE_APPLY_DEF_ON_EDATE',
         ugettext_lazy("Inform on notification date & effective date (apply default on effective date)")),
        (INFORM_ON_NDATE_AND_EDATE_APPLY_DEF_ON_NDATE, 'INFORM_ON_NDATE_AND_EDATE_APPLY_DEF_ON_NDATE',
         ugettext_lazy("Inform on notification date & effective date (apply default on notification date)")),
        (INFORM_ON_NDATE_AND_EDATE_DONT_REACT, 'INFORM_ON_NDATE_AND_EDATE_DONT_REACT',
         ugettext_lazy("Inform on notification date & effective date (don't react)")),
    )

    class Meta(AbstractClassModel.Meta):
        verbose_name = ugettext_lazy('notification class')
        verbose_name_plural = ugettext_lazy('notification classes')


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
        (DAILY, 'DAILY', ugettext_lazy("daily")),
        (WEEKLY, 'WEEKLY', ugettext_lazy("weekly (+7d)")),
        (WEEKLY_EOW, 'WEEKLY_EOW', ugettext_lazy("weekly (eow)")),
        (BE_WEEKLY, 'BE_WEEKLY', ugettext_lazy("bi-weekly (+14d)")),
        (BE_WEEKLY_EOW, 'BE_WEEKLY_EOW', ugettext_lazy("bi-weekly (eow)")),
        (MONTHLY, 'MONTHLY', ugettext_lazy("monthly (+1m)")),
        (MONTHLY_EOM, 'MONTHLY_EOM', ugettext_lazy("monthly (eom)")),
        (QUARTERLY, 'QUARTERLY', ugettext_lazy("quarterly (+3m)")),
        (QUARTERLY_CALENDAR, 'QUARTERLY_CALENDAR', ugettext_lazy("quarterly (calendar)")),
        (SEMI_ANUALLY, 'SEMI_ANUALLY', ugettext_lazy("semi-anually (+6m)")),
        (SEMI_ANUALLY_CALENDAR, 'SEMI_ANUALLY_CALENDAR', ugettext_lazy("semi-anually (calendar)")),
        (ANUALLY, 'ANUALLY', ugettext_lazy("anually (+12m)")),
        (ANUALLY_CALENDAR, 'ANUALLY_CALENDAR', ugettext_lazy("anually (eoy)")),
    )

    class Meta(AbstractClassModel.Meta):
        verbose_name = ugettext_lazy('periodicity group')
        verbose_name_plural = ugettext_lazy('periodicity group')


class TransactionTypeGroup(NamedModel, FakeDeletableModel):
    master_user = models.ForeignKey(
        MasterUser,
        related_name='transaction_type_groups',
        verbose_name=ugettext_lazy('master user')
    )

    class Meta(NamedModel.Meta, FakeDeletableModel.Meta):
        verbose_name = ugettext_lazy('transaction type group')
        verbose_name_plural = ugettext_lazy('transaction type groups')
        permissions = [
            ('view_transactiontypegroup', 'Can view transaction type group'),
            ('manage_transactiontypegroup', 'Can manage transaction type group'),
        ]


class TransactionTypeGroupUserObjectPermission(AbstractUserObjectPermission):
    content_object = models.ForeignKey(TransactionTypeGroup, related_name='user_object_permissions',
                                       verbose_name=ugettext_lazy('content object'))

    class Meta(AbstractUserObjectPermission.Meta):
        verbose_name = ugettext_lazy('transaction type groups - user permission')
        verbose_name_plural = ugettext_lazy('transaction type groups - user permissions')


class TransactionTypeGroupGroupObjectPermission(AbstractGroupObjectPermission):
    content_object = models.ForeignKey(TransactionTypeGroup, related_name='group_object_permissions',
                                       verbose_name=ugettext_lazy('content object'))

    class Meta(AbstractGroupObjectPermission.Meta):
        verbose_name = ugettext_lazy('transaction type groups - group permission')
        verbose_name_plural = ugettext_lazy('transaction type groups - group permissions')


class TransactionType(NamedModel, FakeDeletableModel):
    master_user = models.ForeignKey(MasterUser, related_name='transaction_types',
                                    verbose_name=ugettext_lazy('master user'))
    group = models.ForeignKey(TransactionTypeGroup, null=True, blank=True, on_delete=models.PROTECT)
    display_expr = models.CharField(max_length=255, blank=True, default='')
    instrument_types = models.ManyToManyField('instruments.InstrumentType', related_name='transaction_types',
                                              blank=True, verbose_name=ugettext_lazy('instrument types'))
    is_valid_for_all_portfolios = models.BooleanField(default=True)
    is_valid_for_all_instruments = models.BooleanField(default=True)
    book_transaction_layout_json = models.TextField(null=True, blank=True)

    # portfolios = models.ManyToManyField(
    #     'portfolios.Portfolio',
    #     related_name='transaction_types',
    #     blank=True,
    #     verbose_name=ugettext_lazy('portfolios')
    # )

    class Meta(NamedModel.Meta, FakeDeletableModel.Meta):
        verbose_name = ugettext_lazy('transaction type')
        verbose_name_plural = ugettext_lazy('transaction types')
        permissions = [
            ('view_transactiontype', 'Can view transaction type'),
            ('manage_transactiontype', 'Can manage transaction type'),
        ]
        ordering = ['user_code']

    @property
    def book_transaction_layout(self):
        try:
            return json.loads(self.book_transaction_layout_json) if self.book_transaction_layout_json else None
        except (ValueError, TypeError):
            return None

    @book_transaction_layout.setter
    def book_transaction_layout(self, data):
        self.book_transaction_layout_json = json.dumps(data, cls=DjangoJSONEncoder, sort_keys=True) if data else None


class TransactionTypeUserObjectPermission(AbstractUserObjectPermission):
    content_object = models.ForeignKey(TransactionType, related_name='user_object_permissions',
                                       verbose_name=ugettext_lazy('content object'))

    class Meta(AbstractUserObjectPermission.Meta):
        verbose_name = ugettext_lazy('transaction types - user permission')
        verbose_name_plural = ugettext_lazy('transaction types - user permissions')


class TransactionTypeGroupObjectPermission(AbstractGroupObjectPermission):
    content_object = models.ForeignKey(TransactionType, related_name='group_object_permissions',
                                       verbose_name=ugettext_lazy('content object'))

    class Meta(AbstractGroupObjectPermission.Meta):
        verbose_name = ugettext_lazy('transaction types - group permission')
        verbose_name_plural = ugettext_lazy('transaction types - group permissions')


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
        (NUMBER, ugettext_lazy('Number')),
        (STRING, ugettext_lazy('String')),
        (DATE, ugettext_lazy('Date')),
        # (EXPRESSION, ugettext_lazy('Expression')),
        (RELATION, ugettext_lazy('Relation')),
        # (ACCOUNT, ugettext_lazy('Account')),
        # (INSTRUMENT, ugettext_lazy('Instrument')),
        # (CURRENCY, ugettext_lazy('Currency')),
        # (COUNTERPARTY, ugettext_lazy('Counterparty')),
        # (RESPONSIBLE, ugettext_lazy('Responsible')),
        # (STRATEGY1, ugettext_lazy('Strategy 1')),
        # (STRATEGY2, ugettext_lazy('Strategy 2')),
        # (STRATEGY3, ugettext_lazy('Strategy 3')),
        # (DAILY_PRICING_MODEL, ugettext_lazy('Daily pricing model')),
        # (PAYMENT_SIZE_DETAIL, ugettext_lazy('Payment size detail')),
        # (INSTRUMENT_TYPE, ugettext_lazy('Instrument type'))
    )

    transaction_type = models.ForeignKey(TransactionType, related_name='inputs')
    name = models.CharField(max_length=255, null=True, blank=True)
    verbose_name = models.CharField(max_length=255, null=True, blank=True)
    value_type = models.PositiveSmallIntegerField(default=NUMBER, choices=TYPES,
                                                  verbose_name=ugettext_lazy('value type'))
    content_type = models.ForeignKey(ContentType, null=True, blank=True, verbose_name=ugettext_lazy('content type'))
    order = models.IntegerField(default=0, verbose_name=ugettext_lazy('order'))

    is_fill_from_context = models.BooleanField(default=False)
    value = models.CharField(max_length=255, null=True, blank=True, help_text=ugettext_lazy('is expression'))
    account = models.ForeignKey('accounts.Account', null=True, blank=True, on_delete=models.PROTECT, related_name='+')
    instrument_type = models.ForeignKey('instruments.InstrumentType', null=True, blank=True, on_delete=models.PROTECT,
                                        related_name='+')
    instrument = models.ForeignKey('instruments.Instrument', null=True, blank=True, on_delete=models.PROTECT,
                                   related_name='+')
    currency = models.ForeignKey('currencies.Currency', null=True, blank=True, on_delete=models.PROTECT,
                                 related_name='+')
    counterparty = models.ForeignKey('counterparties.Counterparty', null=True, blank=True, on_delete=models.PROTECT,
                                     related_name='+')
    responsible = models.ForeignKey('counterparties.Responsible', null=True, blank=True, on_delete=models.PROTECT,
                                    related_name='+')
    portfolio = models.ForeignKey('portfolios.Portfolio', null=True, blank=True, on_delete=models.PROTECT,
                                  related_name='+')
    strategy1 = models.ForeignKey('strategies.Strategy1', null=True, blank=True, on_delete=models.PROTECT,
                                  related_name='+')
    strategy2 = models.ForeignKey('strategies.Strategy2', null=True, blank=True, on_delete=models.PROTECT,
                                  related_name='+')
    strategy3 = models.ForeignKey('strategies.Strategy3', null=True, blank=True, on_delete=models.PROTECT,
                                  related_name='+')
    daily_pricing_model = models.ForeignKey('instruments.DailyPricingModel', null=True, blank=True,
                                            on_delete=models.PROTECT, related_name='+')
    payment_size_detail = models.ForeignKey('instruments.PaymentSizeDetail', null=True, blank=True,
                                            on_delete=models.PROTECT, related_name='+')
    price_download_scheme = models.ForeignKey('integrations.PriceDownloadScheme', null=True, blank=True,
                                              on_delete=models.PROTECT, related_name='+')

    class Meta:
        verbose_name = ugettext_lazy('transaction type input')
        verbose_name_plural = ugettext_lazy('transaction type inputs')
        unique_together = [
            ['transaction_type', 'name'],
        ]
        index_together = [
            ['transaction_type', 'order'],
        ]
        ordering = ['name']

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
    action_notes = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = ugettext_lazy('action')
        verbose_name_plural = ugettext_lazy('actions')
        # unique_together = [
        #     ['transaction_type', 'order']
        # ]
        index_together = [
            ['transaction_type', 'order'],
        ]
        ordering = ['order']

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
                                             verbose_name=ugettext_lazy('reference for pricing'))
    daily_pricing_model = models.ForeignKey('instruments.DailyPricingModel', null=True, blank=True,
                                            on_delete=models.PROTECT, related_name='+')
    daily_pricing_model_input = models.ForeignKey(TransactionTypeInput, null=True, blank=True, on_delete=models.PROTECT,
                                                  related_name='+')
    price_download_scheme = models.ForeignKey('integrations.PriceDownloadScheme', on_delete=models.PROTECT, null=True,
                                              blank=True, verbose_name=ugettext_lazy('price download scheme'))
    price_download_scheme_input = models.ForeignKey(TransactionTypeInput, null=True, blank=True,
                                                    on_delete=models.PROTECT, related_name='+')
    maturity_date = models.CharField(max_length=255, default='now()')

    class Meta:
        verbose_name = ugettext_lazy('transaction type action instrument')
        verbose_name_plural = ugettext_lazy('transaction type action instruments')

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
        verbose_name = ugettext_lazy('transaction type action transaction')
        verbose_name_plural = ugettext_lazy('transaction type action transactions')

    def __str__(self):
        return 'Transaction action #%s' % self.order


class EventToHandle(NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='events_to_handle',
                                    verbose_name=ugettext_lazy('master user'))
    transaction_type = models.ForeignKey(TransactionType, on_delete=models.PROTECT,
                                         verbose_name=ugettext_lazy('transaction type'))
    notification_date = models.DateField(null=True, blank=True,
                                         verbose_name=ugettext_lazy('notification date'))
    effective_date = models.DateField(null=True, blank=True,
                                      verbose_name=ugettext_lazy('effective date'))

    class Meta(NamedModel.Meta):
        verbose_name = ugettext_lazy('event to handle')
        verbose_name_plural = ugettext_lazy('events to handle')


@python_2_unicode_compatible
class ComplexTransaction(models.Model):
    transaction_type = models.ForeignKey(TransactionType, on_delete=models.PROTECT)
    code = models.IntegerField(default=0)

    class Meta:
        verbose_name = ugettext_lazy('complex transaction')
        verbose_name_plural = ugettext_lazy('complex transactions')
        index_together = [
            ['transaction_type', 'code']
        ]
        ordering = ['code']

    def __str__(self):
        return str(self.code)

    def save(self, *args, **kwargs):
        if self.code is None or self.code == 0:
            self.code = FakeSequence.next_value(self.transaction_type.master_user, 'complex_transaction')
        super(ComplexTransaction, self).save(*args, **kwargs)


@python_2_unicode_compatible
class Transaction(models.Model):
    master_user = models.ForeignKey(MasterUser, related_name='transactions', verbose_name=ugettext_lazy('master user'))
    complex_transaction = models.ForeignKey(ComplexTransaction, on_delete=models.PROTECT, null=True, blank=True,
                                            related_name='transactions')
    complex_transaction_order = models.PositiveSmallIntegerField(default=0.)
    transaction_code = models.IntegerField(default=0, verbose_name=ugettext_lazy('transaction code'))
    transaction_class = models.ForeignKey(TransactionClass, on_delete=models.PROTECT,
                                          verbose_name=ugettext_lazy("transaction class"))

    portfolio = models.ForeignKey(Portfolio, on_delete=models.PROTECT, verbose_name=ugettext_lazy("portfolio"))

    # Position related
    instrument = models.ForeignKey(Instrument, on_delete=models.PROTECT, null=True, blank=True,
                                   verbose_name=ugettext_lazy("instrument"))
    transaction_currency = models.ForeignKey(Currency, related_name='transactions_as_instrument',
                                             on_delete=models.PROTECT, null=True, blank=True,
                                             verbose_name=ugettext_lazy("transaction currency"))
    position_size_with_sign = models.FloatField(default=0.0, verbose_name=ugettext_lazy("position size with sign"))

    # Cash related
    settlement_currency = models.ForeignKey(Currency, related_name='transactions', on_delete=models.PROTECT,
                                            verbose_name=ugettext_lazy("settlement currency"))
    cash_consideration = models.FloatField(default=0.0, verbose_name=ugettext_lazy("cash consideration"))

    # P&L related
    principal_with_sign = models.FloatField(default=0.0, verbose_name=ugettext_lazy("principal with sign"))
    carry_with_sign = models.FloatField(default=0.0, verbose_name=ugettext_lazy("carry with sign"))
    overheads_with_sign = models.FloatField(default=0.0, verbose_name=ugettext_lazy("overheads with sign"))

    # accounting dates
    transaction_date = models.DateField(editable=False, default=date_now,
                                        verbose_name=ugettext_lazy("transaction date"))
    accounting_date = models.DateField(default=date_now, verbose_name=ugettext_lazy("accounting date"))
    cash_date = models.DateField(default=date_now, verbose_name=ugettext_lazy("cash date"))

    account_position = models.ForeignKey(Account, related_name='account_positions', on_delete=models.PROTECT, null=True,
                                         blank=True, verbose_name=ugettext_lazy("account position"))
    account_cash = models.ForeignKey(Account, related_name='transaction_cashs', on_delete=models.PROTECT, null=True,
                                     blank=True, verbose_name=ugettext_lazy("account cash"))
    account_interim = models.ForeignKey(Account, related_name='account_interims', on_delete=models.PROTECT, null=True,
                                        blank=True, verbose_name=ugettext_lazy("account interim"))

    strategy1_position = models.ForeignKey(Strategy1, null=True, blank=True, related_name='transaction_as_position1',
                                           on_delete=models.PROTECT, verbose_name=ugettext_lazy("strategy - 1 - cash"))
    strategy1_cash = models.ForeignKey(Strategy1, null=True, blank=True, related_name='transaction_as_cash1',
                                       on_delete=models.PROTECT, verbose_name=ugettext_lazy("strategy - 1 - position"))
    strategy2_position = models.ForeignKey(Strategy2, null=True, blank=True, related_name='transaction_as_position2',
                                           on_delete=models.PROTECT, verbose_name=ugettext_lazy("strategy - 2 - cash"))
    strategy2_cash = models.ForeignKey(Strategy2, null=True, blank=True, related_name='transaction_as_cash2',
                                       on_delete=models.PROTECT, verbose_name=ugettext_lazy("strategy - 2 - position"))
    strategy3_position = models.ForeignKey(Strategy3, null=True, blank=True, related_name='transaction_as_position3',
                                           on_delete=models.PROTECT, verbose_name=ugettext_lazy("strategy - 3 - cash"))
    strategy3_cash = models.ForeignKey(Strategy3, null=True, blank=True, on_delete=models.PROTECT,
                                       related_name='transaction_as_cash3',
                                       verbose_name=ugettext_lazy("strategy - 3 - position"))

    reference_fx_rate = models.FloatField(default=0.0, verbose_name=ugettext_lazy("reference fx-rate"),
                                          help_text=ugettext_lazy(
                                              "FX rate to convert from Settlement ccy to Instrument "
                                              "Ccy on Accounting Date (trade date)"))

    # other
    is_locked = models.BooleanField(default=False, verbose_name=ugettext_lazy("is locked"),
                                    help_text=ugettext_lazy('If checked - transaction cannot be changed'))
    is_canceled = models.BooleanField(default=False, verbose_name=ugettext_lazy("is canceled"),
                                      help_text=ugettext_lazy('If checked - transaction is cancelled'))
    factor = models.FloatField(default=0.0, verbose_name=ugettext_lazy("factor"),
                               help_text=ugettext_lazy('Multiplier (for calculations on the form)'))
    trade_price = models.FloatField(default=0.0, verbose_name=ugettext_lazy("trade price"),
                                    help_text=ugettext_lazy('Price (for calculations on the form)'))
    principal_amount = models.FloatField(default=0.0, verbose_name=ugettext_lazy("principal amount"),
                                         help_text=ugettext_lazy(
                                             'Absolute value of Principal with Sign (for calculations on the form)'))
    carry_amount = models.FloatField(default=0.0, verbose_name=ugettext_lazy("carry amount"),
                                     help_text=ugettext_lazy(
                                         'Absolute value of Carry with Sign (for calculations on the form)'))
    overheads = models.FloatField(default=0.0, verbose_name=ugettext_lazy("overheads"),
                                  help_text=ugettext_lazy(
                                      'Absolute value of Carry with Sign (for calculations on the form)'))

    responsible = models.ForeignKey(Responsible, on_delete=models.PROTECT, null=True, blank=True,
                                    verbose_name=ugettext_lazy("responsible"),
                                    help_text=ugettext_lazy("Trader or transaction executer"))
    counterparty = models.ForeignKey(Counterparty, on_delete=models.PROTECT, null=True, blank=True,
                                     verbose_name=ugettext_lazy("counterparty"))

    class Meta:
        verbose_name = ugettext_lazy('transaction')
        verbose_name_plural = ugettext_lazy('transactions')
        index_together = [
            ['master_user', 'transaction_code']
        ]
        ordering = ['transaction_date', 'transaction_code']

    def __str__(self):
        return 'Transaction #%s' % (self.transaction_code)

    def save(self, *args, **kwargs):
        self.transaction_date = min(self.accounting_date, self.cash_date)
        if self.transaction_code is None or self.transaction_code == 0:
            self.transaction_code = FakeSequence.next_value(self.master_user, 'transaction')
        super(Transaction, self).save(*args, **kwargs)


class TransactionAttributeType(AbstractAttributeType):
    class Meta(AbstractAttributeType.Meta):
        verbose_name = ugettext_lazy('transaction attribute type')
        verbose_name_plural = ugettext_lazy('transaction attribute types')
        permissions = [
            ('view_transactionattributetype', 'Can view transaction attribute type'),
            ('manage_transactionattributetype', 'Can manage transaction attribute type'),
        ]


class TransactionAttributeTypeUserObjectPermission(AbstractUserObjectPermission):
    content_object = models.ForeignKey(TransactionAttributeType, related_name='user_object_permissions',
                                       verbose_name=ugettext_lazy("content object"))

    class Meta(AbstractUserObjectPermission.Meta):
        verbose_name = ugettext_lazy('transaction attribute types - user permission')
        verbose_name_plural = ugettext_lazy('transaction attribute types - user permissions')


class TransactionAttributeTypeGroupObjectPermission(AbstractGroupObjectPermission):
    content_object = models.ForeignKey(TransactionAttributeType, related_name='group_object_permissions',
                                       verbose_name=ugettext_lazy("content object"))

    class Meta(AbstractGroupObjectPermission.Meta):
        verbose_name = ugettext_lazy('transaction attribute types - group permission')
        verbose_name_plural = ugettext_lazy('transaction attribute types - group permissions')


class TransactionClassifier(AbstractClassifier):
    attribute_type = models.ForeignKey(TransactionAttributeType, related_name='classifiers',
                                       verbose_name=ugettext_lazy('attribute type'))
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True,
                            verbose_name=ugettext_lazy('parent'))

    class Meta(AbstractClassifier.Meta):
        verbose_name = ugettext_lazy('transaction classifier')
        verbose_name_plural = ugettext_lazy('transaction classifiers')


class TransactionAttributeTypeOption(AbstractAttributeTypeOption):
    member = models.ForeignKey(Member, related_name='transaction_attribute_type_options',
                               verbose_name=ugettext_lazy("member"))
    attribute_type = models.ForeignKey(TransactionAttributeType, related_name='options',
                                       verbose_name=ugettext_lazy("attribute type"))

    class Meta(AbstractAttributeTypeOption.Meta):
        verbose_name = ugettext_lazy('transaction attribute types - option')
        verbose_name_plural = ugettext_lazy('transaction attribute types - options')


class TransactionAttribute(AbstractAttribute):
    attribute_type = models.ForeignKey(TransactionAttributeType, related_name='attributes',
                                       verbose_name=ugettext_lazy("attribute type"))
    content_object = models.ForeignKey(Transaction, related_name='attributes',
                                       verbose_name=ugettext_lazy("content object"))
    classifier = models.ForeignKey(TransactionClassifier, on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name=ugettext_lazy('classifier'))

    class Meta(AbstractAttribute.Meta):
        verbose_name = ugettext_lazy('transaction attribute')
        verbose_name_plural = ugettext_lazy('transaction attributes')


@python_2_unicode_compatible
class ExternalCashFlow(models.Model):
    master_user = models.ForeignKey(MasterUser, related_name='external_cash_flows',
                                    verbose_name=ugettext_lazy('master user'))
    date = models.DateField(default=date_now, db_index=True,
                            verbose_name=ugettext_lazy("date"))
    portfolio = models.ForeignKey(Portfolio, related_name='external_cash_flows', on_delete=models.PROTECT,
                                  verbose_name=ugettext_lazy("portfolio"))
    account = models.ForeignKey(Account, related_name='external_cash_flows', on_delete=models.PROTECT,
                                verbose_name=ugettext_lazy("account"))
    currency = models.ForeignKey(Currency, related_name='external_cash_flows', on_delete=models.PROTECT,
                                 verbose_name=ugettext_lazy("currency"))
    amount = models.FloatField(default=0.,
                               verbose_name=ugettext_lazy("amount"))

    class Meta:
        verbose_name = ugettext_lazy('external cash flow')
        verbose_name_plural = ugettext_lazy('external cash flows')
        ordering = ['date']

    def __str__(self):
        return '%s: %s - %s - %s - %s = %s' % (self.date, self.portfolio, self.account, list(self.strategies.all()),
                                               self.currency, self.amount)


@python_2_unicode_compatible
class ExternalCashFlowStrategy(models.Model):
    external_cash_flow = models.ForeignKey(ExternalCashFlow, related_name='strategies',
                                           verbose_name=ugettext_lazy("external cash flow"))
    order = models.IntegerField(default=0, verbose_name=ugettext_lazy("order"))
    strategy1 = models.ForeignKey(Strategy1, on_delete=models.PROTECT, null=True, blank=True,
                                  related_name="external_cash_flow_strategies1",
                                  verbose_name=ugettext_lazy("strategy1"))
    strategy2 = models.ForeignKey(Strategy2, on_delete=models.PROTECT, null=True, blank=True,
                                  related_name="external_cash_flow_strategies2",
                                  verbose_name=ugettext_lazy("strategy2"))
    strategy3 = models.ForeignKey(Strategy3, on_delete=models.PROTECT, null=True, blank=True,
                                  related_name="external_cash_flow_strategies3",
                                  verbose_name=ugettext_lazy("strategy3"))

    class Meta:
        verbose_name = ugettext_lazy('external cash flow strategy')
        verbose_name_plural = ugettext_lazy('external cash flow strtegies')
        ordering = ['order']

    def __str__(self):
        return '%s' % self.strategy
