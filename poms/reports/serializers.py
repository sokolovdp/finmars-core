from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from poms.api.fields import CurrentMasterUserDefault
from poms.currencies.models import Currency
from poms.instruments.models import Instrument
from poms.reports.models import BalanceReport, BalanceReportItem, BalanceReportSummary, PLReportItem, PLReport


# ----------------------------------------------------------------------------------------------------------------------


class BaseReportItemSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True, source='pk', help_text=_('report item id'))


class BaseReportSerializer(serializers.Serializer):
    master_user = serializers.HiddenField(default=CurrentMasterUserDefault())
    begin_date = serializers.DateField(required=False, allow_null=True, help_text=_('some help text'))
    end_date = serializers.DateField(required=False, allow_null=True, help_text=_('some help text'))
    instruments = serializers.PrimaryKeyRelatedField(queryset=Instrument.objects.all(), required=False, many=True,
                                                     allow_null=True)


# ----------------------------------------------------------------------------------------------------------------------


class BalanceReportItemSerializer(BaseReportItemSerializer):
    # instrument = serializers.IntegerField(required=False, help_text=_('Instrument'))
    # currency = serializers.IntegerField(required=False, help_text=_('currency'))

    balance_position = serializers.FloatField(read_only=True, help_text=_('Position'))

    currency = serializers.PrimaryKeyRelatedField(read_only=True, help_text=_('Currency'))
    currency_name = serializers.CharField(read_only=True)
    currency_history = serializers.PrimaryKeyRelatedField(read_only=True, help_text=_('Currency history'))
    currency_fx_rate = serializers.FloatField(read_only=True)

    instrument = serializers.PrimaryKeyRelatedField(read_only=True, help_text=_('Instrument'))
    instrument_name = serializers.CharField(read_only=True)
    instrument_principal_pricing_ccy = serializers.CharField(read_only=True)
    instrument_price_multiplier = serializers.FloatField(read_only=True)
    instrument_accrued_pricing_ccy = serializers.CharField(read_only=True)
    instrument_accrued_multiplier = serializers.FloatField(read_only=True)

    price_history = serializers.PrimaryKeyRelatedField(read_only=True, help_text=_('price history'))
    instrument_principal_price = serializers.FloatField(read_only=True)
    instrument_accrued_price = serializers.FloatField(read_only=True)

    principal_value_intrument_principal_ccy = serializers.FloatField(read_only=True)
    accrued_value_intrument_principal_ccy = serializers.FloatField(read_only=True)

    instrument_principal_currency_history = serializers.PrimaryKeyRelatedField(read_only=True, help_text=_(''))
    instrument_principal_fx_rate = serializers.FloatField(read_only=True, help_text=_(''))
    instrument_accrued_currency_history = serializers.PrimaryKeyRelatedField(read_only=True, help_text=_(''))
    instrument_accrued_fx_rate = serializers.FloatField(read_only=True, help_text=_(''))

    market_value_system_ccy = serializers.FloatField(read_only=True)

    def create(self, validated_data):
        return BalanceReportItem(**validated_data)

    def update(self, instance, validated_data):
        return instance
    #
    # def get_instrument_name(self, instance):
    #     return getattr(instance.instrument, 'name', None)
    #     # return instance.instrument.name if instance.instrument else None
    #
    # def get_instrument_principal_pricing_ccy(self, instance):
    #     c = getattr(instance.instrument, 'pricing_currency', None)
    #     return getattr(c, 'name', None)
    #
    # def get_instrument_price_multiplier(self, instance):
    #     return getattr(instance.instrument, 'price_multiplier', None)
    #
    # def get_instrument_accrued_pricing_ccy(self, instance):
    #     c = getattr(instance.instrument, 'accrued_currency', None)
    #     return getattr(c, 'name', None)
    #
    # def get_instrument_accrued_multiplier(self, instance):
    #     return getattr(instance.instrument, 'accrued_multiplier', None)
    #
    # def get_instrument_principal_price(self, instance):
    #     return getattr(instance.price_history, 'principal_price', None)
    #
    # def get_instrument_accrued_price(self, instance):
    #     return getattr(instance.price_history, 'accrued_price', None)
    #
    # def get_currency_name(self, instance):
    #     return getattr(instance.currency, 'name', None)
    #     # return instance.currency.name if instance.currency else None
    #
    # def get_currency_fx_rate(self, instance):
    #     return getattr(instance.currency_history, 'fx_rate', None)


class BalanceReportSummarySerializer(serializers.Serializer):
    invested_value = serializers.FloatField(read_only=True, help_text=_('position size with sign'))
    current_value = serializers.FloatField(read_only=True, help_text=_('position size with sign'))
    p_and_l = serializers.FloatField(read_only=True, help_text=_('position size with sign'))

    def create(self, validated_data):
        return BalanceReportSummary(**validated_data)

    def update(self, instance, validated_data):
        return instance


class BalanceReportSerializer(BaseReportSerializer):
    currency = serializers.PrimaryKeyRelatedField(queryset=Currency.objects.all(), required=False, allow_null=True)
    results = BalanceReportItemSerializer(many=True, read_only=True,
                                          help_text=_('balance for currency and instruments'))
    summary = BalanceReportSummarySerializer(read_only=True,
                                             help_text=_('total in specified currency'))

    def create(self, validated_data):
        return BalanceReport(**validated_data)

    def update(self, instance, validated_data):
        return instance


# ----------------------------------------------------------------------------------------------------------------------



class PLReportItemSerializer(BaseReportItemSerializer):
    def create(self, validated_data):
        return PLReportItem(**validated_data)

    def update(self, instance, validated_data):
        return instance


class PLReportSerializer(BaseReportSerializer):
    results = BalanceReportItemSerializer(many=True, read_only=True,
                                          help_text=_('balance for currency and instruments'))

    def create(self, validated_data):
        return PLReport(**validated_data)

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
