from __future__ import unicode_literals

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from poms.api.fields import CurrentMasterUserDefault
from poms.instruments.models import Instrument
from poms.reports.models import BalanceReport, BalanceReportItem


class BaseReportItemSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True, source='pk', help_text=_('report item id'))


class BaseReportSerializer(serializers.Serializer):
    master_user = serializers.HiddenField(default=CurrentMasterUserDefault())
    begin_date = serializers.DateField(required=False, allow_null=True, help_text=_('some help text'))
    end_date = serializers.DateField(required=False, allow_null=True, help_text=_('some help text'))
    instruments = serializers.PrimaryKeyRelatedField(queryset=Instrument.objects.all(), required=False, many=True,
                                                     allow_null=True)
    count = serializers.IntegerField(read_only=True)


class BalanceReportItemSerializer(BaseReportItemSerializer):
    # instrument = serializers.IntegerField(required=False, help_text=_('Instrument'))
    # currency = serializers.IntegerField(required=False, help_text=_('currency'))
    instrument = serializers.PrimaryKeyRelatedField(read_only=True, help_text=_('Instrument'))
    currency = serializers.PrimaryKeyRelatedField(read_only=True, help_text=_('currency'))
    position_size_with_sign = serializers.FloatField(read_only=True, help_text=_('position size with sign'))

    if settings.DEV:
        currency_name = serializers.SerializerMethodField()
        instrument_name = serializers.SerializerMethodField()

    def create(self, validated_data):
        return BalanceReportItem(**validated_data)

    def update(self, instance, validated_data):
        return instance

    def get_currency_name(self, instance):
        return instance.currency.name if instance.currency else None

    def get_instrument_name(self, instance):
        return instance.instrument.name if instance.instrument else None


class BalanceReportSerializer(BaseReportSerializer):
    results = BalanceReportItemSerializer(many=True, read_only=True, help_text=_('some help text'))

    def create(self, validated_data):
        return BalanceReport(**validated_data)

    def update(self, instance, validated_data):
        return instance
