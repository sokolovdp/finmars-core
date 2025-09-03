import logging
from datetime import timedelta

from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import now
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import ReadOnlyField
from rest_framework.serializers import ListSerializer

from poms.common.fields import DateTimeTzAwareField, ExpressionField, FloatEvalField
from poms.common.models import EXPRESSION_FIELD_LENGTH
from poms.common.serializers import (
    ModelMetaSerializer,
    ModelWithObjectStateSerializer,
    ModelWithTimeStampSerializer,
    ModelWithUserCodeSerializer,
    PomsClassSerializer,
)
from poms.common.utils import date_now
from poms.currencies.fields import CurrencyDefault
from poms.currencies.models import CurrencyPricingPolicy
from poms.currencies.serializers import CurrencyEvalSerializer, CurrencyField
from poms.iam.serializers import ModelWithResourceGroupSerializer
from poms.instruments.fields import (
    AUTO_CALCULATE,
    AccrualCalculationModelField,
    AutocalculateFloatEvalField,
    CountryField,
    DailyPricingModelField,
    InstrumentField,
    InstrumentTypeField,
    PaymentSizeDetailField,
    PeriodicityField,
    PricingConditionField,
    PricingPolicyField,
)
from poms.instruments.models import (
    AccrualCalculationModel,
    AccrualCalculationSchedule,
    AccrualEvent,
    CostMethod,
    Country,
    DailyPricingModel,
    EventSchedule,
    EventScheduleAction,
    EventScheduleConfig,
    ExposureCalculationModel,
    GeneratedEvent,
    Instrument,
    InstrumentClass,
    InstrumentFactorSchedule,
    InstrumentPricingPolicy,
    InstrumentType,
    InstrumentTypeAccrual,
    InstrumentTypeEvent,
    InstrumentTypeInstrumentAttribute,
    InstrumentTypeInstrumentFactorSchedule,
    InstrumentTypePricingPolicy,
    LongUnderlyingExposure,
    ManualPricingFormula,
    PaymentSizeDetail,
    Periodicity,
    PriceHistory,
    PricingCondition,
    PricingPolicy,
    ShortUnderlyingExposure,
)
from poms.obj_attrs.serializers import ModelWithAttributesSerializer
from poms.pricing.models import PriceHistoryError
from poms.system_messages.handlers import send_system_message
from poms.transactions.fields import TransactionTypeField
from poms.transactions.models import TransactionType
from poms.users.fields import MasterUserField
from poms.users.utils import get_master_user_from_context, get_member_from_context

_l = logging.getLogger("poms.instruments")


class InstrumentClassSerializer(PomsClassSerializer):
    class Meta(PomsClassSerializer.Meta):
        model = InstrumentClass


class InstrumentClassViewSerializer(PomsClassSerializer):
    class Meta:
        model = InstrumentClass
        fields = ["id", "user_code", "name"]


class DailyPricingModelSerializer(PomsClassSerializer):
    class Meta(PomsClassSerializer.Meta):
        model = DailyPricingModel


class PricingConditionSerializer(PomsClassSerializer):
    class Meta(PomsClassSerializer.Meta):
        model = PricingCondition


class DailyPricingModelViewSerializer(PomsClassSerializer):
    class Meta:
        model = DailyPricingModel
        fields = ["id", "user_code", "name"]


class PricingConditionViewSerializer(PomsClassSerializer):
    class Meta:
        model = PricingCondition
        fields = ["id", "user_code", "name"]


class AccrualCalculationModelSerializer(PomsClassSerializer):
    class Meta(PomsClassSerializer.Meta):
        model = AccrualCalculationModel


class AccrualCalculationModelViewSerializer(PomsClassSerializer):
    class Meta:
        model = AccrualCalculationModel
        fields = ["id", "user_code", "name"]


class PaymentSizeDetailSerializer(PomsClassSerializer):
    class Meta(PomsClassSerializer.Meta):
        model = PaymentSizeDetail


class CountrySerializer(serializers.ModelSerializer):
    class Meta(PomsClassSerializer.Meta):
        fields = [
            "id",
            "name",
            "user_code",
            "country_code",
            "region",
            "region_code",
            "alpha_2",
            "alpha_3",
            "sub_region",
            "sub_region_code",
        ]
        model = Country


class ExposureCalculationModelSerializer(PomsClassSerializer):
    class Meta(PomsClassSerializer.Meta):
        model = ExposureCalculationModel


class LongUnderlyingExposureSerializer(PomsClassSerializer):
    class Meta(PomsClassSerializer.Meta):
        model = LongUnderlyingExposure


class ShortUnderlyingExposureSerializer(PomsClassSerializer):
    class Meta(PomsClassSerializer.Meta):
        model = ShortUnderlyingExposure


class PaymentSizeDetailViewSerializer(PomsClassSerializer):
    class Meta:
        model = PaymentSizeDetail
        fields = ["id", "user_code", "name"]


class PeriodicitySerializer(PomsClassSerializer):
    class Meta(PomsClassSerializer.Meta):
        model = Periodicity


class PeriodicityViewSerializer(PomsClassSerializer):
    class Meta:
        model = Periodicity
        fields = ["id", "user_code", "name"]


class CostMethodSerializer(PomsClassSerializer):
    class Meta(PomsClassSerializer.Meta):
        model = CostMethod


class CostMethodViewSerializer(PomsClassSerializer):
    class Meta:
        model = CostMethod
        fields = ["id", "user_code", "name"]


def set_currency_pricing_scheme_parameters(pricing_policy, parameters):
    # print('pricing_policy %s ' % pricing_policy)
    # print('parameters %s ' % parameters)

    if parameters:
        if hasattr(parameters, "data"):
            pricing_policy.data = parameters.data

        if hasattr(parameters, "default_value"):
            pricing_policy.default_value = parameters.default_value

        if hasattr(parameters, "attribute_key"):
            pricing_policy.attribute_key = parameters.attribute_key


def set_instrument_pricing_scheme_parameters(pricing_policy, parameters):
    # print('pricing_policy %s ' % pricing_policy)
    # print('parameters %s ' % parameters)

    if parameters:
        if hasattr(parameters, "data"):
            pricing_policy.data = parameters.data

        if hasattr(parameters, "default_value"):
            pricing_policy.default_value = parameters.default_value

        if hasattr(parameters, "attribute_key"):
            pricing_policy.attribute_key = parameters.attribute_key


