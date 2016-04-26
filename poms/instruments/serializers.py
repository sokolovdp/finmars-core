from __future__ import unicode_literals

from rest_framework import serializers

from poms.common.serializers import PomsClassSerializer, ClassifierSerializerBase
from poms.currencies.serializers import CurrencyField
from poms.instruments.fields import InstrumentClassifierField, InstrumentField, InstrumentClassifierRootField, \
    InstrumentAttributeTypeField
from poms.instruments.models import InstrumentClassifier, Instrument, PriceHistory, InstrumentClass, DailyPricingModel, \
    AccrualCalculationModel, PaymentSizeDetail, PeriodicityPeriod, CostMethod, InstrumentType, InstrumentAttributeType, \
    InstrumentAttribute, ManualPricingFormula, AccrualCalculationSchedule, InstrumentFactorSchedule, EventSchedule, \
    PricingPolicy
from poms.obj_attrs.serializers import AttributeSerializerBase, AttributeTypeSerializerBase, \
    ModelWithAttributesSerializer
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
    # parent = InstrumentClassifierField(required=False, allow_null=True)
    # children = InstrumentClassifierField(many=True, required=False, read_only=False)

    class Meta(ClassifierSerializerBase.Meta):
        model = InstrumentClassifier


class InstrumentTypeSerializer(serializers.ModelSerializer):
    master_user = MasterUserField()
    tags = TagField(many=True)

    class Meta:
        model = InstrumentType
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes',
                  'instrument_class', 'tags']


class InstrumentAttributeTypeSerializer(AttributeTypeSerializerBase):
    classifier_root = InstrumentClassifierRootField(required=False, allow_null=True)

    class Meta(AttributeTypeSerializerBase.Meta):
        model = InstrumentAttributeType
        fields = AttributeTypeSerializerBase.Meta.fields + ['classifier_root']
        update_read_only_fields = AttributeTypeSerializerBase.Meta.update_read_only_fields + ['classifier_root']


class InstrumentAttributeSerializer(AttributeSerializerBase):
    attribute_type = InstrumentAttributeTypeField()
    classifier = InstrumentClassifierField(required=False, allow_null=True)

    class Meta(AttributeSerializerBase.Meta):
        model = InstrumentAttribute
        fields = AttributeSerializerBase.Meta.fields + ['attribute_type', 'classifier']


class InstrumentSerializer(ModelWithAttributesSerializer):
    master_user = MasterUserField()
    pricing_currency = CurrencyField(read_only=False)
    accrued_currency = CurrencyField(read_only=False)
    attributes = InstrumentAttributeSerializer(many=True)
    tags = TagField(many=True)

    class Meta:
        model = Instrument
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes', 'is_active',
                  'pricing_currency', 'price_multiplier', 'accrued_currency', 'accrued_multiplier',
                  'daily_pricing_model', 'payment_size_detail', 'default_price', 'default_accrued',
                  'attributes', 'tags']


class PriceHistorySerializer(serializers.ModelSerializer):
    instrument = InstrumentField()

    class Meta:
        model = PriceHistory
        fields = ['url', 'id', 'instrument', 'date', 'principal_price', 'accrued_price', 'factor']


class ManualPricingFormulaSerializer(serializers.ModelSerializer):
    instrument = InstrumentField()

    class Meta:
        model = ManualPricingFormula
        fields = ['url', 'id', 'instrument', 'pricing_policy', 'expr', 'notes']


class AccrualCalculationScheduleSerializer(serializers.ModelSerializer):
    instrument = InstrumentField()

    class Meta:
        model = AccrualCalculationSchedule
        fields = ['url', 'id', 'instrument', 'accrual_start_date', 'first_payment_date', 'accrual_size',
                  'accrual_calculation_model', 'periodicity_period', 'notes']


class InstrumentFactorScheduleSerializer(serializers.ModelSerializer):
    instrument = InstrumentField()

    class Meta:
        model = InstrumentFactorSchedule
        fields = ['url', 'id', 'instrument', 'effective_date', 'factor_value']


class EventScheduleSerializer(serializers.ModelSerializer):
    instrument = InstrumentField()
    transaction_types = TransactionTypeField(many=True)

    class Meta:
        model = EventSchedule
        fields = ['url', 'id', 'instrument', 'transaction_types', 'event_class', 'notification_class',
                  'notification_date', 'effective_date']
