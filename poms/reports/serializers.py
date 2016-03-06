from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from poms.reports.models import BalanceReport, BalanceReportItem


class BaseReportItemSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, source='pk', help_text=_('report item id'))


class BaseReportSerializer(serializers.Serializer):
    begin_date = serializers.DateField(allow_null=True, required=False, help_text=_('some help text'))
    end_date = serializers.DateField(allow_null=True, required=False, help_text=_('some help text'))


class BalanceReportItemSerializer(BaseReportItemSerializer):
    instrument = serializers.IntegerField(required=False, help_text=_('Instrument'))

    def create(self, validated_data):
        return BalanceReportItem(**validated_data)

    def update(self, instance, validated_data):
        return instance


class BalanceReportSerializer(BaseReportSerializer):
    items = BalanceReportItemSerializer(many=True, read_only=True, help_text=_('some help text'))

    def create(self, validated_data):
        return BalanceReport(**validated_data)

    def update(self, instance, validated_data):
        return instance