class PricingPolicySerializer(
    ModelWithUserCodeSerializer,
    ModelWithTimeStampSerializer,
    ModelWithObjectStateSerializer,
):
    master_user = MasterUserField()

    # expr = ExpressionField(max_length=EXPRESSION_FIELD_LENGTH, allow_blank=True, allow_null=True)

    class Meta:
        model = PricingPolicy
        fields = [
            "id",
            "master_user",
            "user_code",
            "configuration_code",
            "name",
            "short_name",
            "notes",
            "expr",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # def create_instrument_type_pricing_policies(self, instance):
    #     from poms.pricing.models import InstrumentTypePricingPolicy
    #
    #     instrument_types = InstrumentType.objects.filter(
    #         master_user=instance.master_user
    #     )
    #
    #     for item in instrument_types:
    #         with transaction.atomic():
    #             try:
    #                 try:
    #                     pricing_policy = InstrumentTypePricingPolicy.objects.get(
    #                         instrument_type=item, pricing_policy=instance
    #                     )
    #                 except Exception as e:
    #                     _l.error(
    #                         f"Get error, trying to create new InstrumentTypePricingPolicy {e}"
    #                     )
    #
    #                     pricing_policy = InstrumentTypePricingPolicy(
    #                         instrument_type=item,
    #                         pricing_policy=instance,
    #                         pricing_scheme=instance.default_instrument_pricing_scheme,
    #                     )
    #
    #                     parameters = (
    #                         instance.default_instrument_pricing_scheme.get_parameters()
    #                     )
    #                     set_instrument_pricing_scheme_parameters(
    #                         pricing_policy, parameters
    #                     )
    #
    #                     pricing_policy.save()
    #
    #             except Exception as e:
    #                 _l.error(f"InstrumentTypePricingPolicy create error {e}")
    #
    # def create_instrument_pricing_policies(self, instance):
    #     from poms.pricing.models import InstrumentPricingPolicy
    #
    #     instruments = Instrument.objects.filter(master_user=instance.master_user)
    #
    #     for item in instruments:
    #         with transaction.atomic():
    #             try:
    #                 try:
    #                     pricing_policy = InstrumentPricingPolicy.objects.get(
    #                         instrument=item, pricing_policy=instance
    #                     )
    #                 except Exception as e:
    #                     _l.error(
    #                         f"Get error, trying to create new InstrumentPricingPolicy {e}"
    #                     )
    #
    #                     pricing_policy = InstrumentPricingPolicy(
    #                         instrument=item,
    #                         pricing_policy=instance,
    #                         pricing_scheme=instance.default_instrument_pricing_scheme,
    #                     )
    #
    #                     parameters = (
    #                         instance.default_instrument_pricing_scheme.get_parameters()
    #                     )
    #                     set_instrument_pricing_scheme_parameters(
    #                         pricing_policy, parameters
    #                     )
    #
    #                     pricing_policy.save()
    #             except Exception as e:
    #                 _l.error(f"InstrumentPricingPolicy create error {e}")

    # def create_currency_pricing_policies(self, instance):
    #     from poms.currencies.models import Currency
    #     from poms.pricing.models import CurrencyPricingPolicy
    #
    #     currencies = Currency.objects.filter(master_user=instance.master_user)
    #
    #     for item in currencies:
    #         with transaction.atomic():
    #             try:
    #                 try:
    #                     pricing_policy = CurrencyPricingPolicy.objects.get(
    #                         currency=item, pricing_policy=instance
    #                     )
    #
    #                 except Exception as e:
    #                     _l.error(
    #                         f"Get error, trying to create new CurrencyPricingPolicy {e}"
    #                     )
    #
    #                     pricing_policy = CurrencyPricingPolicy(
    #                         currency=item,
    #                         pricing_policy=instance,
    #                         pricing_scheme=instance.default_currency_pricing_scheme,
    #                     )
    #
    #                     parameters = (
    #                         instance.default_currency_pricing_scheme.get_parameters()
    #                     )
    #                     set_currency_pricing_scheme_parameters(
    #                         pricing_policy, parameters
    #                     )
    #
    #                     pricing_policy.save()
    #
    #             except Exception as e:
    #                 _l.error(f"CurrencyPricingPolicy create error {e}")

    def create(self, validated_data):
        instance = super().create(validated_data)

        # print("Creating Pricing Policies For Entities")

        # self.create_instrument_type_pricing_policies(instance)
        # self.create_instrument_pricing_policies(instance)
        # self.create_currency_pricing_policies(instance)

        return instance

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)

        # print("Creating Pricing Policies For Entities")

        # self.create_instrument_type_pricing_policies(instance)
        # self.create_instrument_pricing_policies(instance)
        # self.create_currency_pricing_policies(instance)

        return instance


class PricingPolicyLightSerializer(ModelWithUserCodeSerializer):
    master_user = MasterUserField()

    class Meta:
        model = PricingPolicy
        fields = ["id", "master_user", "user_code", "name", "short_name"]


class PricingPolicyViewSerializer(ModelWithUserCodeSerializer):
    class Meta:
        model = PricingPolicy
        fields = ["id", "user_code", "name", "short_name", "notes", "expr"]


class InstrumentTypePricingPolicySerializer(serializers.ModelSerializer):
    pricing_policy_id = serializers.IntegerField(read_only=False, required=True)
    pricing_policy = PricingPolicyLightSerializer(read_only=True)

    class Meta:
        model = InstrumentTypePricingPolicy
        fields = (
            "id",
            "pricing_policy_id",
            "pricing_policy",
            "target_pricing_schema_user_code",
            "options",
        )


class InstrumentPricingPolicySerializer(serializers.ModelSerializer):
    pricing_policy_id = serializers.IntegerField(read_only=False, required=True)
    pricing_policy = PricingPolicyLightSerializer(read_only=True)

    class Meta:
        model = InstrumentPricingPolicy
        fields = (
            "id",
            "pricing_policy_id",
            "pricing_policy",
            "target_pricing_schema_user_code",
            "options",
        )


class CurrencyPricingPolicySerializer(serializers.ModelSerializer):
    pricing_policy_id = serializers.IntegerField(read_only=False, required=True)
    pricing_policy = PricingPolicyLightSerializer(read_only=True)

    class Meta:
        model = CurrencyPricingPolicy
        fields = (
            "id",
            "pricing_policy_id",
            "pricing_policy",
            "target_pricing_schema_user_code",
            "options",
        )


class InstrumentTypeAccrualSerializer(serializers.ModelSerializer):
    data = serializers.JSONField(allow_null=False)

    class Meta:
        model = InstrumentTypeAccrual
        fields = ["id", "name", "order", "autogenerate", "data"]


class InstrumentTypeInstrumentAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstrumentTypeInstrumentAttribute
        fields = [
            "id",
            "attribute_type_user_code",
            "value_type",
            "value_string",
            "value_float",
            "value_date",
            "value_classifier",
        ]


class InstrumentTypeInstrumentFactorScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstrumentTypeInstrumentFactorSchedule
        fields = [
            "id",
            "effective_date",
            "effective_date_value_type",
            "position_factor_value",
            "position_factor_value_value_type",
            "factor_value1",
            "factor_value1_value_type",
            "factor_value2",
            "factor_value2_value_type",
            "factor_value3",
            "factor_value3_value_type",
        ]


class InstrumentTypeEventSerializer(serializers.ModelSerializer):
    data = serializers.JSONField(allow_null=True, required=False)

    class Meta:
        model = InstrumentTypeEvent
        fields = ["id", "name", "order", "autogenerate", "data"]


