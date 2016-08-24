from __future__ import unicode_literals

import six
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.fields import empty

from poms.common.fields import ExpressionField, FloatEvalField
from poms.common.serializers import PomsClassSerializer, AbstractClassifierSerializer, AbstractClassifierNodeSerializer, \
    ModelWithUserCodeSerializer
from poms.currencies.fields import CurrencyDefault
from poms.currencies.serializers import CurrencyField
from poms.instruments.fields import InstrumentClassifierField, InstrumentField, InstrumentAttributeTypeField, \
    InstrumentTypeField, PricingPolicyField, InstrumentTypeDefault
from poms.instruments.models import InstrumentClassifier, Instrument, PriceHistory, InstrumentClass, DailyPricingModel, \
    AccrualCalculationModel, PaymentSizeDetail, Periodicity, CostMethod, InstrumentType, InstrumentAttributeType, \
    InstrumentAttribute, ManualPricingFormula, AccrualCalculationSchedule, InstrumentFactorSchedule, EventSchedule, \
    PricingPolicy, EventScheduleAction
from poms.integrations.fields import PriceDownloadSchemeField
from poms.obj_attrs.serializers import AbstractAttributeSerializer, AbstractAttributeTypeSerializer, \
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
    # url = serializers.HyperlinkedIdentityField(view_name='instrumentclassifiernode-detail')

    class Meta(AbstractClassifierNodeSerializer.Meta):
        model = InstrumentClassifier


class InstrumentTypeSerializer(ModelWithObjectPermissionSerializer, ModelWithUserCodeSerializer):
    master_user = MasterUserField()
    one_off_event = TransactionTypeField(allow_null=True, required=False)
    regular_event = TransactionTypeField(allow_null=True, required=False)
    tags = TagField(many=True, required=False, allow_null=True)

    class Meta:
        model = InstrumentType
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'public_name', 'notes', 'is_default',
                  'instrument_class', 'one_off_event', 'regular_event',
                  'tags']


class InstrumentAttributeTypeSerializer(AbstractAttributeTypeSerializer):
    classifiers = InstrumentClassifierSerializer(required=False, allow_null=True, many=True)

    class Meta(AbstractAttributeTypeSerializer.Meta):
        model = InstrumentAttributeType
        fields = AbstractAttributeTypeSerializer.Meta.fields + ['classifiers']


class ManualPricingFormulaSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=False, required=False, allow_null=True)
    pricing_policy = PricingPolicyField(allow_null=False)

    # instrument = InstrumentField()

    class Meta:
        model = ManualPricingFormula
        fields = ['id', 'pricing_policy', 'expr', 'notes']


class AccrualCalculationScheduleSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=False, required=False, allow_null=True)

    class Meta:
        model = AccrualCalculationSchedule
        fields = ['id', 'accrual_start_date', 'first_payment_date', 'accrual_size',
                  'accrual_calculation_model', 'periodicity', 'periodicity_n', 'notes']


class InstrumentFactorScheduleSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=False, required=False, allow_null=True)

    # instrument = InstrumentField()

    class Meta:
        model = InstrumentFactorSchedule
        fields = ['id', 'effective_date', 'factor_value']


class EventScheduleActionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=False, required=False, allow_null=True)
    transaction_type = TransactionTypeField()

    class Meta:
        model = EventScheduleAction
        fields = ['id', 'transaction_type', 'text', 'is_sent_to_pending', 'is_default',
                  'button_position']


class EventScheduleSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=False, required=False, allow_null=True)
    actions = EventScheduleActionSerializer(many=True)

    class Meta:
        model = EventSchedule
        fields = ['id', 'name', 'description', 'event_class', 'notification_class',
                  'effective_date', 'notify_in_n_days', 'periodicity', 'periodicity_n', 'final_date',
                  'actions']


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
    pricing_currency = CurrencyField(default=CurrencyDefault())
    accrued_currency = CurrencyField(default=CurrencyDefault())
    price_download_scheme = PriceDownloadSchemeField(allow_null=True)

    manual_pricing_formulas = ManualPricingFormulaSerializer(many=True, required=False, allow_null=True)
    accrual_calculation_schedules = AccrualCalculationScheduleSerializer(many=True, required=False, allow_null=True)
    factor_schedules = InstrumentFactorScheduleSerializer(many=True, required=False, allow_null=True)
    event_schedules = EventScheduleSerializer(many=True, required=False, allow_null=True)

    attributes = InstrumentAttributeSerializer(many=True, required=False, allow_null=True)
    tags = TagField(many=True, required=False, allow_null=True)

    class Meta:
        model = Instrument
        fields = ['url', 'id', 'master_user', 'instrument_type', 'user_code', 'name', 'short_name',
                  'public_name', 'notes', 'is_active',
                  'pricing_currency', 'price_multiplier', 'accrued_currency', 'accrued_multiplier',
                  'payment_size_detail', 'default_price', 'default_accrued',
                  'user_text_1', 'user_text_2', 'user_text_3',
                  'reference_for_pricing', 'daily_pricing_model', 'price_download_scheme',
                  'maturity_date',
                  'manual_pricing_formulas', 'accrual_calculation_schedules', 'factor_schedules', 'event_schedules',
                  'attributes', 'tags']

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

        return instance

    def save_instr_related(self, instrument, created, instrument_attr, model, validated_data):
        if validated_data is None:
            return

        # if created:
        #     if validated_data:
        #         for attr in validated_data:
        #             o = model(instrument=instrument)
        #             for k, v in six.iteritems(attr):
        #                 if k not in ['id', 'instrument', 'actions']:
        #                     setattr(o, k, v)
        #             o.save()
        #             attr['id'] = o.id
        # else:
        #     related_attr = getattr(instrument, instrument_attr)
        #     if validated_data:
        #         processed = set()
        #         for attr in validated_data:
        #             oid = attr.get('id', None)
        #             if oid:
        #                 try:
        #                     o = related_attr.get(id=oid)
        #                 except ObjectDoesNotExist:
        #                     o = model(instrument=instrument)
        #             else:
        #                 o = model(instrument=instrument)
        #             for k, v in six.iteritems(attr):
        #                 if k not in ['id', 'instrument', 'actions']:
        #                     setattr(o, k, v)
        #             o.save()
        #             processed.add(o.id)
        #             attr['id'] = o.id
        #         related_attr.exclude(id__in=processed).delete()
        #     else:
        #         related_attr.all().delete()

        related_attr = getattr(instrument, instrument_attr)
        processed = set()

        for attr in validated_data:
            oid = attr.get('id', None)
            if oid:
                try:
                    o = related_attr.get(id=oid)
                except ObjectDoesNotExist:
                    o = model(instrument=instrument)
            else:
                o = model(instrument=instrument)
            for k, v in six.iteritems(attr):
                if k not in ['id', 'instrument', 'actions']:
                    setattr(o, k, v)
            o.save()
            processed.add(o.id)
            attr['id'] = o.id

        if not created:
            related_attr.exclude(id__in=processed).delete()

    def save_manual_pricing_formulas(self, instrument, created, manual_pricing_formulas):
        self.save_instr_related(instrument, created, 'manual_pricing_formulas', ManualPricingFormula,
                                manual_pricing_formulas)

    def save_accrual_calculation_schedules(self, instrument, created, accrual_calculation_schedules):
        self.save_instr_related(instrument, created, 'accrual_calculation_schedules', AccrualCalculationSchedule,
                                accrual_calculation_schedules)

    def save_factor_schedules(self, instrument, created, factor_schedules):
        self.save_instr_related(instrument, created, 'factor_schedules', InstrumentFactorSchedule, factor_schedules)

    def save_event_schedules(self, instrument, created, event_schedules):
        self.save_instr_related(instrument, created, 'event_schedules', EventSchedule, event_schedules)

        if event_schedules:
            for es in event_schedules:
                event_schedule = instrument.event_schedules.get(pk=es['id'])

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

                    for k, v in six.iteritems(action_data):
                        if k not in ['id', 'event_schedule', ]:
                            setattr(o, k, v)
                    o.save()
                    processed.add(o.id)
                    action_data['id'] = o.id

                if not created:
                    event_schedule.actions.exclude(id__in=processed).delete()


class PriceHistorySerializer(serializers.ModelSerializer):
    instrument = InstrumentField()
    pricing_policy = PricingPolicyField(allow_null=False)
    principal_price = FloatEvalField()
    accrued_price = FloatEvalField()

    class Meta:
        model = PriceHistory
        fields = ['url', 'id', 'instrument', 'pricing_policy', 'date', 'principal_price', 'accrued_price']

    def __init__(self, *args, **kwargs):
        super(PriceHistorySerializer, self).__init__(*args, **kwargs)
        if 'request' not in self.context:
            self.fields.pop('url')
