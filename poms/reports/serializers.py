from __future__ import unicode_literals

from django.conf import settings
from django.utils.translation import ugettext_lazy
from rest_framework import serializers

from poms.accounts.fields import AccountField
from poms.common.utils import date_now
from poms.currencies.fields import CurrencyField, CurrencyDefault
from poms.instruments.models import CostMethod
from poms.portfolios.fields import PortfolioField
from poms.reports.models import BalanceReport, BalanceReportItem, BalanceReportSummary, PLReportItem, PLReport, \
    PLReportSummary, CostReport, BaseReport
from poms.strategies.fields import Strategy1Field, Strategy2Field, Strategy3Field
from poms.transactions.models import Transaction
from poms.users.fields import MasterUserField


class BaseTransactionSerializer(serializers.ModelSerializer):
    transaction_class_code = serializers.SerializerMethodField()
    transaction_currency_name = serializers.SerializerMethodField()
    portfolio_name = serializers.SerializerMethodField()
    instrument_name = serializers.SerializerMethodField()
    settlement_currency_name = serializers.SerializerMethodField()

    account_cash_name = serializers.SerializerMethodField()
    account_position_name = serializers.SerializerMethodField()
    account_interim_name = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = [
            'id',
            'transaction_class', 'transaction_class_code',
            'portfolio', 'portfolio_name',
            'transaction_currency', 'transaction_currency_name',
            'instrument', 'instrument_name',
            'position_size_with_sign',
            'settlement_currency', 'settlement_currency_name',
            'cash_consideration',
            'principal_with_sign', 'carry_with_sign', 'overheads_with_sign',
            'transaction_date', 'accounting_date', 'cash_date',
            'account_cash', 'account_cash_name',
            'account_position', 'account_position_name',
            'account_interim', 'account_interim_name',
            'reference_fx_rate',
        ]

    def get_transaction_class_code(self, instance):
        return getattr(instance.transaction_class, 'code', None)

    def get_portfolio_name(self, instance):
        return getattr(instance.portfolio, 'name', None)

    def get_transaction_currency_name(self, instance):
        return getattr(instance.transaction_currency, 'name', None)

    def get_instrument_name(self, instance):
        return getattr(instance.instrument, 'name', None)

    def get_settlement_currency_name(self, instance):
        return getattr(instance.settlement_currency, 'name', None)

    def get_account_cash_name(self, instance):
        return getattr(instance.account_cash, 'name', None)

    def get_account_position_name(self, instance):
        return getattr(instance.account_position, 'name', None)

    def get_account_interim_name(self, instance):
        return getattr(instance.account_interim, 'name', None)


class BaseReportItemSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True, source='pk')

    portfolio = serializers.PrimaryKeyRelatedField(read_only=True)
    account = serializers.PrimaryKeyRelatedField(read_only=True)
    strategy1 = serializers.PrimaryKeyRelatedField(read_only=True)
    strategy2 = serializers.PrimaryKeyRelatedField(read_only=True)
    strategy3 = serializers.PrimaryKeyRelatedField(read_only=True)

    instrument = serializers.PrimaryKeyRelatedField(read_only=True)

    name = serializers.CharField(read_only=True)


class BaseReportSerializer(serializers.Serializer):
    task_id = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    task_status = serializers.ReadOnlyField()

    master_user = MasterUserField()

    begin_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True, default=date_now)

    cost_method = serializers.PrimaryKeyRelatedField(queryset=CostMethod.objects, allow_null=True, allow_empty=True,
                                                     initial=CostMethod.AVCO,
                                                     default=lambda: CostMethod.objects.get(pk=CostMethod.AVCO))
    value_currency = CurrencyField(default=CurrencyDefault())

    use_portfolio = serializers.BooleanField(default=False)
    use_account = serializers.BooleanField(default=False)
    use_strategy = serializers.BooleanField(default=False)

    portfolios = PortfolioField(many=True, required=False, allow_null=True, allow_empty=True)
    accounts = AccountField(many=True, required=False, allow_null=True, allow_empty=True)
    strategies1 = Strategy1Field(many=True, required=False, allow_null=True, allow_empty=True)
    strategies2 = Strategy2Field(many=True, required=False, allow_null=True, allow_empty=True)
    strategies3 = Strategy3Field(many=True, required=False, allow_null=True, allow_empty=True)

    # transaction_currencies = CurrencyField(many=True, required=False, allow_null=True)
    # instruments = InstrumentField(many=True, required=False, allow_null=True)