class InstrumentTypeSerializer(
    ModelWithUserCodeSerializer,
    ModelWithAttributesSerializer,
    ModelWithTimeStampSerializer,
    ModelMetaSerializer,
):
    master_user = MasterUserField()
    instrument_class_object = InstrumentClassSerializer(
        source="instrument_class",
        read_only=True,
    )
    one_off_event = TransactionTypeField(
        allow_null=True,
        required=False,
    )
    one_off_event_object = serializers.PrimaryKeyRelatedField(
        source="one_off_event",
        read_only=True,
    )
    regular_event = TransactionTypeField(
        allow_null=True,
        required=False,
    )
    regular_event_object = serializers.PrimaryKeyRelatedField(
        source="regular_event",
        read_only=True,
    )
    factor_same = TransactionTypeField(
        allow_null=True,
        required=False,
    )
    factor_same_object = serializers.PrimaryKeyRelatedField(
        source="factor_same",
        read_only=True,
    )
    factor_up = TransactionTypeField(
        allow_null=True,
        required=False,
    )
    factor_up_object = serializers.PrimaryKeyRelatedField(
        source="factor_up",
        read_only=True,
    )
    factor_down = TransactionTypeField(
        allow_null=True,
        required=False,
    )
    factor_down_object = serializers.PrimaryKeyRelatedField(
        source="factor_down",
        read_only=True,
    )
    pricing_currency_object = serializers.PrimaryKeyRelatedField(
        source="pricing_currency",
        read_only=True,
    )
    pricing_condition_object = PricingConditionSerializer(
        source="pricing_condition",
        read_only=True,
    )
    pricing_policies = InstrumentTypePricingPolicySerializer(required=False, many=True, read_only=False)
    instrument_attributes = InstrumentTypeInstrumentAttributeSerializer(
        required=False,
        many=True,
        read_only=False,
    )
    instrument_factor_schedules = InstrumentTypeInstrumentFactorScheduleSerializer(
        required=False,
        many=True,
        read_only=False,
    )
    accruals = InstrumentTypeAccrualSerializer(
        required=False,
        many=True,
        read_only=False,
    )
    events = InstrumentTypeEventSerializer(
        required=False,
        many=True,
        read_only=False,
    )
    accrued_currency = CurrencyField(
        default=CurrencyDefault(),
    )
    accrued_currency_object = serializers.PrimaryKeyRelatedField(
        source="accrued_currency",
        read_only=True,
    )
    payment_size_detail_object = PaymentSizeDetailSerializer(
        source="payment_size_detail",
        read_only=True,
    )
    instrument_factor_schedule_data = serializers.JSONField(
        allow_null=False,
    )

    class Meta:
        model = InstrumentType
        fields = [
            "id",
            "master_user",
            "user_code",
            "name",
            "short_name",
            "public_name",
            "notes",
            "is_default",
            "is_deleted",
            "instrument_form_layouts",
            "instrument_class",
            "instrument_class_object",
            "one_off_event",
            "one_off_event_object",
            "regular_event",
            "regular_event_object",
            "factor_same",
            "factor_same_object",
            "factor_up",
            "factor_up_object",
            "factor_down",
            "factor_down_object",
            "is_enabled",
            "pricing_policies",
            "has_second_exposure_currency",
            "accruals",
            "events",
            "instrument_attributes",
            "instrument_factor_schedules",
            "payment_size_detail",
            "payment_size_detail_object",
            "accrued_currency",
            "accrued_currency_object",
            "accrued_multiplier",
            "default_accrued",
            "exposure_calculation_model",
            "co_directional_exposure_currency",
            "counter_directional_exposure_currency",
            "co_directional_exposure_currency_value_type",
            "counter_directional_exposure_currency_value_type",
            "long_underlying_instrument",
            "short_underlying_instrument",
            "underlying_long_multiplier",
            "underlying_short_multiplier",
            "long_underlying_exposure",
            "short_underlying_exposure",
            "position_reporting",
            "instrument_factor_schedule_data",
            "pricing_currency",
            "pricing_currency_object",
            "price_multiplier",
            "pricing_condition",
            "pricing_condition_object",
            "default_price",
            "maturity_date",
            "maturity_price",
            "reference_for_pricing",
            "configuration_code",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["one_off_event_object"] = TransactionTypeSimpleViewSerializer(
            source="one_off_event", read_only=True
        )
        self.fields["regular_event_object"] = TransactionTypeSimpleViewSerializer(
            source="regular_event", read_only=True
        )
        self.fields["factor_same_object"] = TransactionTypeSimpleViewSerializer(source="factor_same", read_only=True)
        self.fields["factor_up_object"] = TransactionTypeSimpleViewSerializer(source="factor_up", read_only=True)
        self.fields["factor_down_object"] = TransactionTypeSimpleViewSerializer(source="factor_down", read_only=True)

    def validate(self, attrs):
        instrument_class = attrs.get("instrument_class", None)  # noqa: F841
        # one_off_event = attrs.get('one_off_event', None)
        # regular_event = attrs.get('regular_event', None)
        #
        # if instrument_class:
        #     errors = {}
        #     if instrument_class.has_one_off_event and one_off_event is None:
        #         errors['one_off_event'] = self.fields['one_off_event'].error_messages['required']
        #     if instrument_class.has_regular_event and regular_event is None:
        #         errors['regular_event'] = self.fields['regular_event'].error_messages['required']
        #
        #     if errors:
        #         raise ValidationError(errors)

        return attrs

    def create(self, validated_data):
        pricing_policies = validated_data.pop("pricing_policies", [])
        accruals = validated_data.pop("accruals", [])
        events = validated_data.pop("events", [])
        instrument_attributes = validated_data.pop("instrument_attributes", [])
        instrument_factor_schedules = validated_data.pop("instrument_factor_schedules", [])

        instance = super().create(validated_data)

        self.save_pricing_policies(instance, pricing_policies)
        self.save_accruals(instance, accruals)
        self.save_events(instance, events)
        self.save_instrument_attributes(instance, instrument_attributes)
        self.save_instrument_factor_schedules(instance, instrument_factor_schedules)

        return instance

    def update(self, instance, validated_data):
        pricing_policies = validated_data.pop("pricing_policies", [])
        accruals = validated_data.pop("accruals", [])
        events = validated_data.pop("events", [])
        instrument_attributes = validated_data.pop("instrument_attributes", [])
        instrument_factor_schedules = validated_data.pop("instrument_factor_schedules", [])

        instance = super().update(instance, validated_data)

        self.save_pricing_policies(instance, pricing_policies)
        self.save_accruals(instance, accruals)
        self.save_events(instance, events)
        self.save_instrument_attributes(instance, instrument_attributes)
        self.save_instrument_factor_schedules(instance, instrument_factor_schedules)

        return instance

    @staticmethod
    def _update_and_save_accruals(item: dict, obj: InstrumentTypeAccrual):
        obj.name = item["name"]
        obj.order = item["order"]
        obj.autogenerate = item["autogenerate"]
        obj.data = item.get("data")
        obj.save()

    def save_accruals(self, instance, accruals):
        ids = set()

        if accruals:
            for item in accruals:
                try:
                    oid = item.get("id", None)

                    if oid:
                        ids.add(oid)

                    obj = InstrumentTypeAccrual.objects.get(instrument_type=instance, id=oid)
                    self._update_and_save_accruals(item, obj)

                except InstrumentTypeAccrual.DoesNotExist:
                    try:
                        obj = InstrumentTypeAccrual.objects.create(instrument_type=instance)
                        self._update_and_save_accruals(item, obj)
                        ids.add(obj.id)

                    except Exception as e:
                        _l.error(f"Can't Create Instrument Type Accrual {repr(e)}")

        InstrumentTypeAccrual.objects.filter(
            instrument_type=instance,
        ).exclude(id__in=ids).delete()

    @staticmethod
    def _update_and_save_events(item, o):
        o.name = item["name"]
        o.order = item["order"]
        o.autogenerate = item["autogenerate"]
        o.data = item.get("data", None)
        o.save()

    def save_events(self, instance, events):
        ids = set()

        if events:
            for item in events:
                try:
                    oid = item.get("id", None)

                    if oid:
                        ids.add(oid)

                    o = InstrumentTypeEvent.objects.get(instrument_type=instance, id=oid)
                    self._update_and_save_events(item, o)

                except InstrumentTypeEvent.DoesNotExist:
                    try:
                        o = InstrumentTypeEvent.objects.create(instrument_type=instance)
                        self._update_and_save_events(item, o)
                        ids.add(o.id)

                    except Exception as e:
                        _l.error(f"Can't Create Instrument Type Event {repr(e)}")

        InstrumentTypeEvent.objects.filter(
            instrument_type=instance,
        ).exclude(
            id__in=ids,
        ).delete()

    @staticmethod
    def _update_and_save_attributes(item, obj: InstrumentTypeInstrumentAttribute):
        obj.attribute_type_user_code = item["attribute_type_user_code"]
        obj.value_type = item["value_type"]
        obj.value_string = item["value_string"]
        obj.value_float = item["value_float"]
        obj.value_date = item["value_date"]
        obj.value_classifier = item["value_classifier"]
        obj.save()

    def save_instrument_attributes(self, instance, attributes):
        ids = set()

        if attributes:
            for item in attributes:
                try:
                    oid = item.get("id", None)

                    if oid:
                        ids.add(oid)

                    obj = InstrumentTypeInstrumentAttribute.objects.get(instrument_type=instance, id=oid)
                    self._update_and_save_attributes(item, obj)

                except InstrumentTypeInstrumentAttribute.DoesNotExist:
                    try:
                        obj = InstrumentTypeInstrumentAttribute.objects.create(instrument_type=instance)
                        self._update_and_save_attributes(item, obj)

                        ids.add(obj.id)

                    except Exception as e:
                        _l.error(f"Can't Create Instrument Type Instrument Attribute {repr(e)}")

        _l.info(f"instrument attribute create ids {ids}")

        InstrumentTypeInstrumentAttribute.objects.filter(
            instrument_type=instance,
        ).exclude(
            id__in=ids,
        ).delete()

    @staticmethod
    def _update_and_save_factor_schedules(item: dict, obj: InstrumentTypeInstrumentFactorSchedule):
        obj.effective_date = item["effective_date"]
        obj.effective_date_value_type = item["effective_date_value_type"]
        obj.position_factor_value = item["position_factor_value"]
        obj.position_factor_value_value_type = item["position_factor_value_value_type"]
        obj.factor_value1 = item["factor_value1"]
        obj.factor_value1_value_type = item["factor_value1_value_type"]
        obj.factor_value2 = item["factor_value2"]
        obj.factor_value2_value_type = item["factor_value2_value_type"]
        obj.factor_value3 = item["factor_value3"]
        obj.factor_value3_value_type = item["factor_value3_value_type"]

        obj.save()

    def save_instrument_factor_schedules(self, instance, events):
        ids = set()

        if events:
            for item in events:
                try:
                    oid = item.get("id", None)
                    if oid:
                        ids.add(oid)

                    obj = InstrumentTypeInstrumentFactorSchedule.objects.get(instrument_type=instance, id=oid)
                    self._update_and_save_factor_schedules(item, obj)

                except InstrumentTypeInstrumentFactorSchedule.DoesNotExist:
                    try:
                        obj = InstrumentTypeInstrumentFactorSchedule.objects.create(instrument_type=instance)
                        self._update_and_save_factor_schedules(item, obj)
                        ids.add(obj.id)

                    except Exception as e:
                        _l.error(f"Can't Create Instrument Factor Schedule {repr(e)}")

        _l.error(f"instrument Factor Schedule create ids {ids}")

        InstrumentTypeInstrumentFactorSchedule.objects.filter(instrument_type=instance).exclude(id__in=ids).delete()

    def save_pricing_policies(self, instance, pricing_policies):
        ids = set()
        pricing_policies = pricing_policies or []
        for item in pricing_policies:
            obj, _ = InstrumentTypePricingPolicy.objects.get_or_create(
                instrument_type=instance,
                pricing_policy_id=item["pricing_policy_id"],
            )
            self._update_and_save_pricing_policies(item, obj)
            ids.add(obj.id)

        to_delete = InstrumentTypePricingPolicy.objects.filter(instrument_type=instance)
        if ids:
            to_delete = to_delete.exclude(id__in=ids)
        to_delete.delete()

    @staticmethod
    def _update_and_save_pricing_policies(item: dict, obj: InstrumentTypePricingPolicy):
        obj.target_pricing_schema_user_code = item["target_pricing_schema_user_code"]
        if "options" in item:
            obj.options = item["options"]
        obj.save()


class TransactionTypeSimpleViewSerializer(ModelWithUserCodeSerializer):
    class Meta:
        model = TransactionType
        fields = ["id", "user_code", "name", "short_name", "public_name", "is_deleted"]


class InstrumentTypeLightSerializer(ModelWithUserCodeSerializer):
    master_user = MasterUserField()

    class Meta:
        model = InstrumentType
        fields = [
            "id",
            "master_user",
            "user_code",
            "name",
            "short_name",
            "public_name",
            "is_default",
            "is_deleted",
            "is_enabled",
        ]


class InstrumentTypeViewSerializer(ModelWithUserCodeSerializer):
    instrument_class_object = InstrumentClassSerializer(source="instrument_class", read_only=True)

    class Meta:
        model = InstrumentType
        fields = [
            "id",
            "instrument_class",
            "instrument_class_object",
            "user_code",
            "name",
            "short_name",
            "public_name",
            "instrument_form_layouts",
        ]


class AccrualEventSerializer(serializers.ModelSerializer):
    accrual_calculation_model = AccrualCalculationModelField()
    accrual_calculation_model_object = AccrualCalculationModelSerializer(
        source="accrual_calculation_model", read_only=True
    )

    class Meta:
        model = AccrualEvent
        fields = [
            "user_code",
            "start_date",
            "end_date",
            "accrual_size",
            "payment_date",
            "periodicity_n",
            "accrual_calculation_model",
            "accrual_calculation_model_object",
            "notes",
        ]


class InstrumentSerializer(
    ModelWithResourceGroupSerializer,
    ModelWithAttributesSerializer,
    ModelWithUserCodeSerializer,
    ModelWithTimeStampSerializer,
    ModelWithObjectStateSerializer,
):
    master_user = MasterUserField()
    pricing_currency = CurrencyField()
    accrued_currency = CurrencyField()
    instrument_type = InstrumentTypeField()
    co_directional_exposure_currency = CurrencyField()
    counter_directional_exposure_currency = CurrencyField()
    long_underlying_instrument = InstrumentField(required=False, allow_null=True)
    short_underlying_instrument = InstrumentField(required=False, allow_null=True)
    pricing_condition = PricingConditionField(required=False, allow_null=True)
    payment_size_detail = PaymentSizeDetailField(required=False, allow_null=True)
    daily_pricing_model = DailyPricingModelField(required=False, allow_null=True)
    country = CountryField(required=False, allow_null=True)
    first_transaction_date = serializers.ReadOnlyField()

    # ==== Objects below ====

    instrument_type_object = InstrumentTypeViewSerializer(source="instrument_type", read_only=True)
    pricing_currency_object = serializers.PrimaryKeyRelatedField(source="pricing_currency", read_only=True)
    accrued_currency_object = serializers.PrimaryKeyRelatedField(source="accrued_currency", read_only=True)
    co_directional_exposure_currency_object = serializers.PrimaryKeyRelatedField(
        source="co_directional_exposure_currency", read_only=True
    )
    counter_directional_exposure_currency_object = serializers.PrimaryKeyRelatedField(
        source="counter_directional_exposure_currency", read_only=True
    )
    long_underlying_instrument_object = serializers.PrimaryKeyRelatedField(
        source="long_underlying_instrument", read_only=True
    )
    short_underlying_instrument_object = serializers.PrimaryKeyRelatedField(
        source="short_underlying_instrument", read_only=True
    )
    exposure_calculation_model_object = ExposureCalculationModelSerializer(
        source="exposure_calculation_model", read_only=True
    )
    payment_size_detail_object = PaymentSizeDetailSerializer(source="payment_size_detail", read_only=True)
    daily_pricing_model_object = DailyPricingModelSerializer(source="daily_pricing_model", read_only=True)
    pricing_condition_object = PricingConditionSerializer(source="pricing_condition", read_only=True)
    country_object = CountrySerializer(source="country", read_only=True)
    identifier = serializers.JSONField(allow_null=False)
    registration_date = serializers.DateField(required=False, allow_null=True)

    class Meta:
        model = Instrument
        fields = [
            "id",
            "master_user",
            "instrument_type",
            "instrument_type_object",
            "user_code",
            "name",
            "short_name",
            "public_name",
            "notes",
            "identifier",
            "is_active",
            "is_deleted",
            "has_linked_with_portfolio",
            "pricing_currency",
            "pricing_currency_object",
            "price_multiplier",
            "accrued_currency",
            "accrued_currency_object",
            "accrued_multiplier",
            "payment_size_detail",
            "payment_size_detail_object",
            "default_price",
            "default_accrued",
            "user_text_1",
            "user_text_2",
            "user_text_3",
            "reference_for_pricing",
            "daily_pricing_model",
            "daily_pricing_model_object",
            "pricing_condition",
            "pricing_condition_object",
            "maturity_date",
            "maturity_price",
            "manual_pricing_formulas",
            "accrual_calculation_schedules",
            "factor_schedules",
            "event_schedules",
            "is_enabled",
            "pricing_policies",
            "exposure_calculation_model",
            "exposure_calculation_model_object",
            "co_directional_exposure_currency",
            "counter_directional_exposure_currency",
            "co_directional_exposure_currency_object",
            "counter_directional_exposure_currency_object",
            "long_underlying_instrument",
            "short_underlying_instrument",
            "long_underlying_instrument_object",
            "short_underlying_instrument_object",
            "underlying_long_multiplier",
            "underlying_short_multiplier",
            "long_underlying_exposure",
            "short_underlying_exposure",
            "position_reporting",
            "country",
            "country_object",
            "files",
            "first_transaction_date",
            "accrual_events",
            "registration_date",
        ]

    def __init__(self, *args, **kwargs):
        from poms.currencies.serializers import CurrencyViewSerializer
        from poms.explorer.serializers import FinmarsFileSerializer

        super().__init__(*args, **kwargs)

        self.fields["pricing_currency_object"] = CurrencyViewSerializer(source="pricing_currency", read_only=True)
        self.fields["accrued_currency_object"] = CurrencyViewSerializer(source="accrued_currency", read_only=True)
        self.fields["co_directional_exposure_currency_object"] = CurrencyViewSerializer(
            source="accrued_currency", read_only=True
        )
        self.fields["counter_directional_exposure_currency_object"] = CurrencyViewSerializer(
            source="accrued_currency", read_only=True
        )
        self.fields["manual_pricing_formulas"] = ManualPricingFormulaSerializer(
            many=True, required=False, allow_null=True
        )
        self.fields["accrual_calculation_schedules"] = AccrualCalculationScheduleSerializer(
            many=True, required=False, allow_null=True
        )
        self.fields["factor_schedules"] = InstrumentFactorScheduleSerializer(
            many=True, required=False, allow_null=True
        )
        self.fields["event_schedules"] = EventScheduleSerializer(many=True, required=False, allow_null=True)
        self.fields["pricing_policies"] = InstrumentPricingPolicySerializer(many=True, required=False, allow_null=True)
        self.fields["files"] = FinmarsFileSerializer(many=True, read_only=True)
        self.fields["accrual_events"] = AccrualEventSerializer(many=True, required=False, allow_null=True)

    def create(self, validated_data: dict) -> Instrument:
        func = f"{self.__class__.__name__}.create"

        # remove all nested objects from Instrument validated data
        manual_pricing_formulas = validated_data.pop("manual_pricing_formulas", None)
        accrual_calculation_schedules = validated_data.pop("accrual_calculation_schedules", None)
        factor_schedules = validated_data.pop("factor_schedules", None)
        event_schedules = validated_data.pop("event_schedules", None)
        pricing_policies = validated_data.pop("pricing_policies", [])
        accrual_events = validated_data.pop("accrual_events", [])

        instance = super().create(validated_data)
        _l.info(f"{func} created instrument.user_code={instance.user_code}")

        # created all related objects of the instance
        self.save_manual_pricing_formulas(instance, True, manual_pricing_formulas)
        self.save_accrual_calculation_schedules(instance, True, accrual_calculation_schedules)
        self.save_factor_schedules(instance, True, factor_schedules)
        self.save_event_schedules(instance, True, event_schedules)
        self.save_pricing_policies(instance, pricing_policies)
        self.save_accrual_events(instance, True, accrual_events)

        return instance

    def update(self, instance: Instrument, validated_data: dict) -> Instrument:
        func = f"{self.__class__.__name__}.update instance.user_code={instance.user_code} "

        # remove all nested objects from Instrument validated data

        manual_pricing_formulas = validated_data.pop("manual_pricing_formulas", None)
        accrual_calculation_schedules = validated_data.pop("accrual_calculation_schedules", None)
        factor_schedules = validated_data.pop("factor_schedules", None)
        event_schedules = validated_data.pop("event_schedules", None)
        pricing_policies = validated_data.pop("pricing_policies", [])
        accrual_events = validated_data.pop("accrual_events", [])

        instance = super().update(instance, validated_data)
        _l.info(f"{func} updated instrument.user_code={instance.user_code}")

        # created or update all related objects of the instance

        if manual_pricing_formulas:
            self.save_manual_pricing_formulas(instance, False, manual_pricing_formulas)
        if accrual_calculation_schedules:
            self.save_accrual_calculation_schedules(instance, False, accrual_calculation_schedules)
        if factor_schedules:
            self.save_factor_schedules(instance, False, factor_schedules)
        if event_schedules:
            self.save_event_schedules(instance, False, event_schedules)
        if accrual_events:
            self.save_accrual_events(instance, False, accrual_events)

        self.save_pricing_policies(instance, pricing_policies)

        try:  # can be set after in import
            self.calculate_prices_accrued_price(instance, False)
        except Exception as e:
            _l.error(f"Could not calculate prices and accrued price {repr(e)}")

        # needed to update data about related objects
        instance.refresh_from_db()

        return instance

    def save_pricing_policies(self, instance, pricing_policies):
        ids = set()
        pricing_policies = pricing_policies or []
        for item in pricing_policies:
            obj, _ = InstrumentPricingPolicy.objects.get_or_create(
                instrument=instance,
                pricing_policy_id=item["pricing_policy_id"],
            )
            self._update_and_save_pricing_policies(item, obj)
            ids.add(obj.id)

        to_delete = InstrumentPricingPolicy.objects.filter(instrument=instance)
        if ids:
            to_delete = to_delete.exclude(id__in=ids)
        to_delete.delete()

    @staticmethod
    def _update_and_save_pricing_policies(item: dict, obj: InstrumentPricingPolicy):
        obj.target_pricing_schema_user_code = item["target_pricing_schema_user_code"]
        if "options" in item:
            obj.options = item["options"]
        obj.save()

    def save_instr_related(
        self,
        instrument: Instrument,
        created: bool,
        instrument_attr: str,
        model,
        validated_data: dict,
        accept=None,
    ):
        validated_data = validated_data or []

        related_attr = getattr(instrument, instrument_attr)
        processed = {}

        for attr in validated_data:
            oid = attr.get("id", None)
            if oid:
                try:
                    o = related_attr.get(id=oid)
                except ObjectDoesNotExist:
                    o = model(instrument=instrument)
            else:
                o = model(instrument=instrument)

            if callable(accept) and not accept(attr, o):
                if o:
                    processed[o.id] = o
                continue
            for k, v in attr.items():
                if k not in ["id", "instrument", "actions"]:
                    setattr(o, k, v)
            o.save()
            processed[o.id] = o
            attr["id"] = o.id

        if not created:
            related_attr.exclude(id__in=processed.keys()).delete()

        return processed

    def save_manual_pricing_formulas(self, instrument, created, manual_pricing_formulas):
        self.save_instr_related(
            instrument,
            created,
            "manual_pricing_formulas",
            ManualPricingFormula,
            manual_pricing_formulas,
        )

    def save_accrual_calculation_schedules(self, instrument, created, accrual_calculation_schedules):
        self.save_instr_related(
            instrument,
            created,
            "accrual_calculation_schedules",
            AccrualCalculationSchedule,
            accrual_calculation_schedules,
        )

    def save_factor_schedules(self, instrument, created, factor_schedules):
        self.save_instr_related(
            instrument,
            created,
            "factor_schedules",
            InstrumentFactorSchedule,
            factor_schedules,
        )

    def save_event_schedules(self, instrument, created, event_schedules):
        event_schedules = event_schedules or []
        events = self.save_instr_related(
            instrument,
            created,
            "event_schedules",
            EventSchedule,
            event_schedules,
            accept=lambda attr, obj: not obj.is_auto_generated if obj else True,
        )

        for es in event_schedules:
            try:
                event_schedule = events[es["id"]]
            except KeyError:
                continue

            if event_schedule.is_auto_generated:
                continue

            actions_data = es.get("actions", None)
            if actions_data is None:
                continue

            processed = set()
            for action_data in actions_data:
                oid = action_data.get("id", None)
                if oid:
                    try:
                        o = event_schedule.actions.get(id=oid)
                    except ObjectDoesNotExist:
                        o = EventScheduleAction(event_schedule=event_schedule)
                else:
                    o = EventScheduleAction(event_schedule=event_schedule)

                for k, v in action_data.items():
                    if k not in [
                        "id",
                        "event_schedule",
                    ]:
                        setattr(o, k, v)
                o.save()
                processed.add(o.id)
                action_data["id"] = o.id

            if not created:
                event_schedule.actions.exclude(id__in=processed).delete()

    def calculate_prices_accrued_price(self, instrument, created):
        instrument.calculate_prices_accrued_price()

    def rebuild_event_schedules(self, instrument, created):
        try:
            instrument.rebuild_event_schedules()
        except ValueError as e:
            raise ValidationError({"instrument_type": f"{repr(e)}"}) from e

    def save_accrual_events(self, instrument, created, accrual_events):
        self.save_instr_related(
            instrument,
            created,
            "accrual_events",
            AccrualEvent,
            accrual_events,
        )


class InstrumentLightSerializer(ModelWithUserCodeSerializer):
    master_user = MasterUserField()

    class Meta:
        model = Instrument
        fields = [
            "id",
            "master_user",
            "user_code",
            "name",
            "short_name",
            "public_name",
            "identifier",
            "is_active",
            "is_deleted",
            "is_enabled",
            "has_linked_with_portfolio",
        ]

    def to_representation(self, instance):
        return super().to_representation(instance)


class InstrumentEvalSerializer(ModelWithUserCodeSerializer):
    pricing_currency = CurrencyEvalSerializer(read_only=True)
    accrued_currency = CurrencyEvalSerializer(read_only=True)
    country = CountrySerializer(read_only=True)

    identifier = serializers.JSONField(allow_null=False)

    class Meta:
        model = Instrument
        fields = [
            "id",
            "master_user",
            "user_code",
            "name",
            "short_name",
            "public_name",
            "is_active",
            "is_deleted",
            "is_enabled",
            "identifier",
            "has_linked_with_portfolio",
            "pricing_currency",
            "accrued_currency",
            "price_multiplier",
            "accrued_multiplier",
            "default_price",
            "default_accrued",
            "user_text_1",
            "user_text_2",
            "user_text_3",
            "reference_for_pricing",
            "country",
        ]

        read_only_fields = fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # self.fields['pricing_currency'] = CurrencyEvalSerializer(read_only=True)


class InstrumentForSelectSerializer(ModelWithUserCodeSerializer):
    master_user = MasterUserField()
    instrument_type_object = InstrumentTypeViewSerializer(
        source="instrument_type",
        read_only=True,
    )
    instrument_type = serializers.CharField(source="instrument_type.user_code")

    class Meta:
        model = Instrument
        fields = [
            "id",
            "master_user",
            "user_code",
            "name",
            "short_name",
            "identifier",
            "modified_at",
            "instrument_type",
            "instrument_type_object",
            "public_name",
            "is_active",
            "is_deleted",
            "is_enabled",
            "has_linked_with_portfolio",
        ]


class InstrumentViewSerializer(ModelWithUserCodeSerializer):
    instrument_type_object = InstrumentTypeViewSerializer(source="instrument_type", read_only=True)

    class Meta:
        model = Instrument
        fields = [
            "id",
            "instrument_type",
            "instrument_type_object",
            "user_code",
            "name",
            "short_name",
            "public_name",
            "notes",
            "is_active",
            "is_deleted",
            "identifier",
            "has_linked_with_portfolio",
            "user_text_1",
            "user_text_2",
            "user_text_3",
            "maturity_date",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


# DEPRECTATED (25.05.2020) delete soon
class ManualPricingFormulaSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=False, required=False, allow_null=True)
    pricing_policy = PricingPolicyField(allow_null=False)
    pricing_policy_object = PricingPolicyViewSerializer(source="pricing_policy", read_only=True)

    class Meta:
        model = ManualPricingFormula
        fields = ["id", "pricing_policy", "pricing_policy_object", "expr", "notes"]


class AccrualCalculationScheduleSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=False, required=False, allow_null=True)
    accrual_calculation_model = AccrualCalculationModelField()
    accrual_calculation_model_object = AccrualCalculationModelSerializer(
        source="accrual_calculation_model", read_only=True
    )
    periodicity = PeriodicityField(allow_null=False)
    periodicity_object = PeriodicitySerializer(source="periodicity", read_only=True)

    class Meta:
        model = AccrualCalculationSchedule
        fields = [
            "id",
            "accrual_start_date",
            "accrual_start_date_value_type",
            "first_payment_date",
            "first_payment_date_value_type",
            "accrual_size",
            "accrual_size_value_type",
            "periodicity_n",
            "periodicity_n_value_type",
            "accrual_calculation_model",
            "accrual_calculation_model_object",
            "periodicity",
            "periodicity_object",
            "notes",
        ]

    def validate(self, attrs):
        return attrs


