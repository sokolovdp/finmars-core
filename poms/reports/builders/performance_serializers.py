from __future__ import unicode_literals

from rest_framework import serializers

from poms.reports.builders.base_serializers import ReportPortfolioSerializer, \
    ReportAccountSerializer, ReportStrategy1Serializer, ReportStrategy2Serializer, ReportStrategy3Serializer, \
    CustomFieldViewSerializer
from poms.reports.builders.performance_item import PerformanceReport
from poms.reports.fields import CustomFieldField
from poms.users.fields import MasterUserField, HiddenMemberField


class PerformanceReportItemSerializer(serializers.Serializer):
    id = serializers.ReadOnlyField()

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('read_only', True)

        super(PerformanceReportItemSerializer, self).__init__(*args, **kwargs)


class PerformanceReportSerializer(serializers.Serializer):
    task_id = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    task_status = serializers.ReadOnlyField()

    master_user = MasterUserField()
    member = HiddenMemberField()

    custom_fields = CustomFieldField(many=True, allow_empty=True, allow_null=True, required=False)

    items = PerformanceReportItemSerializer(many=True, read_only=True)

    item_portfolios = ReportPortfolioSerializer(source='portfolios', many=True, read_only=True)
    item_accounts = ReportAccountSerializer(source='accounts', many=True, read_only=True)
    item_strategies1 = ReportStrategy1Serializer(source='strategies1', many=True, read_only=True)
    item_strategies2 = ReportStrategy2Serializer(source='strategies2', many=True, read_only=True)
    item_strategies3 = ReportStrategy3Serializer(source='strategies3', many=True, read_only=True)

    custom_fields_object = CustomFieldViewSerializer(source='custom_fields', read_only=True, many=True)

    def __init__(self, *args, **kwargs):
        super(PerformanceReportSerializer, self).__init__(*args, **kwargs)

    def create(self, validated_data):
        return PerformanceReport(**validated_data)

    def to_representation(self, instance):
        data = super(PerformanceReportSerializer, self).to_representation(instance)

        return data
