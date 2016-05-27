from __future__ import unicode_literals

from rest_framework import serializers

from poms.common.serializers import PomsClassSerializer, ClassifierSerializerBase, ClassifierNodeSerializerBase
from poms.currencies.serializers import CurrencyField
from poms.instruments.fields import InstrumentClassifierField, InstrumentField, InstrumentAttributeTypeField
from poms.instruments.models import InstrumentClassifier, Instrument, PriceHistory, InstrumentClass, DailyPricingModel, \
    AccrualCalculationModel, PaymentSizeDetail, PeriodicityPeriod, CostMethod, InstrumentType, InstrumentAttributeType, \
    InstrumentAttribute, ManualPricingFormula, AccrualCalculationSchedule, InstrumentFactorSchedule, EventSchedule, \
    PricingPolicy
from poms.obj_attrs.serializers import AttributeSerializerBase, AttributeTypeSerializerBase, \
    ModelWithAttributesSerializer
from poms.obj_perms.serializers import ModelWithObjectPermissionSerializer
from poms.tags.fields import TagField
from poms.transactions.fields import TransactionTypeField
from poms.users.fields import MasterUserField


class InstrumentClassSerializer(PomsClassSerializer):
    class Meta(PomsClassSerializer.Meta):
        model = InstrumentClass


class DailyPricingModelSerializer(PomsClassSerializer):
    class Meta(PomsClassSerializer.Meta):
        model = DailyPricingModel


class AccrualCalculationModelSerializer(PomsClassSerializer):
    class Meta(PomsClassSerializer.Meta):
        model = AccrualCalculationModel


class PaymentSizeDetailSerializer(PomsClassSerializer):
    class Meta(PomsClassSerializer.Meta):
        model = PaymentSizeDetail


class PeriodicityPeriodSerializer(PomsClassSerializer):
    class Meta(PomsClassSerializer.Meta):
        model = PeriodicityPeriod


class CostMethodSerializer(PomsClassSerializer):
    class Meta(PomsClassSerializer.Meta):
        model = CostMethod


class PricingPolicySerializer(serializers.ModelSerializer):
    master_user = MasterUserField()

    class Meta:
        model = PricingPolicy
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes',
                  'expr']


class InstrumentClassifierSerializer(ClassifierSerializerBase):
    class Meta(ClassifierSerializerBase.Meta):
        model = InstrumentClassifier


class InstrumentClassifierNodeSerializer(ClassifierNodeSerializerBase):
    url = serializers.HyperlinkedIdentityField(view_name='instrumentclassifiernode-detail')

    class Meta(ClassifierNodeSerializerBase.Meta):
        model = InstrumentClassifier


class InstrumentTypeSerializer(ModelWithObjectPermissionSerializer):
    master_user = MasterUserField()
    tags = TagField(many=True)

    class Meta:
        model = InstrumentType
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes',
                  'instrument_class', 'tags']


class InstrumentAttributeTypeSerializer(AttributeTypeSerializerBase, ModelWithObjectPermissionSerializer):
    # classifier_root = InstrumentClassifierRootField(required=False, allow_null=True)
    classifiers = InstrumentClassifierSerializer(required=False, allow_null=True, many=True)

    class Meta(AttributeTypeSerializerBase.Meta):
        model = InstrumentAttributeType
        fields = AttributeTypeSerializerBase.Meta.fields + ['classifiers']
        # update_read_only_fields = AttributeTypeSerializerBase.Meta.update_read_only_fields + ['classifier_root']


class ManualPricingFormulaSerializer(serializers.ModelSerializer):
    # instrument = InstrumentField()

    class Meta:
        model = ManualPricingFormula
        fields = ['id', 'instrument', 'pricing_policy', 'expr', 'notes']


class AccrualCalculationScheduleSerializer(serializers.ModelSerializer):
    # instrument = InstrumentField()

    class Meta:
        model = AccrualCalculationSchedule
        fields = ['id', 'instrument', 'accrual_start_date', 'first_payment_date', 'accrual_size',
                  'accrual_calculation_model', 'periodicity_period', 'notes']


class InstrumentFactorScheduleSerializer(serializers.ModelSerializer):
    # instrument = InstrumentField()

    class Meta:
        model = InstrumentFactorSchedule
        fields = ['id', 'instrument', 'effective_date', 'factor_value']


class EventScheduleSerializer(serializers.ModelSerializer):
    # instrument = InstrumentField()
    transaction_types = TransactionTypeField(many=True)

    class Meta:
        model = EventSchedule
        fields = ['id', 'instrument', 'transaction_types', 'event_class', 'notification_class',
                  'notification_date', 'effective_date']


class InstrumentAttributeSerializer(AttributeSerializerBase):
    attribute_type = InstrumentAttributeTypeField()
    classifier = InstrumentClassifierField(required=False, allow_null=True)

    class Meta(AttributeSerializerBase.Meta):
        model = InstrumentAttribute
        fields = AttributeSerializerBase.Meta.fields + ['attribute_type', 'classifier']


class InstrumentSerializer(ModelWithAttributesSerializer, ModelWithObjectPermissionSerializer):
    master_user = MasterUserField()
    pricing_currency = CurrencyField(read_only=False)
    accrued_currency = CurrencyField(read_only=False)

    manual_pricing_formulas = ManualPricingFormulaSerializer(many=True, required=False, allow_null=True)
    accrual_calculation_schedules = AccrualCalculationScheduleSerializer(many=True, required=False, allow_null=True)
    factor_schedules = InstrumentFactorScheduleSerializer(many=True, required=False, allow_null=True)
    event_schedules = EventScheduleSerializer(many=True, required=False, allow_null=True)

    attributes = InstrumentAttributeSerializer(many=True)
    tags = TagField(many=True)

    class Meta:
        model = Instrument
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes', 'is_active',
                  'pricing_currency', 'price_multiplier', 'accrued_currency', 'accrued_multiplier',
                  'daily_pricing_model', 'payment_size_detail', 'default_price', 'default_accrued',
                  'manual_pricing_formulas', 'accrual_calculation_schedules', 'factor_schedules', 'event_schedules',
                  'attributes', 'tags']


class PriceHistorySerializer(serializers.ModelSerializer):
    instrument = InstrumentField()

    class Meta:
        model = PriceHistory
        fields = ['url', 'id', 'instrument', 'date', 'principal_price', 'accrued_price', 'factor']