class AccrualCalculationScheduleStandaloneSerializer(serializers.ModelSerializer):
    instrument = InstrumentField()

    accrual_calculation_model = AccrualCalculationModelField()
    accrual_calculation_model_object = AccrualCalculationModelSerializer(
        source="accrual_calculation_model", read_only=True
    )
    periodicity = PeriodicityField(allow_null=False)
    periodicity_object = PeriodicitySerializer(source="periodicity", read_only=True)

    class Meta:
        model = AccrualCalculationSchedule
        fields = [
            "id",
            "instrument",
            "accrual_start_date",
            "accrual_start_date_value_type",
            "first_payment_date",
            "first_payment_date_value_type",
            "accrual_size",
            "accrual_size_value_type",
            "periodicity_n",
            "periodicity_n_value_type",
            "accrual_calculation_model",
            "accrual_calculation_model_object",
            "periodicity",
            "periodicity_object",
            "notes",
        ]

    def validate(self, attrs):
        return attrs


class InstrumentFactorScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstrumentFactorSchedule
        fields = ["id", "effective_date", "factor_value"]


class InstrumentFactorScheduleStandaloneSerializer(serializers.ModelSerializer):
    instrument = InstrumentField()

    class Meta:
        model = InstrumentFactorSchedule
        fields = ["id", "instrument", "effective_date", "factor_value"]


class EventScheduleActionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=False, required=False, allow_null=True)
    text = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=True,
        allow_blank=True,
        allow_null=True,
    )

    display_text = serializers.SerializerMethodField()

    data = serializers.JSONField(allow_null=True, required=False)

    class Meta:
        model = EventScheduleAction
        fields = [
            "id",
            "transaction_type",
            "text",
            "is_sent_to_pending",
            "data",
            "is_book_automatic",
            "button_position",
            "display_text",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_display_text(self, obj):
        r = self.root
        if isinstance(r, ListSerializer):
            r = r.child
        if isinstance(r, GeneratedEventSerializer):
            return r.generate_text(obj.text)
        return None


class EventScheduleSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=False, required=False, allow_null=True)
    actions = EventScheduleActionSerializer(many=True, required=False, allow_null=True)
    event_class_object = serializers.PrimaryKeyRelatedField(source="event_class", read_only=True)
    notification_class_object = serializers.PrimaryKeyRelatedField(source="notification_class", read_only=True)
    periodicity_object = PeriodicitySerializer(source="periodicity", read_only=True)
    name = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=True,
        allow_blank=True,
        allow_null=True,
    )
    description = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    data = serializers.JSONField(allow_null=True, required=False)

    class Meta:
        model = EventSchedule
        fields = [
            "id",
            "name",
            "description",
            "event_class",
            "event_class_object",
            "notification_class",
            "notification_class_object",
            "notify_in_n_days",
            "periodicity",
            "periodicity_object",
            "effective_date",
            "effective_date_value_type",
            "periodicity_n",
            "periodicity_n_value_type",
            "final_date",
            "final_date_value_type",
            "is_auto_generated",
            "actions",
            "data",
        ]
        read_only_fields = ["is_auto_generated"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        from poms.transactions.serializers import (
            EventClassSerializer,
            NotificationClassSerializer,
        )

        self.fields["event_class_object"] = EventClassSerializer(source="event_class", read_only=True)
        self.fields["notification_class_object"] = NotificationClassSerializer(
            source="notification_class", read_only=True
        )

    def validate(self, attrs):
        return attrs


class InstrumentCalculatePricesAccruedPriceSerializer(serializers.Serializer):
    begin_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)

    def validate(self, attrs):
        begin_date = attrs.get("begin_date", None)
        end_date = attrs.get("end_date", None)
        if begin_date is None and end_date is None:
            attrs["begin_date"] = attrs["end_date"] = date_now() - timedelta(days=1)
        return attrs


