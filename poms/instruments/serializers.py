from __future__ import unicode_literals

from datetime import timedelta

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from poms.common.fields import ExpressionField, FloatEvalField
from poms.common.serializers import PomsClassSerializer, AbstractClassifierSerializer, AbstractClassifierNodeSerializer, \
    ModelWithUserCodeSerializer, ReadonlyModelWithNameSerializer, ReadonlyModelSerializer, ReadonlyNamedModelSerializer
from poms.common.utils import date_now
from poms.currencies.fields import CurrencyDefault
from poms.currencies.serializers import CurrencyField
from poms.instruments.fields import InstrumentClassifierField, InstrumentField, InstrumentAttributeTypeField, \
    InstrumentTypeField, PricingPolicyField, InstrumentTypeDefault
from poms.instruments.models import InstrumentClassifier, Instrument, PriceHistory, InstrumentClass, DailyPricingModel, \
    AccrualCalculationModel, PaymentSizeDetail, Periodicity, CostMethod, InstrumentType, InstrumentAttributeType, \
    InstrumentAttribute, ManualPricingFormula, AccrualCalculationSchedule, InstrumentFactorSchedule, EventSchedule, \
    PricingPolicy, EventScheduleAction, EventScheduleConfig
from poms.integrations.fields import PriceDownloadSchemeField
from poms.obj_attrs.serializers import AbstractAttributeSerializer, AbstractAttributeTypeSerializer, \
    ModelWithAttributesSerializer
from poms.obj_perms.serializers import ModelWithObjectPermissionSerializer, \
    ReadonlyNamedModelWithObjectPermissionSerializer
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


class PeriodicitySerializer(PomsClassSerializer):
    class Meta(PomsClassSerializer.Meta):
        model = Periodicity


class CostMethodSerializer(PomsClassSerializer):
    class Meta(PomsClassSerializer.Meta):
        model = CostMethod


class PricingPolicySerializer(ModelWithUserCodeSerializer):
    master_user = MasterUserField()
    expr = ExpressionField(allow_blank=False, allow_null=False)

    class Meta:
        model = PricingPolicy
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes', 'expr']


class InstrumentClassifierSerializer(AbstractClassifierSerializer):
    class Meta(AbstractClassifierSerializer.Meta):
        model = InstrumentClassifier


class InstrumentClassifierNodeSerializer(AbstractClassifierNodeSerializer):
    class Meta(AbstractClassifierNodeSerializer.Meta):
        model = InstrumentClassifier


class InstrumentTypeSerializer(ModelWithObjectPermissionSerializer, ModelWithUserCodeSerializer):
    master_user = MasterUserField()
    instrument_class_object = ReadonlyModelWithNameSerializer(source='instrument_class')
    one_off_event = TransactionTypeField(allow_null=True, required=False)
    one_off_event_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='one_off_event')
    regular_event = TransactionTypeField(allow_null=True, required=False)
    regular_event_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='regular_event')
    factor_same = TransactionTypeField(allow_null=True, required=False)
    factor_same_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='factor_same')
    factor_up = TransactionTypeField(allow_null=True, required=False)
    factor_up_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='factor_up')
    factor_down = TransactionTypeField(allow_null=True, required=False)
    factor_down_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='factor_down')
    tags = TagField(many=True, required=False, allow_null=True)
    tags_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='tags', many=True)

    class Meta:
        model = InstrumentType
        fields = [
            'url', 'id', 'master_user', 'instrument_class', 'instrument_class_object',
            'user_code', 'name', 'short_name', 'public_name',
            'notes', 'is_default', 'is_deleted', 'one_off_event', 'one_off_event_object',
            'regular_event', 'regular_event_object', 'factor_same', 'factor_same_object',
            'factor_up', 'factor_up_object', 'factor_down', 'factor_down_object',
            'tags', 'tags_object',
        ]

    def validate(self, attrs):
        instrument_class = attrs['instrument_class']
        one_off_event = attrs.get('one_off_event', None)
        regular_event = attrs.get('regular_event', None)

        errors = {}
        if instrument_class.has_one_off_event and one_off_event is None:
            errors['one_off_event'] = self.fields['one_off_event'].error_messages['required']
        if instrument_class.has_regular_event and regular_event is None:
            errors['regular_event'] = self.fields['regular_event'].error_messages['required']

        if errors:
            raise ValidationError(errors)

        return attrs


