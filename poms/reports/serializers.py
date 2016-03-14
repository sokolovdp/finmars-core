from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from poms.api.fields import CurrentMasterUserDefault
from poms.instruments.models import Instrument
from poms.instruments.serializers import InstrumentField
from poms.reports.models import BalanceReport, BalanceReportItem, BalanceReportSummary, PLReportInstrument, PLReport, \
    PLReportSummary, CostReport

# ----------------------------------------------------------------------------------------------------------------------
from poms.transactions.models import Transaction


class BaseReportItemSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True, source='pk', help_text=_('report item id'))


class BaseReportSerializer(serializers.Serializer):
    master_user = serializers.HiddenField(default=CurrentMasterUserDefault())
    begin_date = serializers.DateField(required=False, allow_null=True, help_text=_('some help text'))
    end_date = serializers.DateField(required=False, allow_null=True, help_text=_('some help text'))
    instruments = InstrumentField(many=True, required=False, allow_null=True)


# ----------------------------------------------------------------------------------------------------------------------


class BalanceReportItemSerializer(BaseReportItemSerializer):
    # instrument = serializers.IntegerField(required=False, help_text=_('Instrument'))
    # currency = serializers.IntegerField(required=False, help_text=_('currency'))

    balance_position = serializers.FloatField(read_only=True, help_text=_('Position'))

    currency = serializers.PrimaryKeyRelatedField(read_only=True, help_text=_('Currency'))
    currency_name = serializers.SerializerMethodField()
    currency_history = serializers.PrimaryKeyRelatedField(read_only=True, help_text=_('Currency history'))
    currency_fx_rate = serializers.FloatField(read_only=True)

    instrument = serializers.PrimaryKeyRelatedField(read_only=True, help_text=_('Instrument'))
    instrument_name = serializers.SerializerMethodField()
    instrument_principal_pricing_ccy = serializers.SerializerMethodField()
    instrument_price_multiplier = serializers.FloatField(read_only=True)
    instrument_accrued_pricing_ccy = serializers.SerializerMethodField()
    instrument_accrued_multiplier = serializers.FloatField(read_only=True)

    price_history = serializers.PrimaryKeyRelatedField(read_only=True, help_text=_('price history'))
    instrument_principal_price = serializers.FloatField(read_only=True)
    instrument_accrued_price = serializers.FloatField(read_only=True)

    principal_value_instrument_principal_ccy = serializers.FloatField(read_only=True)
    accrued_value_instrument_principal_ccy = serializers.FloatField(read_only=True)

    instrument_principal_currency_history = serializers.PrimaryKeyRelatedField(read_only=True, help_text=_(''))
    instrument_principal_fx_rate = serializers.FloatField(read_only=True, help_text=_(''))
    instrument_accrued_currency_history = serializers.PrimaryKeyRelatedField(read_only=True, help_text=_(''))
    instrument_accrued_fx_rate = serializers.FloatField(read_only=True, help_text=_(''))

    principal_value_system_ccy = serializers.FloatField(read_only=True)
    accrued_value_system_ccy = serializers.FloatField(read_only=True)

    market_value_system_ccy = serializers.FloatField(read_only=True)

    def create(self, validated_data):
        return BalanceReportItem(**validated_data)

    def update(self, instance, validated_data):
        return instance

    def get_currency_name(self, instance):
        return getattr(instance.currency, 'name', None)

    def get_instrument_name(self, instance):
        return getattr(instance.instrument, 'name', None)

    def get_instrument_principal_pricing_ccy(self, instance):
        instrument = getattr(instance, 'instrument', None)
        pricing_currency = getattr(instrument, 'pricing_currency', None)
        return getattr(pricing_currency, 'name', None)

    def get_instrument_accrued_pricing_ccy(self, instance):
        instrument = getattr(instance, 'instrument', None)
        accrued_currency = getattr(instrument, 'accrued_currency', None)
        return getattr(accrued_currency, 'name', None)