CREATE_ACTIONS = {
    "create",
    "bulk_create",
}
AUTOCALCULATE_ACTIONS = {
    *CREATE_ACTIONS,
    "update",
    "partial_update",
}


class PriceHistorySerializer(ModelMetaSerializer):
    instrument = InstrumentField()
    instrument_object = InstrumentViewSerializer(source="instrument", read_only=True)
    pricing_policy = PricingPolicyField(allow_null=False)
    pricing_policy_object = PricingPolicySerializer(source="pricing_policy", read_only=True)
    principal_price = FloatEvalField()
    accrued_price = AutocalculateFloatEvalField()
    procedure_modified_datetime = ReadOnlyField()
    ytm = ReadOnlyField()

    class Meta:
        model = PriceHistory
        fields = [
            "id",
            "instrument",
            "instrument_object",
            "pricing_policy",
            "pricing_policy_object",
            "date",
            "principal_price",
            "accrued_price",
            "procedure_modified_datetime",
            "nav",
            "cash_flow",
            "factor",
            "long_delta",
            "short_delta",
            "is_temporary_price",
            "ytm",
            "modified_duration",
            "error_message",
        ]

    def validate(self, attrs: dict) -> dict:
        action = self.context["view"].action
        if action in AUTOCALCULATE_ACTIONS:
            if action in CREATE_ACTIONS and not attrs.get("date"):
                raise ValidationError("To calculate 'accrued_price' valid 'date' must be provided")

            if attrs.get("accrued_price") == AUTO_CALCULATE:
                attrs["accrued_price"] = None

            if attrs.get("factor") == AUTO_CALCULATE:
                attrs["factor"] = None

        return attrs

    def get_unique_together_validators(self):
        return []

    @staticmethod
    def create_price_history_error(instance):
        history_item = PriceHistoryError()
        history_item.status = PriceHistoryError.STATUS_CREATED
        history_item.master_user = instance.instrument.master_user
        history_item.instrument = instance.instrument
        history_item.principal_price = instance.principal_price
        history_item.accrued_price = instance.accrued_price
        history_item.date = instance.date
        history_item.pricing_policy = instance.pricing_policy
        history_item.save()
        return history_item

    def create(self, validated_data):
        instance = super().create(validated_data)
        instance.procedure_modified_datetime = now()
        instance.save()

        try:
            history_item = PriceHistoryError.objects.filter(
                instrument=instance.instrument,
                master_user=instance.instrument.master_user,
                date=instance.date,
                pricing_policy=instance.pricing_policy,
            )[0]

            history_item.status = PriceHistoryError.STATUS_OVERWRITTEN
            history_item.save()

        except (PriceHistoryError.DoesNotExist, IndexError):
            self.create_price_history_error(instance)

        member = get_member_from_context(self.context)
        master_user = get_master_user_from_context(self.context)

        send_system_message(
            master_user=master_user,
            performed_by=member.username,
            section="prices",
            type="success",
            title="New Price (manual)",
            description=(f"{instance.instrument.user_code} {str(instance.date)} {str(instance.principal_price)}"),
        )

        return instance

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        instance.procedure_modified_datetime = now()
        instance.save()

        self.create_price_history_error(instance)

        member = get_member_from_context(self.context)
        master_user = get_master_user_from_context(self.context)

        send_system_message(
            master_user=master_user,
            performed_by=member.username,
            section="prices",
            type="warning",
            title="Edit Price (manual)",
            description=(f"{instance.instrument.user_code} {str(instance.date)} {str(instance.principal_price)}"),
        )

        return instance