# class InstrumentTypeBulkObjectPermissionSerializer(AbstractBulkObjectPermissionSerializer):
#     content_objects = InstrumentTypeField(many=True, allow_null=False, allow_empty=False)
#
#     class Meta:
#         model = InstrumentType


class InstrumentAttributeTypeSerializer(AbstractAttributeTypeSerializer):
    classifiers = InstrumentClassifierSerializer(required=False, allow_null=True, many=True)

    class Meta(AbstractAttributeTypeSerializer.Meta):
        model = InstrumentAttributeType
        fields = AbstractAttributeTypeSerializer.Meta.fields + ['classifiers']


# class InstrumentAttributeTypeBulkObjectPermissionSerializer(AbstractBulkObjectPermissionSerializer):
#     content_objects = InstrumentAttributeTypeField(many=True, allow_null=False, allow_empty=False)
#
#     class Meta:
#         model = InstrumentAttributeType


class ManualPricingFormulaSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=False, required=False, allow_null=True)
    pricing_policy = PricingPolicyField(allow_null=False)

    # instrument = InstrumentField()

    class Meta:
        model = ManualPricingFormula
        fields = ['id', 'pricing_policy', 'expr', 'notes']


class AccrualCalculationScheduleSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=False, required=False, allow_null=True)
    accrual_calculation_model_object = ReadonlyModelWithNameSerializer(source='accrual_calculation_model')
    periodicity_object = ReadonlyModelWithNameSerializer(source='periodicity')

    class Meta:
        model = AccrualCalculationSchedule
        fields = [
            'id', 'accrual_start_date', 'first_payment_date', 'accrual_size', 'accrual_calculation_model',
            'accrual_calculation_model_object', 'periodicity', 'periodicity_object', 'periodicity_n', 'notes']


class InstrumentFactorScheduleSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=False, required=False, allow_null=True)

    # instrument = InstrumentField()

    class Meta:
        model = InstrumentFactorSchedule
        fields = ['id', 'effective_date', 'factor_value']


class EventScheduleActionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=False, required=False, allow_null=True)
    transaction_type = TransactionTypeField()
    transaction_type_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='transaction_type')

    class Meta:
        model = EventScheduleAction
        fields = ['id', 'transaction_type', 'transaction_type_object', 'text', 'is_sent_to_pending',
                  'is_book_automatic', 'button_position']


class EventScheduleSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=False, required=False, allow_null=True)
    event_class_object = ReadonlyModelWithNameSerializer(source='event_class')
    notification_class_object = ReadonlyModelWithNameSerializer(source='notification_class')
    periodicity_object = ReadonlyModelWithNameSerializer(source='periodicity')
    actions = EventScheduleActionSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = EventSchedule
        fields = [
            'id', 'name', 'description', 'event_class', 'event_class_object', 'notification_class',
            'notification_class_object', 'effective_date', 'notify_in_n_days', 'periodicity', 'periodicity_object',
            'periodicity_n', 'final_date', 'is_auto_generated', 'actions'
        ]
        read_only_fields = ['is_auto_generated']


class InstrumentAttributeSerializer(AbstractAttributeSerializer):
    attribute_type = InstrumentAttributeTypeField()
    classifier = InstrumentClassifierField(required=False, allow_null=True)

    class Meta(AbstractAttributeSerializer.Meta):
        model = InstrumentAttribute
        fields = AbstractAttributeSerializer.Meta.fields + ['attribute_type', 'classifier']