# ----------------------------------------------------------------------------------------------------------------------


class BalanceReportItemSerializer(BaseReportItemSerializer):
    balance_position = serializers.FloatField(read_only=True, help_text=ugettext_lazy('Position'))

    currency = serializers.PrimaryKeyRelatedField(read_only=True, help_text=ugettext_lazy('Currency'))
    # currency_name = serializers.SerializerMethodField()
    currency_history = serializers.PrimaryKeyRelatedField(read_only=True, help_text=ugettext_lazy('Currency history'))
    currency_fx_rate = serializers.FloatField(read_only=True)

    instrument_principal_pricing_ccy = serializers.SerializerMethodField()
    instrument_price_multiplier = serializers.FloatField(read_only=True)
    instrument_accrued_pricing_ccy = serializers.SerializerMethodField()
    instrument_accrued_multiplier = serializers.FloatField(read_only=True)
    price_history = serializers.PrimaryKeyRelatedField(read_only=True, help_text=ugettext_lazy('price history'))
    instrument_principal_price = serializers.FloatField(read_only=True)
    instrument_accrued_price = serializers.FloatField(read_only=True)
    principal_value_instrument_principal_ccy = serializers.FloatField(read_only=True)
    accrued_value_instrument_accrued_ccy = serializers.FloatField(read_only=True)
    instrument_principal_currency_history = serializers.PrimaryKeyRelatedField(read_only=True,
                                                                               help_text=ugettext_lazy(''))
    instrument_principal_fx_rate = serializers.FloatField(read_only=True, help_text=ugettext_lazy(''))
    instrument_accrued_currency_history = serializers.PrimaryKeyRelatedField(read_only=True,
                                                                             help_text=ugettext_lazy(''))
    instrument_accrued_fx_rate = serializers.FloatField(read_only=True, help_text=ugettext_lazy(''))

    principal_value_system_ccy = serializers.FloatField(read_only=True)
    accrued_value_system_ccy = serializers.FloatField(read_only=True)
    market_value_system_ccy = serializers.FloatField(read_only=True)

    transaction = serializers.PrimaryKeyRelatedField(read_only=True,
                                                     help_text=ugettext_lazy('Transaction for case 1&2'))

    def create(self, validated_data):
        return BalanceReportItem(**validated_data)

    def update(self, instance, validated_data):
        return instance

    def get_currency_name(self, instance):
        return getattr(instance.currency, 'name', None)

    def get_instrument_principal_pricing_ccy(self, instance):
        instrument = getattr(instance, 'instrument', None)
        pricing_currency = getattr(instrument, 'pricing_currency', None)
        return getattr(pricing_currency, 'name', None)

    def get_instrument_accrued_pricing_ccy(self, instance):
        instrument = getattr(instance, 'instrument', None)
        accrued_currency = getattr(instrument, 'accrued_currency', None)
        return getattr(accrued_currency, 'name', None)


class BalanceReportSummarySerializer(serializers.Serializer):
    invested_value_system_ccy = serializers.FloatField(read_only=True,
                                                       help_text=ugettext_lazy('invested value in system currency'))
    current_value_system_ccy = serializers.FloatField(read_only=True,
                                                      help_text=ugettext_lazy('current value in system currency'))
    p_l_system_ccy = serializers.FloatField(read_only=True, help_text=ugettext_lazy('position size with sign'))

    def create(self, validated_data):
        return BalanceReportSummary(**validated_data)

    def update(self, instance, validated_data):
        return instance


class BalanceReportSerializer(BaseReportSerializer):
    show_transaction_details = serializers.BooleanField(default=False)
    items = BalanceReportItemSerializer(many=True, read_only=True)

    if settings.DEV:
        summary = BalanceReportSummarySerializer(read_only=True)
        invested_items = BalanceReportItemSerializer(many=True, read_only=True)
        transactions = BaseTransactionSerializer(many=True, read_only=True)

    def create(self, validated_data):
        return BalanceReport(**validated_data)

    def update(self, instance, validated_data):
        return instance


# ----------------------------------------------------------------------------------------------------------------------