class PriceHistoryRecalculateSerializer(PriceHistorySerializer):
    recalculate_inputs = serializers.MultipleChoiceField(
        required=False,
        default=[],
        choices=["accrued_price", "factor", "ytm", "modified_duration"],
    )

    class Meta(PriceHistorySerializer.Meta):
        fields = PriceHistorySerializer.Meta.fields + ["recalculate_inputs"]

    def validate(self, attrs: dict) -> dict:
        if "accrued_price" in attrs.get("recalculate_inputs"):
            if not attrs.get("date"):
                raise ValidationError("To calculate 'accrued_price' valid 'date' must be provided")
            attrs["accrued_price"] = None

        if "factor" in attrs.get("recalculate_inputs"):
            attrs["factor"] = None

        return attrs


class PriceHistoryCalculateSerializer(serializers.Serializer):
    date_from = serializers.DateField(required=True)
    date_to = serializers.DateField(required=True)
    instruments = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)
    pricing_policies = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)

    def validate(self, attrs):
        if attrs["date_from"] > attrs["date_to"]:
            raise serializers.ValidationError("`date_from` must be earlier than `date_to`.")
        return attrs


class GeneratedEventSerializer(serializers.ModelSerializer):
    status_date = DateTimeTzAwareField(read_only=True)
    is_need_reaction = serializers.BooleanField(read_only=True)

    data = serializers.JSONField(allow_null=False)

    class Meta:
        model = GeneratedEvent
        fields = [
            "id",
            "effective_date",
            "notification_date",
            "status",
            "status_date",
            "event_schedule",
            "instrument",
            "portfolio",
            "account",
            "strategy1",
            "strategy2",
            "strategy3",
            "position",
            "is_need_reaction",
            "action",
            "transaction_type",
            "member",
            "data",
        ]
        read_only_fields = fields

    def __init__(self, *args, **kwargs):
        from poms.accounts.serializers import AccountViewSerializer
        from poms.portfolios.serializers import PortfolioViewSerializer
        from poms.strategies.serializers import (
            Strategy1ViewSerializer,
            Strategy2ViewSerializer,
            Strategy3ViewSerializer,
        )
        from poms.transactions.serializers import TransactionTypeViewSerializer
        from poms.users.serializers import MemberViewSerializer

        super().__init__(*args, **kwargs)
        self._current_instance = None

        self.fields["event_schedule_object"] = EventScheduleSerializer(source="event_schedule", read_only=True)
        self.fields["instrument_object"] = InstrumentViewSerializer(source="instrument", read_only=True)

        self.fields["portfolio_object"] = PortfolioViewSerializer(source="portfolio", read_only=True)

        self.fields["account_object"] = AccountViewSerializer(source="account", read_only=True)

        self.fields["strategy1_object"] = Strategy1ViewSerializer(source="strategy1", read_only=True)
        self.fields["strategy2_object"] = Strategy2ViewSerializer(source="strategy2", read_only=True)
        self.fields["strategy3_object"] = Strategy3ViewSerializer(source="strategy3", read_only=True)

        self.fields["action_object"] = EventScheduleActionSerializer(source="action", read_only=True)

        self.fields["transaction_type_object"] = TransactionTypeViewSerializer(
            source="transaction_type", read_only=True
        )

        self.fields["member_object"] = MemberViewSerializer(source="member", read_only=True)

    def to_representation(self, instance):
        self._current_instance = instance
        try:
            return super().to_representation(instance)
        finally:
            self._current_instance = None

    def generate_text(self, exr, names=None):
        return self._current_instance.generate_text(
            exr,
            names=names,
            context=self.context,
        )