class InstrumentSerializer(ModelWithAttributesSerializer, ModelWithObjectPermissionSerializer,
                           ModelWithUserCodeSerializer):
    master_user = MasterUserField()
    instrument_type = InstrumentTypeField(default=InstrumentTypeDefault())
    instrument_type_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='instrument_type')
    pricing_currency = CurrencyField(default=CurrencyDefault())
    pricing_currency_object = ReadonlyNamedModelSerializer(source='pricing_currency')
    accrued_currency = CurrencyField(default=CurrencyDefault())
    accrued_currency_object = ReadonlyNamedModelSerializer(source='accrued_currency')
    payment_size_detail_object = ReadonlyModelWithNameSerializer(source='payment_size_detail')
    daily_pricing_model_object = ReadonlyModelWithNameSerializer(source='daily_pricing_model')
    price_download_scheme = PriceDownloadSchemeField(allow_null=True)
    price_download_scheme_object = ReadonlyModelSerializer(source='price_download_scheme', fields=['scheme_name'])

    manual_pricing_formulas = ManualPricingFormulaSerializer(many=True, required=False, allow_null=True)
    accrual_calculation_schedules = AccrualCalculationScheduleSerializer(many=True, required=False, allow_null=True)
    factor_schedules = InstrumentFactorScheduleSerializer(many=True, required=False, allow_null=True)
    event_schedules = EventScheduleSerializer(many=True, required=False, allow_null=True)

    attributes = InstrumentAttributeSerializer(many=True, required=False, allow_null=True)
    tags = TagField(many=True, required=False, allow_null=True)
    tags_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='tags', many=True)

    class Meta:
        model = Instrument
        fields = [
            'url', 'id', 'master_user', 'instrument_type', 'instrument_type_object', 'user_code', 'name', 'short_name',
            'public_name', 'notes', 'is_active', 'is_deleted',
            'pricing_currency', 'pricing_currency_object', 'price_multiplier',
            'accrued_currency', 'accrued_currency_object', 'accrued_multiplier',
            'payment_size_detail', 'payment_size_detail_object', 'default_price', 'default_accrued',
            'user_text_1', 'user_text_2', 'user_text_3',
            'reference_for_pricing', 'daily_pricing_model', 'daily_pricing_model_object',
            'price_download_scheme', 'price_download_scheme_object',
            'maturity_date',
            'manual_pricing_formulas', 'accrual_calculation_schedules', 'factor_schedules', 'event_schedules',
            'attributes', 'tags', 'tags_object'
        ]

    def create(self, validated_data):
        manual_pricing_formulas = validated_data.pop('manual_pricing_formulas', None)
        accrual_calculation_schedules = validated_data.pop('accrual_calculation_schedules', None)
        factor_schedules = validated_data.pop('factor_schedules', None)
        event_schedules = validated_data.pop('event_schedules', None)

        instance = super(InstrumentSerializer, self).create(validated_data)

        self.save_manual_pricing_formulas(instance, True, manual_pricing_formulas)
        self.save_accrual_calculation_schedules(instance, True, accrual_calculation_schedules)
        self.save_factor_schedules(instance, True, factor_schedules)
        self.save_event_schedules(instance, True, event_schedules)

        self.rebuild_event_schedules(instance, True)

        return instance

    def update(self, instance, validated_data):
        manual_pricing_formulas = validated_data.pop('manual_pricing_formulas', None)
        accrual_calculation_schedules = validated_data.pop('accrual_calculation_schedules', None)
        factor_schedules = validated_data.pop('factor_schedules', None)
        event_schedules = validated_data.pop('event_schedules', None)

        instance = super(InstrumentSerializer, self).update(instance, validated_data)

        self.save_manual_pricing_formulas(instance, False, manual_pricing_formulas)
        self.save_accrual_calculation_schedules(instance, False, accrual_calculation_schedules)
        self.save_factor_schedules(instance, False, factor_schedules)
        self.save_event_schedules(instance, False, event_schedules)

        self.calculate_prices_accrued_price(instance, False)
        self.rebuild_event_schedules(instance, False)

        return instance

    def save_instr_related(self, instrument, created, instrument_attr, model, validated_data, accept=None):
        if validated_data is None:
            return

        related_attr = getattr(instrument, instrument_attr)
        processed = {}

        for attr in validated_data:
            oid = attr.get('id', None)
            if oid:
                try:
                    o = related_attr.get(id=oid)
                except ObjectDoesNotExist:
                    o = model(instrument=instrument)
            else:
                o = model(instrument=instrument)
            if callable(accept):
                if not accept(attr, o):
                    if o:
                        processed[o.id] = o
                    continue
            for k, v in attr.items():
                if k not in ['id', 'instrument', 'actions']:
                    setattr(o, k, v)
            o.save()
            processed[o.id] = o
            attr['id'] = o.id

        if not created:
            related_attr.exclude(id__in=processed.keys()).delete()

        return processed

    def save_manual_pricing_formulas(self, instrument, created, manual_pricing_formulas):
        self.save_instr_related(instrument, created, 'manual_pricing_formulas', ManualPricingFormula,
                                manual_pricing_formulas)

    def save_accrual_calculation_schedules(self, instrument, created, accrual_calculation_schedules):
        self.save_instr_related(instrument, created, 'accrual_calculation_schedules', AccrualCalculationSchedule,
                                accrual_calculation_schedules)

    def save_factor_schedules(self, instrument, created, factor_schedules):
        self.save_instr_related(instrument, created, 'factor_schedules', InstrumentFactorSchedule, factor_schedules)

    def save_event_schedules(self, instrument, created, event_schedules):
        events = self.save_instr_related(instrument, created, 'event_schedules', EventSchedule, event_schedules,
                                         accept=lambda attr, obj: not obj.is_auto_generated if obj else True)

        if event_schedules:
            for es in event_schedules:
                try:
                    event_schedule = events[es['id']]
                except KeyError:
                    continue
                if event_schedule.is_auto_generated:
                    continue

                actions_data = es.get('actions', None)
                if actions_data is None:
                    continue

                processed = set()
                for action_data in actions_data:
                    oid = action_data.get('id', None)
                    if oid:
                        try:
                            o = event_schedule.actions.get(id=oid)
                        except ObjectDoesNotExist:
                            o = EventScheduleAction(event_schedule=event_schedule)
                    else:
                        o = EventScheduleAction(event_schedule=event_schedule)

                    for k, v in action_data.items():
                        if k not in ['id', 'event_schedule', ]:
                            setattr(o, k, v)
                    o.save()
                    processed.add(o.id)
                    action_data['id'] = o.id

                if not created:
                    event_schedule.actions.exclude(id__in=processed).delete()

    def calculate_prices_accrued_price(self, instrument, created):
        instrument.calculate_prices_accrued_price(save=True)

    def rebuild_event_schedules(self, instrument, created):
        try:
            instrument.rebuild_event_schedules()
        except ValueError as e:
            raise ValidationError({'instrument_type': '%s' % e})