class PLReportTransactionSerializer(BaseTransactionSerializer):
    principal_with_sign_system_ccy = serializers.FloatField(read_only=True)
    carry_with_sign_system_ccy = serializers.FloatField(read_only=True)
    overheads_with_sign_system_ccy = serializers.FloatField(read_only=True)

    class Meta:
        model = Transaction
        fields = BaseTransactionSerializer.Meta.fields + [
            'principal_with_sign_system_ccy', 'carry_with_sign_system_ccy', 'overheads_with_sign_system_ccy',
        ]


class PLReportItemSerializer(BaseReportItemSerializer):
    principal_with_sign_system_ccy = serializers.FloatField(read_only=True)
    carry_with_sign_system_ccy = serializers.FloatField(read_only=True)
    overheads_with_sign_system_ccy = serializers.FloatField(read_only=True)
    total_system_ccy = serializers.FloatField(read_only=True)

    def create(self, validated_data):
        return PLReportItem(**validated_data)

    def update(self, instance, validated_data):
        return instance


class PLReportSummarySerializer(serializers.Serializer):
    principal_with_sign_system_ccy = serializers.FloatField(read_only=True,
                                                            help_text=ugettext_lazy(''))
    carry_with_sign_system_ccy = serializers.FloatField(read_only=True,
                                                        help_text=ugettext_lazy(''))
    overheads_with_sign_system_ccy = serializers.FloatField(read_only=True,
                                                            help_text=ugettext_lazy(''))
    total_system_ccy = serializers.FloatField(read_only=True,
                                              help_text=ugettext_lazy(''))

    def create(self, validated_data):
        return PLReportSummary(**validated_data)

    def update(self, instance, validated_data):
        return instance


class PLReportSerializer(BaseReportSerializer):
    items = PLReportItemSerializer(many=True, read_only=True, help_text=ugettext_lazy('items'))

    if settings.DEV:
        summary = PLReportSummarySerializer(read_only=True)
        transactions = PLReportTransactionSerializer(many=True, read_only=True)

    def create(self, validated_data):
        return PLReport(**validated_data)

    def update(self, instance, validated_data):
        return instance


# ----------------------------------------------------------------------------------------------------------------------


class CostTransactionSerializer(BaseTransactionSerializer):
    rolling_position = serializers.FloatField(read_only=True)
    avco_multiplier = serializers.FloatField(read_only=True)
    fifo_multiplier = serializers.FloatField(read_only=True)

    remaining_position = serializers.FloatField(read_only=True)
    remaining_position_cost_settlement_ccy = serializers.FloatField(read_only=True)
    remaining_position_cost_system_ccy = serializers.FloatField(read_only=True)

    class Meta:
        model = Transaction
        fields = BaseTransactionSerializer.Meta.fields + [
            'rolling_position',
            'avco_multiplier', 'fifo_multiplier',
            'remaining_position', 'remaining_position_cost_settlement_ccy', 'remaining_position_cost_system_ccy',
        ]

    def get_transaction_class_code(self, instance):
        return getattr(instance.transaction_class, 'code', None)

    def get_transaction_currency_name(self, instance):
        return getattr(instance.transaction_currency, 'name', None)

    def get_instrument_name(self, instance):
        return getattr(instance.instrument, 'name', None)

    def get_settlement_currency_name(self, instance):
        return getattr(instance.settlement_currency, 'name', None)


class CostReportInstrumentSerializer(BaseReportItemSerializer):
    pricing_currency_name = serializers.SerializerMethodField(read_only=True)
    pricing_currency_fx_rate = serializers.SerializerMethodField()
    price_multiplier = serializers.SerializerMethodField()
    position = serializers.FloatField(read_only=True)
    cost_system_ccy = serializers.FloatField(read_only=True)
    cost_instrument_ccy = serializers.FloatField(read_only=True)
    cost_price = serializers.FloatField(read_only=True)
    cost_price_adjusted = serializers.FloatField(read_only=True)

    def create(self, validated_data):
        return PLReportItem(**validated_data)

    def update(self, instance, validated_data):
        return instance

    def get_pricing_currency_name(self, instance):
        pricing_currency = getattr(instance.instrument, 'pricing_currency', None)
        return getattr(pricing_currency, 'name', None)

    def get_pricing_currency_fx_rate(self, instance):
        pricing_currency_fx_rate = getattr(instance.instrument, 'pricing_currency_fx_rate', None)
        return pricing_currency_fx_rate

    def get_price_multiplier(self, instance):
        return getattr(instance.instrument, 'price_multiplier', None)