class EventScheduleConfigSerializer(serializers.ModelSerializer):
    master_user = MasterUserField()
    name = ExpressionField(max_length=EXPRESSION_FIELD_LENGTH)
    description = ExpressionField(max_length=EXPRESSION_FIELD_LENGTH)
    notification_class_object = serializers.PrimaryKeyRelatedField(source="notification_class", read_only=True)

    class Meta:
        model = EventScheduleConfig
        fields = [
            "id",
            "master_user",
            "name",
            "description",
            "notification_class",
            "notification_class_object",
            "notify_in_n_days",
            "action_text",
            "action_is_sent_to_pending",
            "action_is_book_automatic",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        from poms.transactions.serializers import NotificationClassSerializer

        self.fields["notification_class_object"] = NotificationClassSerializer(
            source="notification_class", read_only=True
        )


class InstrumentTypeProcessSerializer(serializers.Serializer):
    def __init__(self, **kwargs):
        kwargs["context"] = context = kwargs.get("context", {}) or {}
        super().__init__(**kwargs)
        context["instance"] = self.instance

        self.fields["instrument_type"] = serializers.PrimaryKeyRelatedField(read_only=True)
        self.fields["instrument"] = serializers.SerializerMethodField(required=False, allow_null=True)

        self.fields["instrument_type_object"] = InstrumentTypeViewSerializer(source="instrument_type", read_only=True)

    def get_instrument(self, obj):
        return obj.instrument

    def validate(self, attrs):
        return attrs

    def create(self, validated_data):
        return validated_data


class InstrumentTypeEvalSerializer(ModelWithUserCodeSerializer, ModelWithTimeStampSerializer):
    master_user = MasterUserField()
    instrument_class_object = InstrumentClassSerializer(source="instrument_class", read_only=True)
    one_off_event = TransactionTypeField(allow_null=True, required=False)
    one_off_event_object = serializers.PrimaryKeyRelatedField(source="one_off_event", read_only=True)
    regular_event = TransactionTypeField(allow_null=True, required=False)
    regular_event_object = serializers.PrimaryKeyRelatedField(source="regular_event", read_only=True)
    factor_same = TransactionTypeField(allow_null=True, required=False)
    factor_same_object = serializers.PrimaryKeyRelatedField(source="factor_same", read_only=True)
    factor_up = TransactionTypeField(allow_null=True, required=False)
    factor_up_object = serializers.PrimaryKeyRelatedField(source="factor_up", read_only=True)
    factor_down = TransactionTypeField(allow_null=True, required=False)
    factor_down_object = serializers.PrimaryKeyRelatedField(source="factor_down", read_only=True)

    pricing_currency_object = serializers.PrimaryKeyRelatedField(source="pricing_currency", read_only=True)
    pricing_condition_object = PricingConditionSerializer(source="pricing_condition", read_only=True)

    instrument_attributes = InstrumentTypeInstrumentAttributeSerializer(required=False, many=True, read_only=False)
    instrument_factor_schedules = InstrumentTypeInstrumentFactorScheduleSerializer(
        required=False, many=True, read_only=False
    )

    accruals = InstrumentTypeAccrualSerializer(required=False, many=True, read_only=False)
    events = InstrumentTypeEventSerializer(required=False, many=True, read_only=False)

    accrued_currency = CurrencyField(default=CurrencyDefault())
    accrued_currency_object = serializers.PrimaryKeyRelatedField(source="accrued_currency", read_only=True)

    payment_size_detail_object = PaymentSizeDetailSerializer(source="payment_size_detail", read_only=True)

    instrument_factor_schedule_data = serializers.JSONField(allow_null=False)

    class Meta:
        model = InstrumentType
        fields = [
            "id",
            "master_user",
            "user_code",
            "name",
            "short_name",
            "public_name",
            "notes",
            "is_default",
            "is_deleted",
            "instrument_form_layouts",
            "instrument_class",
            "instrument_class_object",
            "one_off_event",
            "one_off_event_object",
            "regular_event",
            "regular_event_object",
            "factor_same",
            "factor_same_object",
            "factor_up",
            "factor_up_object",
            "factor_down",
            "factor_down_object",
            "is_enabled",
            "pricing_policies",
            "has_second_exposure_currency",
            "accruals",
            "events",
            "instrument_attributes",
            "instrument_factor_schedules",
            "payment_size_detail",
            "payment_size_detail_object",
            "accrued_currency",
            "accrued_currency_object",
            "accrued_multiplier",
            "default_accrued",
            "exposure_calculation_model",
            "co_directional_exposure_currency",
            "counter_directional_exposure_currency",
            "co_directional_exposure_currency_value_type",
            "counter_directional_exposure_currency_value_type",
            "long_underlying_instrument",
            "short_underlying_instrument",
            "underlying_long_multiplier",
            "underlying_short_multiplier",
            "long_underlying_exposure",
            "short_underlying_exposure",
            "position_reporting",
            "instrument_factor_schedule_data",
            "pricing_currency",
            "pricing_currency_object",
            "price_multiplier",
            "pricing_condition",
            "pricing_condition_object",
            "default_price",
            "maturity_date",
            "maturity_price",
            "reference_for_pricing",
        ]

        read_only_fields = fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["one_off_event_object"] = TransactionTypeSimpleViewSerializer(
            source="one_off_event", read_only=True
        )
        self.fields["regular_event_object"] = TransactionTypeSimpleViewSerializer(
            source="regular_event", read_only=True
        )
        self.fields["factor_same_object"] = TransactionTypeSimpleViewSerializer(source="factor_same", read_only=True)
        self.fields["factor_up_object"] = TransactionTypeSimpleViewSerializer(source="factor_up", read_only=True)
        self.fields["factor_down_object"] = TransactionTypeSimpleViewSerializer(source="factor_down", read_only=True)


class InstrumentTypeApplySerializer(serializers.Serializer):
    mode = serializers.ChoiceField(
        required=False,
        allow_null=True,
        choices=("fill", "overwrite"),
        default="overwrite",
    )
    fields_to_update = serializers.ListField(
        child=serializers.ChoiceField(
            choices=(
                "default_price",
                "default_accrued",
                "reference_for_pricing",
                "maturity_date",
                "maturity_price",
                "pricing_policies",
            )
        ),
        required=True,
        allow_empty=False,
    )


class AttachmentSerializer(serializers.Serializer):
    attachments = serializers.ListSerializer(child=serializers.CharField())

    def validate(self, attrs: dict) -> dict:
        from poms.explorer.models import StorageObject

        files = []
        for file_path in attrs["attachments"]:
            file = StorageObject.objects.filter(path=file_path, is_file=True).first()
            if not file:
                raise ValidationError(f"no such file: {file_path}")

            files.append(file)

        attrs["files"] = files
        return attrs

    def update(self, instance, *args):
        instance.files.add(*self.validated_data["files"])


class InstrumentOnBalanceSerializer(serializers.Serializer):
    date = serializers.DateField(write_only=True, default=now().date())
    user_codes = serializers.ListField(child=serializers.CharField(), write_only=True)


class DayTimeConventionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccrualCalculationModel
        fields = [
            "id",
            "user_code",
            "name",
        ]