class BalanceReportSummarySerializer(serializers.Serializer):
    invested_value_system_ccy = serializers.FloatField(read_only=True, help_text=_('invested value in system currency'))
    current_value_system_ccy = serializers.FloatField(read_only=True, help_text=_('current value in system currency'))
    p_l_system_ccy = serializers.FloatField(read_only=True, help_text=_('position size with sign'))

    def create(self, validated_data):
        return BalanceReportSummary(**validated_data)

    def update(self, instance, validated_data):
        return instance


class BalanceReportSerializer(BaseReportSerializer):
    invested_items = BalanceReportItemSerializer(many=True, read_only=True,
                                                 help_text=_('invested'))
    items = BalanceReportItemSerializer(many=True, read_only=True,
                                        help_text=_('items'))
    summary = BalanceReportSummarySerializer(read_only=True,
                                             help_text=_('total in specified currency'))

    def create(self, validated_data):
        return BalanceReport(**validated_data)

    def update(self, instance, validated_data):
        return instance


# ----------------------------------------------------------------------------------------------------------------------


class PLReportTransactionSerializer(serializers.ModelSerializer):
    transaction_class = serializers.PrimaryKeyRelatedField(read_only=True)
    transaction_class_code = serializers.SerializerMethodField()

    transaction_currency = serializers.PrimaryKeyRelatedField(read_only=True)
    transaction_currency_name = serializers.SerializerMethodField()
    transaction_currency_history = serializers.SerializerMethodField()
    transaction_currency_fx_rate = serializers.FloatField(read_only=True)

    instrument = serializers.PrimaryKeyRelatedField(read_only=True)
    instrument_name = serializers.SerializerMethodField()

    settlement_currency = serializers.PrimaryKeyRelatedField(read_only=True)
    settlement_currency_name = serializers.SerializerMethodField()
    settlement_currency_history = serializers.SerializerMethodField()
    settlement_currency_fx_rate = serializers.FloatField(read_only=True)

    position_size_with_sign = serializers.FloatField(read_only=True)

    cash_consideration = serializers.FloatField(read_only=True)
    principal_with_sign = serializers.FloatField(read_only=True)
    carry_with_sign = serializers.FloatField(read_only=True)
    overheads_with_sign = serializers.FloatField(read_only=True)

    principal_with_sign_system_ccy = serializers.FloatField(read_only=True)
    carry_with_sign_system_ccy = serializers.FloatField(read_only=True)
    overheads_with_sign_system_ccy = serializers.FloatField(read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id',
            'transaction_class', 'transaction_class_code',
            'transaction_currency', 'transaction_currency_name',
            'transaction_currency_history', 'transaction_currency_fx_rate',
            'instrument', 'instrument_name',
            'settlement_currency', 'settlement_currency_name',
            'settlement_currency_history', 'settlement_currency_fx_rate',
            'position_size_with_sign',
            'cash_consideration', 'principal_with_sign', 'carry_with_sign', 'overheads_with_sign',
            'principal_with_sign_system_ccy', 'carry_with_sign_system_ccy', 'overheads_with_sign_system_ccy',
        ]

    def get_transaction_class_code(self, instance):
        return getattr(instance.transaction_class, 'code', None)

    def get_transaction_currency_name(self, instance):
        return getattr(instance.transaction_currency, 'name', None)

    def get_instrument_name(self, instance):
        return getattr(instance.instrument, 'name', None)

    def get_settlement_currency_name(self, instance):
        return getattr(instance.settlement_currency, 'name', None)

    def get_transaction_currency_history(self, instance):
        h = getattr(instance, 'transaction_currency_history', None)
        return getattr(h, 'pk', None)

    def get_settlement_currency_history(self, instance):
        h = getattr(instance, 'settlement_currency_history', None)
        return getattr(h, 'pk', None)