class CostReportSerializer(BaseReportSerializer):
    items = CostReportInstrumentSerializer(many=True, read_only=True)

    if settings.DEV:
        transactions = CostTransactionSerializer(many=True, read_only=True)

    def create(self, validated_data):
        return CostReport(**validated_data)

    def update(self, instance, validated_data):
        return instance


# ----------------------------------------------------------------------------------------------------------------------


class YTMTransactionSerializer(BaseTransactionSerializer):
    rolling_position = serializers.FloatField(read_only=True)
    avco_multiplier = serializers.FloatField(read_only=True)
    fifo_multiplier = serializers.FloatField(read_only=True)

    ytm = serializers.FloatField(read_only=True)
    time_invested = serializers.FloatField(read_only=True)
    remaining_position = serializers.FloatField(read_only=True)
    remaining_position_percent = serializers.FloatField(read_only=True)
    weighted_ytm = serializers.FloatField(read_only=True)
    weighted_time_invested = serializers.FloatField(read_only=True)

    class Meta:
        model = Transaction
        fields = BaseTransactionSerializer.Meta.fields + [
            'rolling_position',
            'avco_multiplier', 'fifo_multiplier',
            'ytm', 'time_invested',
            'remaining_position', 'remaining_position_percent',
            'weighted_ytm', 'weighted_time_invested',
        ]

    def get_transaction_class_code(self, instance):
        return getattr(instance.transaction_class, 'code', None)

    def get_transaction_currency_name(self, instance):
        return getattr(instance.transaction_currency, 'name', None)

    def get_instrument_name(self, instance):
        return getattr(instance.instrument, 'name', None)

    def get_settlement_currency_name(self, instance):
        return getattr(instance.settlement_currency, 'name', None)


class YTMReportInstrumentSerializer(BaseReportItemSerializer):
    position = serializers.FloatField(read_only=True)
    ytm = serializers.FloatField(read_only=True)
    time_invested = serializers.FloatField(read_only=True)

    def create(self, validated_data):
        return PLReportItem(**validated_data)

    def update(self, instance, validated_data):
        return instance


class YTMReportSerializer(BaseReportSerializer):
    items = YTMReportInstrumentSerializer(many=True, read_only=True)

    if settings.DEV:
        transactions = YTMTransactionSerializer(many=True, read_only=True)

    def create(self, validated_data):
        return CostReport(**validated_data)

    def update(self, instance, validated_data):
        return instance


# ----------------------------------------------------------------------------------------------------------------------


class SimpleMultipliersReportItemSerializer(BaseReportItemSerializer):
    instrument = serializers.PrimaryKeyRelatedField(read_only=True)
    position_size_with_sign = serializers.FloatField(read_only=True)
    avco_multiplier = serializers.FloatField(read_only=True)
    fifo_multiplier = serializers.FloatField(read_only=True)
    rolling_position = serializers.FloatField(read_only=True)

    def create(self, validated_data):
        return None

    def update(self, instance, validated_data):
        return instance

    def get_currency_name(self, instance):
        return instance.currency.name if instance.currency else None

    def get_instrument_name(self, instance):
        return instance.instrument.name if instance.instrument else None


class SimpleMultipliersReportSerializer(BaseReportSerializer):
    results = SimpleMultipliersReportItemSerializer(many=True, read_only=True,
                                                    help_text=ugettext_lazy('some help text'))

    def create(self, validated_data):
        return BalanceReport(**validated_data)

    def update(self, instance, validated_data):
        return instance


class SimpleMultipliersReport2TransactionSerializer(BaseTransactionSerializer):
    rolling_position = serializers.FloatField(read_only=True)
    avco_multiplier = serializers.FloatField(read_only=True)
    fifo_multiplier = serializers.FloatField(read_only=True)

    class Meta:
        model = Transaction
        fields = BaseTransactionSerializer.Meta.fields + [
            'rolling_position', 'avco_multiplier', 'fifo_multiplier',
        ]


class SimpleMultipliersReport2Serializer(BaseReportSerializer):
    transactions = SimpleMultipliersReport2TransactionSerializer(many=True, read_only=True)

    def create(self, validated_data):
        return BaseReport(**validated_data)

    def update(self, instance, validated_data):
        return instance