class InstrumentCalculatePricesAccruedPriceSerializer(serializers.Serializer):
    begin_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)

    def validate(self, attrs):
        begin_date = attrs.get('begin_date', None)
        end_date = attrs.get('end_date', None)
        if begin_date is None and end_date is None:
            attrs['begin_date'] = attrs['end_date'] = date_now() - timedelta(days=1)
        return attrs


# class InstrumentBulkObjectPermissionSerializer(AbstractBulkObjectPermissionSerializer):
#     content_objects = InstrumentField(many=True, allow_null=False, allow_empty=False)
#
#     class Meta:
#         model = Instrument


class PriceHistorySerializer(serializers.ModelSerializer):
    instrument = InstrumentField()
    instrument_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='instrument')
    pricing_policy = PricingPolicyField(allow_null=False)
    pricing_policy_object = ReadonlyNamedModelSerializer(source='pricing_policy')
    principal_price = FloatEvalField()
    accrued_price = FloatEvalField()

    class Meta:
        model = PriceHistory
        fields = [
            'url', 'id', 'instrument', 'instrument_object', 'pricing_policy', 'pricing_policy_object',
            'date', 'principal_price', 'accrued_price'
        ]

    def __init__(self, *args, **kwargs):
        super(PriceHistorySerializer, self).__init__(*args, **kwargs)
        if 'request' not in self.context:
            self.fields.pop('url')


class EventScheduleConfigSerializer(serializers.ModelSerializer):
    master_user = MasterUserField()
    name = ExpressionField()
    description = ExpressionField()
    notification_class_object = ReadonlyModelWithNameSerializer(source='notification_class')

    class Meta:
        model = EventScheduleConfig
        fields = [
            'url', 'id', 'master_user', 'name', 'description', 'notification_class', 'notification_class_object',
            'notify_in_n_days', 'action_text', 'action_is_sent_to_pending', 'action_is_book_automatic',
        ]