class PLReportInstrumentSerializer(BaseReportItemSerializer):
    instrument = serializers.PrimaryKeyRelatedField(read_only=True)
    instrument_name = serializers.SerializerMethodField()

    principal_with_sign_system_ccy = serializers.FloatField(read_only=True)
    carry_with_sign_system_ccy = serializers.FloatField(read_only=True)
    overheads_with_sign_system_ccy = serializers.FloatField(read_only=True)
    total_system_ccy = serializers.FloatField(read_only=True)

    def create(self, validated_data):
        return PLReportInstrument(**validated_data)

    def update(self, instance, validated_data):
        return instance

    def get_instrument_name(self, instance):
        return getattr(instance.instrument, 'name', None)


class PLReportSummarySerializer(serializers.Serializer):
    principal_with_sign_system_ccy = serializers.FloatField(read_only=True,
                                                            help_text=_(''))
    carry_with_sign_system_ccy = serializers.FloatField(read_only=True,
                                                        help_text=_(''))
    overheads_with_sign_system_ccy = serializers.FloatField(read_only=True,
                                                            help_text=_(''))
    total_system_ccy = serializers.FloatField(read_only=True,
                                              help_text=_(''))

    def create(self, validated_data):
        return PLReportSummary(**validated_data)

    def update(self, instance, validated_data):
        return instance


class PLReportSerializer(BaseReportSerializer):
    transactions = PLReportTransactionSerializer(many=True, read_only=True)
    items = PLReportInstrumentSerializer(many=True, read_only=True,
                                         help_text=_('items'))
    summary = PLReportSummarySerializer(read_only=True,
                                        help_text=_('total in specified currency'))

    def create(self, validated_data):
        return PLReport(**validated_data)

    def update(self, instance, validated_data):
        return instance


# ----------------------------------------------------------------------------------------------------------------------


class CostTransactionSerializer(serializers.ModelSerializer):
    transaction_class = serializers.PrimaryKeyRelatedField(read_only=True)
    transaction_class_code = serializers.SerializerMethodField()

    transaction_currency = serializers.PrimaryKeyRelatedField(read_only=True)
    transaction_currency_name = serializers.SerializerMethodField()

    instrument = serializers.PrimaryKeyRelatedField(read_only=True)
    instrument_name = serializers.SerializerMethodField()
    settlement_currency = serializers.PrimaryKeyRelatedField(read_only=True)
    settlement_currency_name = serializers.SerializerMethodField()

    position_size_with_sign = serializers.FloatField(read_only=True)

    cash_consideration = serializers.FloatField(read_only=True)
    principal_with_sign = serializers.FloatField(read_only=True)
    carry_with_sign = serializers.FloatField(read_only=True)
    overheads_with_sign = serializers.FloatField(read_only=True)

    avco_multiplier = serializers.FloatField(read_only=True)
    fifo_multiplier = serializers.FloatField(read_only=True)
    rolling_position = serializers.FloatField(read_only=True)

    remaining_position = serializers.FloatField(read_only=True)
    remaining_position_cost_settlement_ccy = serializers.FloatField(read_only=True)
    remaining_position_cost_system_ccy = serializers.FloatField(read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id',
            'transaction_class', 'transaction_class_code',
            'transaction_currency', 'transaction_currency_name',
            'instrument', 'instrument_name',
            'settlement_currency', 'settlement_currency_name',
            'position_size_with_sign',
            'cash_consideration', 'principal_with_sign', 'carry_with_sign', 'overheads_with_sign',
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
    instrument = serializers.PrimaryKeyRelatedField(read_only=True)
    instrument_name = serializers.SerializerMethodField()

    pricing_currency_name = serializers.SerializerMethodField(read_only=True)
    pricing_currency_fx_rate = serializers.SerializerMethodField()
    price_multiplier = serializers.SerializerMethodField()
    position = serializers.FloatField(read_only=True)
    cost_system_ccy = serializers.FloatField(read_only=True)
    cost_instrument_ccy = serializers.FloatField(read_only=True)
    cost_price = serializers.FloatField(read_only=True)
    cost_price_adjusted = serializers.FloatField(read_only=True)

    def create(self, validated_data):
        return PLReportInstrument(**validated_data)

    def update(self, instance, validated_data):
        return instance

    def get_instrument_name(self, instance):
        return getattr(instance.instrument, 'name', None)

    def get_pricing_currency_name(self, instance):
        pricing_currency = getattr(instance.instrument, 'pricing_currency', None)
        return getattr(pricing_currency, 'name', None)

    def get_pricing_currency_fx_rate(self, instance):
        pricing_currency_fx_rate = getattr(instance.instrument, 'pricing_currency_fx_rate', None)
        return pricing_currency_fx_rate

    def get_price_multiplier(self, instance):
        return getattr(instance.instrument, 'price_multiplier', None)


class CostReportSerializer(BaseReportSerializer):
    multiplier_class = serializers.ChoiceField(default='avco', choices=[['avco', _('avco')], ['fifo', _('fifo')]])
    transactions = CostTransactionSerializer(many=True, read_only=True, help_text=_('Transactions with miltipliers'))
    items = CostReportInstrumentSerializer(many=True, read_only=True)

    def create(self, validated_data):
        return CostReport(**validated_data)

    def update(self, instance, validated_data):
        return instance


# ----------------------------------------------------------------------------------------------------------------------


class YTMTransactionSerializer(serializers.ModelSerializer):
    transaction_class = serializers.PrimaryKeyRelatedField(read_only=True)
    transaction_class_code = serializers.SerializerMethodField()

    transaction_currency = serializers.PrimaryKeyRelatedField(read_only=True)
    transaction_currency_name = serializers.SerializerMethodField()

    instrument = serializers.PrimaryKeyRelatedField(read_only=True)
    instrument_name = serializers.SerializerMethodField()
    settlement_currency = serializers.PrimaryKeyRelatedField(read_only=True)
    settlement_currency_name = serializers.SerializerMethodField()

    position_size_with_sign = serializers.FloatField(read_only=True)

    avco_multiplier = serializers.FloatField(read_only=True)
    fifo_multiplier = serializers.FloatField(read_only=True)
    rolling_position = serializers.FloatField(read_only=True)

    ytm = serializers.FloatField(read_only=True)
    time_invested = serializers.FloatField(read_only=True)
    remaining_position = serializers.FloatField(read_only=True)
    remaining_position_percent = serializers.FloatField(read_only=True)
    weighted_ytm = serializers.FloatField(read_only=True)
    weighted_time_invested = serializers.FloatField(read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id',
            'transaction_class', 'transaction_class_code',
            'transaction_currency', 'transaction_currency_name',
            'instrument', 'instrument_name',
            'settlement_currency', 'settlement_currency_name',
            'position_size_with_sign',
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
    instrument = serializers.PrimaryKeyRelatedField(read_only=True)
    instrument_name = serializers.SerializerMethodField()

    position = serializers.FloatField(read_only=True)
    ytm = serializers.FloatField(read_only=True)
    time_invested = serializers.FloatField(read_only=True)

    def create(self, validated_data):
        return PLReportInstrument(**validated_data)

    def update(self, instance, validated_data):
        return instance

    def get_instrument_name(self, instance):
        return getattr(instance.instrument, 'name', None)


class YTMReportSerializer(BaseReportSerializer):
    multiplier_class = serializers.ChoiceField(default='avco', choices=[['avco', _('avco')], ['fifo', _('fifo')]])
    transactions = YTMTransactionSerializer(many=True, read_only=True, help_text=_('Transactions with miltipliers'))
    items = YTMReportInstrumentSerializer(many=True, read_only=True)

    def create(self, validated_data):
        return CostReport(**validated_data)

    def update(self, instance, validated_data):
        return instance


# ----------------------------------------------------------------------------------------------------------------------


class SimpleMultipliersReportItemSerializer(BaseReportItemSerializer):
    instrument = serializers.PrimaryKeyRelatedField(read_only=True, help_text=_('Instrument'))
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
    results = SimpleMultipliersReportItemSerializer(many=True, read_only=True, help_text=_('some help text'))

    def create(self, validated_data):
        return BalanceReport(**validated_data)

    def update(self, instance, validated_data):
        return instance
