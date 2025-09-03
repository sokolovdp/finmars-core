import contextlib
import json
import traceback
from logging import getLogger

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty
from rest_framework.validators import UniqueTogetherValidator

from poms.accounts.fields import AccountField, AccountTypeField
from poms.celery_tasks.models import CeleryTask
from poms.celery_tasks.serializers import CeleryTaskSerializer
from poms.common.fields import ExpressionField
from poms.common.models import EXPRESSION_FIELD_LENGTH
from poms.common.serializers import (
    ModelMetaSerializer,
    ModelWithTimeStampSerializer,
    ModelWithUserCodeSerializer,
    PomsClassSerializer,
)
from poms.common.storage import get_storage
from poms.counterparties.fields import CounterpartyField, ResponsibleField
from poms.currencies.fields import CurrencyDefault, CurrencyField
from poms.currencies.models import CurrencyHistory
from poms.instruments.fields import (
    InstrumentField,
    InstrumentTypeDefault,
    InstrumentTypeField,
    PricingConditionField,
    PricingPolicyField,
)
from poms.instruments.models import (
    AccrualCalculationModel,
    DailyPricingModel,
    Instrument,
    PaymentSizeDetail,
    Periodicity,
    PriceHistory,
    PricingCondition,
)
from poms.integrations.fields import (
    ComplexTransactionImportSchemeRestField,
    InstrumentDownloadSchemeField,
    PriceDownloadSchemeField,
)
from poms.integrations.models import (
    AbstractMapping,
    AccountClassifierMapping,
    AccountMapping,
    AccountTypeMapping,
    AccrualCalculationModelMapping,
    AccrualScheduleDownloadMethod,
    BloombergDataProviderCredential,
    ComplexTransactionImportScheme,
    ComplexTransactionImportSchemeCalculatedInput,
    ComplexTransactionImportSchemeField,
    ComplexTransactionImportSchemeInput,
    ComplexTransactionImportSchemeReconField,
    ComplexTransactionImportSchemeReconScenario,
    ComplexTransactionImportSchemeRuleScenario,
    ComplexTransactionImportSchemeSelectorValue,
    CounterpartyClassifierMapping,
    CounterpartyMapping,
    CurrencyMapping,
    DailyPricingModelMapping,
    DataProvider,
    FactorScheduleDownloadMethod,
    ImportConfig,
    InstrumentAttributeValueMapping,
    InstrumentClassifierMapping,
    InstrumentDownloadScheme,
    InstrumentDownloadSchemeAttribute,
    InstrumentDownloadSchemeInput,
    InstrumentMapping,
    InstrumentTypeMapping,
    MappingTable,
    MappingTableKeyValue,
    PaymentSizeDetailMapping,
    PeriodicityMapping,
    PortfolioClassifierMapping,
    PortfolioMapping,
    PriceDownloadScheme,
    PriceDownloadSchemeMapping,
    PricingConditionMapping,
    PricingPolicyMapping,
    ProviderClass,
    ResponsibleClassifierMapping,
    ResponsibleMapping,
    Strategy1Mapping,
    Strategy2Mapping,
    Strategy3Mapping,
    TransactionFileResult,
)
from poms.integrations.providers.base import ProviderException, get_provider
from poms.obj_attrs.fields import GenericAttributeTypeField, GenericClassifierField
from poms.obj_attrs.serializers import (
    GenericAttributeTypeSerializer,
    GenericClassifierSerializer,
    ModelWithAttributesSerializer,
)
from poms.portfolios.fields import PortfolioField
from poms.strategies.fields import Strategy1Field, Strategy2Field, Strategy3Field
from poms.users.fields import HiddenMemberField, MasterUserField
from poms.users.models import EcosystemDefault
from poms.users.utils import get_space_code_from_context
from poms_app import settings

_l = getLogger("poms.integrations")

storage = get_storage()


class ProviderClassSerializer(PomsClassSerializer):
    class Meta(PomsClassSerializer.Meta):
        model = ProviderClass


class FactorScheduleDownloadMethodSerializer(PomsClassSerializer):
    class Meta(PomsClassSerializer.Meta):
        model = FactorScheduleDownloadMethod


class AccrualScheduleDownloadMethodSerializer(PomsClassSerializer):
    class Meta(PomsClassSerializer.Meta):
        model = AccrualScheduleDownloadMethod


class BloombergDataProviderCredentialSerializer(serializers.ModelSerializer):
    master_user = MasterUserField()
    p12cert = serializers.FileField(allow_null=True, allow_empty_file=False, write_only=True)
    password = serializers.CharField(allow_null=True, allow_blank=True, write_only=True)

    class Meta:
        model = BloombergDataProviderCredential
        fields = [
            "id",
            "master_user",
            "p12cert",
            "password",
            "has_p12cert",
            "has_password",
            "is_valid",
        ]

    def create(self, validated_data):
        p12cert = validated_data.pop("p12cert", None)

        instance = super().create(validated_data)

        space_code = get_space_code_from_context(self.context)

        cert_file_path = f"{space_code}/brokers/bloomberg/{p12cert.name}"

        storage.save(cert_file_path, p12cert)

        instance.p12cert = cert_file_path
        instance.save()

        return instance

    def update(self, instance, validated_data):
        p12cert = validated_data.pop("p12cert", None)

        instance = super().update(instance, validated_data)

        space_code = get_space_code_from_context(self.context)

        cert_file_path = f"{space_code}/brokers/bloomberg/{p12cert.name}"

        storage.save(cert_file_path, p12cert)

        instance.p12cert = cert_file_path
        instance.save()

        return instance


class ImportConfigSerializer(serializers.ModelSerializer):
    master_user = MasterUserField()
    provider_object = ProviderClassSerializer(source="provider", read_only=True)
    p12cert = serializers.FileField(allow_null=True, allow_empty_file=False, write_only=True)
    password = serializers.CharField(allow_null=True, allow_blank=True, write_only=True)

    class Meta:
        model = ImportConfig
        fields = [
            "id",
            "master_user",
            "provider",
            "provider_object",
            "p12cert",
            "password",
            "has_p12cert",
            "has_password",
            "is_valid",
        ]


class InstrumentDownloadSchemeInputSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=False, required=False, allow_null=True)

    class Meta:
        model = InstrumentDownloadSchemeInput
        fields = ["id", "name", "name_expr", "field"]


class InstrumentDownloadSchemeAttributeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=False, required=False, allow_null=True)
    attribute_type = GenericAttributeTypeField()
    attribute_type_object = serializers.PrimaryKeyRelatedField(source="attribute_type", read_only=True)
    value = ExpressionField(max_length=EXPRESSION_FIELD_LENGTH, allow_blank=True)

    class Meta:
        model = InstrumentDownloadSchemeAttribute
        # attribute_type_model = InstrumentAttributeType
        fields = ["id", "attribute_type", "attribute_type_object", "value"]

    def __init__(self, *args, **kwargs):
        from poms.obj_attrs.serializers import GenericAttributeTypeViewSerializer

        super().__init__(*args, **kwargs)
        self.fields["attribute_type_object"] = GenericAttributeTypeViewSerializer(
            source="attribute_type", read_only=True
        )

    def validate(self, attrs):
        attribute_type = attrs.get("attribute_type", None)
        if attribute_type and (
            attribute_type.content_type_id != ContentType.objects.get(app_label="instruments", model="instrument").id
        ):
            self.fields["attribute_type"].fail("does_not_exist", pk_value=attribute_type.id)
        return attrs


class InstrumentDownloadSchemeSerializer(
    ModelWithUserCodeSerializer, ModelWithTimeStampSerializer, ModelMetaSerializer
):
    master_user = MasterUserField()
    provider_object = ProviderClassSerializer(source="provider", read_only=True)

    inputs = InstrumentDownloadSchemeInputSerializer(many=True, read_only=False)

    instrument_user_code = ExpressionField(max_length=EXPRESSION_FIELD_LENGTH, allow_blank=True)
    instrument_name = ExpressionField(max_length=EXPRESSION_FIELD_LENGTH)
    instrument_short_name = ExpressionField(max_length=EXPRESSION_FIELD_LENGTH, allow_blank=True)
    instrument_public_name = ExpressionField(max_length=EXPRESSION_FIELD_LENGTH, allow_blank=True)
    instrument_notes = ExpressionField(max_length=EXPRESSION_FIELD_LENGTH, allow_blank=True)
    instrument_type = ExpressionField(max_length=EXPRESSION_FIELD_LENGTH, allow_blank=True)
    pricing_currency = ExpressionField(max_length=EXPRESSION_FIELD_LENGTH, allow_blank=True)
    price_multiplier = ExpressionField(max_length=EXPRESSION_FIELD_LENGTH, allow_blank=True)
    accrued_currency = ExpressionField(max_length=EXPRESSION_FIELD_LENGTH, allow_blank=True)
    accrued_multiplier = ExpressionField(max_length=EXPRESSION_FIELD_LENGTH, allow_blank=True)
    maturity_date = ExpressionField(max_length=EXPRESSION_FIELD_LENGTH, allow_blank=True)
    maturity_price = ExpressionField(max_length=EXPRESSION_FIELD_LENGTH, allow_blank=True)
    user_text_1 = ExpressionField(max_length=EXPRESSION_FIELD_LENGTH, allow_blank=True)
    user_text_2 = ExpressionField(max_length=EXPRESSION_FIELD_LENGTH, allow_blank=True)
    user_text_3 = ExpressionField(max_length=EXPRESSION_FIELD_LENGTH, allow_blank=True)

    payment_size_detail_object = serializers.PrimaryKeyRelatedField(source="payment_size_detail", read_only=True)
    factor_schedule_method_object = serializers.PrimaryKeyRelatedField(source="factor_schedule_method", read_only=True)
    accrual_calculation_schedule_method_object = serializers.PrimaryKeyRelatedField(
        source="accrual_calculation_schedule_method", read_only=True
    )

    attributes = InstrumentDownloadSchemeAttributeSerializer(many=True, read_only=False)

    class Meta:
        model = InstrumentDownloadScheme
        fields = [
            "id",
            "master_user",
            "mode",
            "user_code",
            "configuration_code",
            "name",
            "short_name",
            "public_name",
            "notes",
            "provider",
            "provider_object",
            "inputs",
            "reference_for_pricing",
            "instrument_user_code",
            "instrument_name",
            "instrument_short_name",
            "instrument_public_name",
            "instrument_notes",
            "instrument_type",
            "pricing_currency",
            "price_multiplier",
            "accrued_currency",
            "accrued_multiplier",
            "user_text_1",
            "user_text_2",
            "user_text_3",
            "maturity_date",
            "maturity_price",
            "payment_size_detail",
            "payment_size_detail_object",
            "default_price",
            "default_accrued",
            "factor_schedule_method",
            "factor_schedule_method_object",
            "accrual_calculation_schedule_method",
            "accrual_calculation_schedule_method_object",
            "attributes",
        ]

    def __init__(self, *args, **kwargs):
        from poms.instruments.serializers import PaymentSizeDetailSerializer

        super().__init__(*args, **kwargs)

        self.fields["payment_size_detail_object"] = PaymentSizeDetailSerializer(
            source="payment_size_detail", read_only=True
        )
        self.fields["factor_schedule_method_object"] = FactorScheduleDownloadMethodSerializer(
            source="factor_schedule_method", read_only=True
        )
        self.fields["accrual_calculation_schedule_method_object"] = AccrualScheduleDownloadMethodSerializer(
            source="accrual_calculation_schedule_method", read_only=True
        )

    def create(self, validated_data):
        inputs = validated_data.pop("inputs", None) or []
        attributes = validated_data.pop("attributes", None) or []
        instance = super().create(validated_data)
        self.save_inputs(instance, inputs)
        self.save_attributes(instance, attributes)
        return instance

    def update(self, instance, validated_data):
        inputs = validated_data.pop("inputs", empty)
        attributes = validated_data.pop("attributes", None) or []
        instance = super().update(instance, validated_data)
        if inputs is not empty:
            self.save_inputs(instance, inputs)
        if attributes is not empty:
            self.save_attributes(instance, attributes)
        return instance

    def save_inputs(self, instance, inputs):
        pk_set = set()
        for input_values in inputs:
            input_id = input_values.pop("id", None)
            input0 = None
            if input_id:
                with contextlib.suppress(ObjectDoesNotExist):
                    input0 = instance.inputs.get(pk=input_id)
            if input0 is None:
                input0 = InstrumentDownloadSchemeInput(scheme=instance)
            for name, value in input_values.items():
                setattr(input0, name, value)
            input0.save()
            pk_set.add(input0.id)
        instance.inputs.exclude(pk__in=pk_set).delete()

    def save_attributes(self, instance, attributes):
        pk_set = set()
        for attr_values in attributes:
            attribute_type = attr_values["attribute_type"]
            try:
                attr = instance.attributes.get(attribute_type=attribute_type)
            except ObjectDoesNotExist:
                attr = None
            if attr is None:
                attr = InstrumentDownloadSchemeAttribute(scheme=instance)
            for name, value in attr_values.items():
                setattr(attr, name, value)
            attr.save()
            pk_set.add(attr.id)
        instance.attributes.exclude(pk__in=pk_set).delete()


class InstrumentDownloadSchemeLightSerializer(serializers.ModelSerializer):
    master_user = MasterUserField()
    provider_object = ProviderClassSerializer(source="provider", read_only=True)

    class Meta:
        model = InstrumentDownloadScheme
        fields = [
            "id",
            "master_user",
            "user_code",
            "name",
            "short_name",
            "provider",
            "provider_object",
        ]


class PriceDownloadSchemeSerializer(serializers.ModelSerializer):
    master_user = MasterUserField()
    provider_object = ProviderClassSerializer(source="provider", read_only=True)

    class Meta:
        model = PriceDownloadScheme
        fields = [
            "id",
            "master_user",
            "scheme_name",
            "provider",
            "provider_object",
            "bid0",
            "bid1",
            "bid2",
            "bid_multiplier",
            "ask0",
            "ask1",
            "ask2",
            "ask_multiplier",
            "last",
            "last_multiplier",
            "mid",
            "mid_multiplier",
            "bid_history",
            "bid_history_multiplier",
            "ask_history",
            "ask_history_multiplier",
            "mid_history",
            "mid_history_multiplier",
            "last_history",
            "last_history_multiplier",
            "currency_fxrate",
            "currency_fxrate_multiplier",
        ]


class PriceDownloadSchemeViewSerializer(serializers.ModelSerializer):
    provider_object = ProviderClassSerializer(source="provider", read_only=True)

    class Meta:
        model = PriceDownloadScheme
        fields = [
            "id",
            "scheme_name",
            "provider",
            "provider_object",
        ]


# ------------------


class MappingTableKeyValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = MappingTableKeyValue
        fields = [
            "key",
            "value",
        ]


class MappingTableSerializer(ModelMetaSerializer):
    master_user = MasterUserField()

    items = MappingTableKeyValueSerializer(many=True)

    class Meta:
        model = MappingTable
        fields = [
            "id",
            "master_user",
            "name",
            "user_code",
            "short_name",
            "notes",
            "configuration_code",
            "items",
        ]

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        mapping_table = MappingTable.objects.create(**validated_data)

        for item_data in items_data:
            MappingTableKeyValue.objects.create(mapping_table=mapping_table, **item_data)

        return mapping_table

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items")
        instance.name = validated_data.get("name", instance.name)
        instance.short_name = validated_data.get("short_name", instance.short_name)
        instance.notes = validated_data.get("notes", instance.notes)

        instance.save()

        _l.info(f"items_data {items_data}")

        MappingTableKeyValue.objects.filter(mapping_table=instance).delete()

        for item_data in items_data:
            MappingTableKeyValue.objects.create(mapping_table=instance, **item_data)

        return MappingTable.objects.get(pk=instance.pk)


class AbstractMappingSerializer(serializers.ModelSerializer):
    master_user = MasterUserField()

    class Meta:
        model = AbstractMapping
        fields = [
            "id",
            "master_user",
            "provider",
            "value",
            "content_object",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["provider_object"] = ProviderClassSerializer(source="provider", read_only=True)

        content_object_view_serializer_class = self.get_content_object_view_serializer()
        self.fields["content_object_object"] = content_object_view_serializer_class(
            source="content_object", read_only=True
        )

        model = self.Meta.model
        self.validators.append(
            UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=("master_user", "provider", "value"),
                message=gettext_lazy("The fields provider and value must make a unique set."),
            )
        )

    def get_content_object_view_serializer(self):
        raise NotImplementedError()


class AbstractClassifierMappingSerializer(serializers.ModelSerializer):
    master_user = MasterUserField()

    # currency = CurrencyField()
    # currency_object = serializers.PrimaryKeyRelatedField(source='currency', read_only=True)

    class Meta:
        model = AbstractMapping
        fields = [
            "id",
            "master_user",
            "provider",
            "value",
            "attribute_type",
            "content_object",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["provider_object"] = ProviderClassSerializer(source="provider", read_only=True)

        self.fields["attribute_type_object"] = GenericAttributeTypeSerializer(source="attribute_type", read_only=True)

        self.fields["content_object_object"] = GenericClassifierSerializer(source="content_object", read_only=True)

        model = self.Meta.model
        self.validators.append(
            UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=("master_user", "provider", "value", "attribute_type"),
                message=gettext_lazy("The fields provider, value and attribute_type must make a unique set."),
            )
        )


class CurrencyMappingSerializer(AbstractMappingSerializer):
    content_object = CurrencyField()

    class Meta(AbstractMappingSerializer.Meta):
        model = CurrencyMapping

    def get_content_object_view_serializer(self):
        from poms.currencies.serializers import CurrencyViewSerializer

        return CurrencyViewSerializer


class PricingPolicyMappingSerializer(AbstractMappingSerializer):
    content_object = PricingPolicyField()

    class Meta(AbstractMappingSerializer.Meta):
        model = PricingPolicyMapping

    def get_content_object_view_serializer(self):
        from poms.instruments.serializers import PricingPolicyViewSerializer

        return PricingPolicyViewSerializer


class AccountTypeMappingSerializer(AbstractMappingSerializer):
    content_object = AccountTypeField()

    class Meta(AbstractMappingSerializer.Meta):
        model = AccountTypeMapping

    def get_content_object_view_serializer(self):
        from poms.accounts.serializers import AccountTypeViewSerializer

        return AccountTypeViewSerializer


class InstrumentTypeMappingSerializer(AbstractMappingSerializer):
    content_object = InstrumentTypeField()

    class Meta(AbstractMappingSerializer.Meta):
        model = InstrumentTypeMapping

    def get_content_object_view_serializer(self):
        from poms.instruments.serializers import InstrumentTypeViewSerializer

        return InstrumentTypeViewSerializer


class InstrumentAttributeValueMappingSerializer(AbstractMappingSerializer):
    content_object = GenericAttributeTypeField()
    classifier = GenericClassifierField(allow_empty=True, allow_null=True)

    class Meta(AbstractMappingSerializer.Meta):
        model = InstrumentAttributeValueMapping
        fields = AbstractMappingSerializer.Meta.fields + [
            "value_string",
            "value_float",
            "value_date",
            "classifier",
        ]

    def __init__(self, *args, **kwargs):
        from poms.obj_attrs.serializers import GenericClassifierViewSerializer

        super().__init__(*args, **kwargs)
        self.fields["classifier_object"] = GenericClassifierViewSerializer(source="classifier", read_only=True)

    def get_content_object_view_serializer(self):
        from poms.obj_attrs.serializers import GenericAttributeTypeViewSerializer

        return GenericAttributeTypeViewSerializer

    def validate(self, attrs):
        content_object = attrs.get("content_object", None)
        if content_object and (
            content_object.content_type_id != ContentType.objects.get(app_label="instruments", model="instrument").id
        ):
            self.fields["content_object"].fail("does_not_exist", pk_value=content_object.id)

        classifier = attrs.get("classifier", None)
        if classifier and classifier.attribute_type_id != content_object.id:
            raise serializers.ValidationError({"classifier": "Invalid classifier"})

        return attrs


class AccrualCalculationModelMappingSerializer(AbstractMappingSerializer):
    content_object = serializers.PrimaryKeyRelatedField(queryset=AccrualCalculationModel.objects.all())

    class Meta(AbstractMappingSerializer.Meta):
        model = AccrualCalculationModelMapping

    def get_content_object_view_serializer(self):
        from poms.instruments.serializers import AccrualCalculationModelSerializer

        return AccrualCalculationModelSerializer


class PeriodicityMappingSerializer(AbstractMappingSerializer):
    content_object = serializers.PrimaryKeyRelatedField(queryset=Periodicity.objects.all())

    class Meta(AbstractMappingSerializer.Meta):
        model = PeriodicityMapping

    def get_content_object_view_serializer(self):
        from poms.instruments.serializers import PeriodicitySerializer

        return PeriodicitySerializer


class AccountMappingSerializer(AbstractMappingSerializer):
    content_object = AccountField()

    class Meta(AbstractMappingSerializer.Meta):
        model = AccountMapping

    def get_content_object_view_serializer(self):
        from poms.accounts.serializers import AccountViewSerializer

        return AccountViewSerializer


class AccountClassifierMappingSerializer(AbstractClassifierMappingSerializer):
    attribute_type = GenericAttributeTypeField()
    content_object = GenericClassifierField()

    class Meta(AbstractClassifierMappingSerializer.Meta):
        model = AccountClassifierMapping


class InstrumentMappingSerializer(AbstractMappingSerializer):
    content_object = InstrumentField()

    class Meta(AbstractMappingSerializer.Meta):
        model = InstrumentMapping

    def get_content_object_view_serializer(self):
        from poms.instruments.serializers import InstrumentViewSerializer

        return InstrumentViewSerializer


class InstrumentClassifierMappingSerializer(AbstractClassifierMappingSerializer):
    attribute_type = GenericAttributeTypeField()
    content_object = GenericClassifierField()

    class Meta(AbstractClassifierMappingSerializer.Meta):
        model = InstrumentClassifierMapping


class CounterpartyMappingSerializer(AbstractMappingSerializer):
    content_object = CounterpartyField()

    class Meta(AbstractMappingSerializer.Meta):
        model = CounterpartyMapping

    def get_content_object_view_serializer(self):
        from poms.counterparties.serializers import CounterpartyViewSerializer

        return CounterpartyViewSerializer


class CounterpartyClassifierMappingSerializer(AbstractClassifierMappingSerializer):
    attribute_type = GenericAttributeTypeField()
    content_object = GenericClassifierField()

    class Meta(AbstractClassifierMappingSerializer.Meta):
        model = CounterpartyClassifierMapping


class ResponsibleMappingSerializer(AbstractMappingSerializer):
    content_object = ResponsibleField()

    class Meta(AbstractMappingSerializer.Meta):
        model = ResponsibleMapping

    def get_content_object_view_serializer(self):
        from poms.counterparties.serializers import ResponsibleViewSerializer

        return ResponsibleViewSerializer


class ResponsibleClassifierMappingSerializer(AbstractClassifierMappingSerializer):
    attribute_type = GenericAttributeTypeField()
    content_object = GenericClassifierField()

    class Meta(AbstractClassifierMappingSerializer.Meta):
        model = ResponsibleClassifierMapping


class PortfolioMappingSerializer(AbstractMappingSerializer):
    content_object = PortfolioField()

    class Meta(AbstractMappingSerializer.Meta):
        model = PortfolioMapping

    def get_content_object_view_serializer(self):
        from poms.portfolios.serializers import PortfolioViewSerializer

        return PortfolioViewSerializer


class PortfolioClassifierMappingSerializer(AbstractClassifierMappingSerializer):
    attribute_type = GenericAttributeTypeField()
    content_object = GenericClassifierField()

    class Meta(AbstractClassifierMappingSerializer.Meta):
        model = PortfolioClassifierMapping


class Strategy1MappingSerializer(AbstractMappingSerializer):
    content_object = Strategy1Field()

    class Meta(AbstractMappingSerializer.Meta):
        model = Strategy1Mapping

    def get_content_object_view_serializer(self):
        from poms.strategies.serializers import Strategy1ViewSerializer

        return Strategy1ViewSerializer


class Strategy2MappingSerializer(AbstractMappingSerializer):
    content_object = Strategy2Field()

    class Meta(AbstractMappingSerializer.Meta):
        model = Strategy2Mapping

    def get_content_object_view_serializer(self):
        from poms.strategies.serializers import Strategy2ViewSerializer

        return Strategy2ViewSerializer


class Strategy3MappingSerializer(AbstractMappingSerializer):
    content_object = Strategy3Field()

    class Meta(AbstractMappingSerializer.Meta):
        model = Strategy3Mapping

    def get_content_object_view_serializer(self):
        from poms.strategies.serializers import Strategy3ViewSerializer

        return Strategy3ViewSerializer


class DailyPricingModelMappingSerializer(AbstractMappingSerializer):
    content_object = serializers.PrimaryKeyRelatedField(queryset=DailyPricingModel.objects.all())

    class Meta(AbstractMappingSerializer.Meta):
        model = DailyPricingModelMapping

    def get_content_object_view_serializer(self):
        from poms.instruments.serializers import DailyPricingModelSerializer

        return DailyPricingModelSerializer


class PaymentSizeDetailMappingSerializer(AbstractMappingSerializer):
    content_object = serializers.PrimaryKeyRelatedField(queryset=PaymentSizeDetail.objects.all())

    class Meta(AbstractMappingSerializer.Meta):
        model = PaymentSizeDetailMapping

    def get_content_object_view_serializer(self):
        from poms.instruments.serializers import PaymentSizeDetailSerializer

        return PaymentSizeDetailSerializer


class PricingConditionMappingSerializer(AbstractMappingSerializer):
    content_object = serializers.PrimaryKeyRelatedField(queryset=PricingCondition.objects.all())

    class Meta(AbstractMappingSerializer.Meta):
        model = PricingConditionMapping

    def get_content_object_view_serializer(self):
        from poms.instruments.serializers import PricingConditionSerializer

        return PricingConditionSerializer


class PriceDownloadSchemeMappingSerializer(AbstractMappingSerializer):
    content_object = PriceDownloadSchemeField()

    class Meta(AbstractMappingSerializer.Meta):
        model = PriceDownloadSchemeMapping

    def get_content_object_view_serializer(self):
        return PriceDownloadSchemeViewSerializer


class ImportInstrumentViewSerializer(ModelWithAttributesSerializer, ModelWithUserCodeSerializer):
    instrument_type = InstrumentTypeField(default=InstrumentTypeDefault())
    instrument_type_object = serializers.PrimaryKeyRelatedField(source="instrument_type", read_only=True)
    pricing_currency = CurrencyField(default=CurrencyDefault())
    pricing_currency_object = serializers.PrimaryKeyRelatedField(source="pricing_currency", read_only=True)
    accrued_currency = CurrencyField(default=CurrencyDefault())
    accrued_currency_object = serializers.PrimaryKeyRelatedField(source="accrued_currency", read_only=True)
    payment_size_detail_object = serializers.PrimaryKeyRelatedField(source="payment_size_detail", read_only=True)
    accrual_calculation_schedules = serializers.SerializerMethodField()
    factor_schedules = serializers.SerializerMethodField()
    event_schedules = serializers.PrimaryKeyRelatedField(read_only=True, many=True)
    pricing_condition = PricingConditionField()
    accrual_events = serializers.SerializerMethodField()

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
            "is_active",
            "is_deleted",
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
            "maturity_date",
            "pricing_condition",
            # 'manual_pricing_formulas',
            "accrual_calculation_schedules",
            "factor_schedules",
            "event_schedules",
            "accrual_events",
            # 'attributes',
            "co_directional_exposure_currency",
            "counter_directional_exposure_currency",
        ]

    def __init__(self, *args, **kwargs):
        from poms.currencies.serializers import CurrencyViewSerializer
        from poms.instruments.serializers import (
            EventScheduleSerializer,
            InstrumentTypeViewSerializer,
            PaymentSizeDetailSerializer,
        )

        super().__init__(*args, **kwargs)

        self.fields["pricing_currency_object"] = CurrencyViewSerializer(source="pricing_currency", read_only=True)
        self.fields["accrued_currency_object"] = CurrencyViewSerializer(source="accrued_currency", read_only=True)

        self.fields["instrument_type_object"] = InstrumentTypeViewSerializer(source="instrument_type", read_only=True)
        self.fields["payment_size_detail_object"] = PaymentSizeDetailSerializer(
            source="payment_size_detail", read_only=True
        )
        self.fields["event_schedules"] = EventScheduleSerializer(many=True, required=False, allow_null=True)

        self.fields["attributes"] = serializers.SerializerMethodField()

    def get_accrual_calculation_schedules(self, obj):
        from poms.instruments.serializers import AccrualCalculationScheduleSerializer

        if hasattr(obj, "_accrual_calculation_schedules"):
            l = obj._accrual_calculation_schedules  # noqa: E741
        else:
            l = obj.accrual_calculation_schedules.all()  # noqa: E741
        return AccrualCalculationScheduleSerializer(instance=l, many=True, read_only=True, context=self.context).data

    def get_factor_schedules(self, obj):
        from poms.instruments.serializers import InstrumentFactorScheduleSerializer

        if hasattr(obj, "_factor_schedules"):
            l = obj._factor_schedules  # noqa: E741
        else:
            l = obj.factor_schedules.all()  # noqa: E741
        return InstrumentFactorScheduleSerializer(instance=l, many=True, read_only=True, context=self.context).data

    def get_attributes(self, obj):
        from poms.obj_attrs.serializers import GenericAttributeSerializer

        _l.warning("get_attributes: _attributes=%s", hasattr(obj, "_attributes"))

        l = obj._attributes if hasattr(obj, "_attributes") else obj.attributes.all()  # noqa: E741

        return GenericAttributeSerializer(instance=l, many=True, read_only=True, context=self.context).data

    def get_accrual_events(self, obj):
        from poms.instruments.serializers import AccrualEventSerializer

        accrual_events = obj.accrual_events.all()
        return AccrualEventSerializer(instance=accrual_events, many=True, read_only=True, context=self.context).data


class ImportInstrumentEntry:
    def __init__(
        self,
        master_user=None,
        member=None,
        instrument_code=None,
        instrument_name=None,
        instrument_type_code=None,
        instrument_download_scheme=None,
        task=None,
        task_result_overrides=None,
        instrument=None,
        errors=None,
    ):
        self.master_user = master_user
        self.member = member
        self.instrument_code = instrument_code
        self.instrument_name = instrument_name
        self.instrument_type_code = instrument_type_code
        self.instrument_download_scheme = instrument_download_scheme
        self.task = task
        self._task_object = None
        self.task_result_overrides = task_result_overrides
        self.instrument = instrument
        self.errors = errors

    @property
    def task_object(self):
        if not self._task_object and self.task:
            self._task_object = CeleryTask.objects.get(pk=self.task)
        return self._task_object

    @task_object.setter
    def task_object(self, value):
        self._task_object = value
        self.task = getattr(value, "pk", None)


class UnifiedDataEntry:
    def __init__(
        self,
        master_user=None,
        member=None,
        id=None,
        entity_type=None,
        task=None,
        task_result_overrides=None,
        errors=None,
    ):
        self.master_user = master_user
        self.member = member
        self.id = id
        self.entity_type = entity_type
        self.task = task
        self._task_object = None
        self.task_result_overrides = task_result_overrides
        self.errors = errors

    @property
    def task_object(self):
        if not self._task_object and self.task:
            self._task_object = CeleryTask.objects.get(pk=self.task)
        return self._task_object

    @task_object.setter
    def task_object(self, value):
        self._task_object = value
        self.task = getattr(value, "pk", None)


class ImportInstrumentSerializer(serializers.Serializer):
    master_user = MasterUserField()
    member = HiddenMemberField()
    instrument_download_scheme = InstrumentDownloadSchemeField()
    instrument_code = serializers.CharField(required=True)

    task = serializers.IntegerField(required=False, allow_null=True)
    task_object = CeleryTaskSerializer(read_only=True)
    task_result = serializers.SerializerMethodField()
    task_result_overrides = serializers.JSONField(default={}, allow_null=True)

    # instrument = serializers.ReadOnlyField()
    errors = serializers.ReadOnlyField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["instrument"] = ImportInstrumentViewSerializer(read_only=True)

    def validate(self, attrs):
        master_user = attrs["master_user"]
        instrument_download_scheme = attrs["instrument_download_scheme"]
        instrument_code = attrs["instrument_code"]

        try:
            provider = get_provider(master_user=master_user, provider=instrument_download_scheme.provider_id)
        except ProviderException as e:
            raise serializers.ValidationError(
                {
                    "instrument_download_scheme": gettext_lazy('Check "%(provider)s" provider configuration.')
                    % {"provider": instrument_download_scheme.provider}
                }
            ) from e

        if not provider.is_valid_reference(instrument_code):
            raise serializers.ValidationError(
                {
                    "instrument_code": gettext_lazy('Invalid value for "%(provider)s" provider.')
                    % {
                        "reference": instrument_code,
                        "provider": instrument_download_scheme.provider,
                    }
                }
            )

        task_result_overrides = attrs.get("task_result_overrides", None) or {}
        if isinstance(task_result_overrides, str):
            try:
                task_result_overrides = json.loads(task_result_overrides)
            except ValueError as e:
                raise serializers.ValidationError(
                    {"task_result_overrides": gettext_lazy("Invalid JSON string.")}
                ) from e
        if not isinstance(task_result_overrides, dict):
            raise serializers.ValidationError({"task_result_overrides": gettext_lazy("Invalid value.")})

        task_result_overrides = {
            k: v for k, v in task_result_overrides.items() if k in instrument_download_scheme.fields
        }
        attrs["task_result_overrides"] = task_result_overrides
        return attrs

    def create(self, validated_data: dict) -> ImportInstrumentEntry:
        from poms.integrations.tasks import download_instrument

        task_result_overrides = validated_data.get("task_result_overrides")
        instance = ImportInstrumentEntry(**validated_data)
        if instance.task:
            task, instrument, errors = download_instrument(
                task=instance.task_object,
                value_overrides=task_result_overrides,
            )
        else:
            task, instrument, errors = download_instrument(
                instrument_code=instance.instrument_code,
                instrument_download_scheme=instance.instrument_download_scheme,
                master_user=instance.master_user,
                member=instance.member,
            )

        instance.task_object = task
        instance.instrument = instrument
        instance.errors = errors
        return instance

    def get_task_result(self, obj):
        if obj.task_object.status != CeleryTask.STATUS_DONE:
            return {}

        fields = obj.task_object.options_object["fields"]
        result_object = obj.task_object.result_object
        return {k: v for k, v in result_object.items() if k in fields}


def check_instrument_type(instrument_type: str) -> str:
    if "bond" in instrument_type:
        return "bond"
    elif "stock" in instrument_type:
        return "stock"

    raise ValidationError(f"invalid instrument_type_code='{instrument_type}'")


# database import FN-1736
class ImportInstrumentDatabaseSerializer(serializers.Serializer):
    master_user = MasterUserField()
    member = HiddenMemberField()
    user_code = serializers.CharField(required=True)
    instrument_type_user_code = serializers.CharField(
        required=True,
        validators=[check_instrument_type],
    )
    task = serializers.IntegerField(required=False, allow_null=True)
    result_id = serializers.IntegerField(required=False, allow_null=True)
    errors = serializers.ReadOnlyField()

    def create_task(self, validated_data: dict) -> dict:
        from poms.integrations.tasks import (
            import_instrument_finmars_database,
            ttl_finisher,
        )

        task = CeleryTask.objects.create(
            status=CeleryTask.STATUS_PENDING,
            master_user=validated_data["master_user"],
            member=validated_data["member"],
            verbose_name="Import Instrument From Finmars Database",
            function_name="import_instrument_finmars_database",
            type="import_from_database",
            ttl=settings.FINMARS_DATABASE_TIMEOUT,
        )
        task.options_object = {  # params expected in finmars-database view
            "user_code": validated_data["user_code"],
            "type_user_code": validated_data["instrument_type_user_code"],
        }
        task.result_object = {"task": task.id}
        task.save()
        ttl_finisher.apply_async(
            kwargs={
                "task_id": task.id,
                "context": {
                    "space_code": task.master_user.space_code,
                    "realm_code": task.master_user.realm_code,
                },
            },
            countdown=task.ttl,
        )

        _l.info(f"{self.__class__.__name__} created task.id={task.id}")

        import_instrument_finmars_database(task.id)

        task.refresh_from_db()

        result = task.result_object
        result["errors"] = task.error_message

        _l.info(f"{self.__class__.__name__} result={result}")

        return result


# database import FN-1736
class ImportCurrencyDatabaseSerializer(serializers.Serializer):
    master_user = MasterUserField()
    member = HiddenMemberField()
    user_code = serializers.CharField(required=True)
    task = serializers.IntegerField(required=False, allow_null=True)
    result_id = serializers.IntegerField(required=False, allow_null=True)
    errors = serializers.ReadOnlyField()

    def create_task(self, validated_data: dict) -> dict:
        from poms.integrations.tasks import (
            import_currency_finmars_database,
            ttl_finisher,
        )

        task = CeleryTask.objects.create(
            status=CeleryTask.STATUS_PENDING,
            master_user=validated_data["master_user"],
            member=validated_data["member"],
            verbose_name="Import Currency From Finmars Database",
            function_name="import_currency_finmars_database",
            type="import_from_database",
            ttl=settings.FINMARS_DATABASE_TIMEOUT,
        )
        task.options_object = {  # params expected in finmars-database view
            "user_code": validated_data["user_code"],
        }
        task.result_object = {"task": task.id}
        task.save()
        ttl_finisher.apply_async(
            kwargs={
                "task_id": task.id,
                "context": {
                    "space_code": task.master_user.space_code,
                    "realm_code": task.master_user.realm_code,
                },
            },
            countdown=task.ttl,
        )

        _l.info(f"{self.__class__.__name__} created task.id={task.id}")

        import_currency_finmars_database(task.id)

        task.refresh_from_db()

        result = task.result_object
        result["errors"] = task.error_message

        _l.info(f"{self.__class__.__name__} result={result}")

        return result


# database import FN-1736
class ImportCompanyDatabaseSerializer(serializers.Serializer):
    master_user = MasterUserField()
    member = HiddenMemberField()
    company_id = serializers.CharField(required=True)
    task = serializers.IntegerField(required=False, allow_null=True)
    result_id = serializers.IntegerField(required=False, allow_null=True)
    errors = serializers.ReadOnlyField()

    def create_task(self, validated_data: dict) -> dict:
        from poms.integrations.tasks import (
            import_company_finmars_database,
            ttl_finisher,
        )

        task = CeleryTask.objects.create(
            status=CeleryTask.STATUS_PENDING,
            master_user=validated_data["master_user"],
            member=validated_data["member"],
            verbose_name="Import Company From Finmars Database",
            function_name="import_company_finmars_database",
            type="import_from_database",
            ttl=settings.FINMARS_DATABASE_TIMEOUT,
        )
        task.options_object = {  # params expected in finmars-database view
            "company_id": validated_data["company_id"],
        }
        task.result_object = {"task": task.id}
        task.save()
        ttl_finisher.apply_async(
            kwargs={
                "task_id": task.id,
                "context": {
                    "space_code": task.master_user.space_code,
                    "realm_code": task.master_user.realm_code,
                },
            },
            countdown=task.ttl,
        )

        _l.info(f"{self.__class__.__name__} created task.id={task.id}")

        import_company_finmars_database(task.id)

        task.refresh_from_db()

        result = task.result_object
        result["errors"] = task.error_message

        _l.info(f"{self.__class__.__name__} result={result}")

        return result


# database import FN-1736
class ImportPriceDatabaseSerializer(serializers.Serializer):
    master_user = MasterUserField()
    member = HiddenMemberField()
    reference = serializers.CharField(required=True)
    date_from = serializers.DateField(required=True)
    date_to = serializers.DateField(required=True)
    task = serializers.IntegerField(required=False, allow_null=True)
    result_id = serializers.IntegerField(required=False, allow_null=True)
    errors = serializers.ReadOnlyField()

    def validate(self, attrs):
        if attrs["date_from"] > attrs["date_to"]:
            raise ValidationError("invalid dates range!")

        return attrs

    def create_task(self, validated_data: dict) -> dict:
        from poms.integrations.tasks import import_price_finmars_database, ttl_finisher

        task = CeleryTask.objects.create(
            status=CeleryTask.STATUS_PENDING,
            master_user=validated_data["master_user"],
            member=validated_data["member"],
            verbose_name="Import Price From Finmars Database",
            function_name="import_price_finmars_database",
            type="import_from_database",
            ttl=settings.FINMARS_DATABASE_TIMEOUT,
        )
        task.options_object = {  # params expected in finmars-database view
            "reference": validated_data["reference"],
            "date_from": validated_data["date_from"],
            "date_to": validated_data["date_to"],
        }
        task.result_object = {"task": task.id}
        task.save()
        ttl_finisher.apply_async(
            kwargs={
                "task_id": task.id,
                "context": {
                    "space_code": task.master_user.space_code,
                    "realm_code": task.master_user.realm_code,
                },
            },
            countdown=task.ttl,
        )

        _l.info(f"{self.__class__.__name__} created task.id={task.id}")

        import_price_finmars_database(task.id)

        task.refresh_from_db()

        result = task.result_object
        result["errors"] = task.error_message

        _l.info(f"{self.__class__.__name__} result={result}")

        return result


# database import callbacks FN-1736
class CallBackDataDictRequestSerializer(serializers.Serializer):
    request_id = serializers.IntegerField(required=True, min_value=1)
    task_id = serializers.IntegerField(required=True, allow_null=True)
    data = serializers.DictField(required=True, allow_null=True)

    def validate(self, attrs: dict) -> dict:
        task = CeleryTask.objects.filter(id=attrs["request_id"]).first()
        if not task:
            err_msg = f"no celery task with id={attrs['request_id']}"
            raise ValidationError({"request_id": "invalid"}, err_msg)

        attrs["task"] = task

        if (attrs["task_id"] is None) and (attrs["data"] is None):
            err_msg = "data & task_id can't be both null"
            raise ValidationError({"task_id": "null", "data": "null"}, err_msg)

        return attrs


class ImportUnifiedDataProviderSerializer(serializers.Serializer):
    master_user = MasterUserField()
    member = HiddenMemberField()
    id = serializers.CharField(required=True, initial="-")
    entity_type = serializers.CharField(required=True, initial="-")
    task = serializers.IntegerField(required=False, allow_null=True)
    result_id = serializers.IntegerField(required=False, allow_null=True)
    errors = serializers.ReadOnlyField()

    def create(self, validated_data):
        from poms.integrations.tasks import download_unified_data

        instance = UnifiedDataEntry(**validated_data)

        task, errors = download_unified_data(
            id=instance.id,
            entity_type=instance.entity_type,
            master_user=instance.master_user,
            member=instance.member,
        )
        instance.task_object = task
        instance.errors = errors

        if task and task.result_object:
            instance.result_id = task.result_object["id"]

        return instance


class ImportTestCertificate:
    def __init__(self, master_user=None, member=None, provider_id=None, task=None):
        self.master_user = master_user
        self.member = member
        self.provider_id = provider_id

        self.task = task
        self._task_object = None

    @property
    def task_object(self):
        if not self._task_object and self.task:
            self._task_object = CeleryTask.objects.get(pk=self.task)
        return self._task_object

    @task_object.setter
    def task_object(self, value):
        self._task_object = value
        self.task = getattr(value, "pk", None)


class ImportPricingEntry:
    def __init__(
        self,
        master_user=None,
        member=None,
        instruments=None,
        currencies=None,
        date_from=None,
        date_to=None,
        is_yesterday=None,
        balance_date=None,
        fill_days=None,
        override_existed=False,
        task=None,
        instrument_histories=None,
        currency_histories=None,
    ):
        self.master_user = master_user
        self.member = member
        self.instruments = instruments
        self.currencies = currencies

        self.date_from = date_from
        self.date_to = date_to
        self.is_yesterday = is_yesterday
        self.balance_date = balance_date
        self.fill_days = fill_days
        self.override_existed = override_existed

        self.task = task
        self._task_object = None
        self.instrument_histories = instrument_histories
        self.currency_histories = currency_histories

    @property
    def task_object(self):
        if not self._task_object and self.task:
            self._task_object = CeleryTask.objects.get(pk=self.task)
        return self._task_object

    @task_object.setter
    def task_object(self, value):
        self._task_object = value
        self.task = getattr(value, "pk", None)

    @property
    def errors(self):
        t = self.task_object
        return t.options_object.get("errors", None) if t else None

    @property
    def instrument_price_missed(self):
        if not self.is_yesterday:
            return []
        result = getattr(self.task_object, "result_object", {})
        instrument_price_missed = result.get("instrument_price_missed", [])
        if instrument_price_missed:
            instruments_pk = [instr_id for instr_id, _ in instrument_price_missed]
            existed_instrument_prices = {
                (p.instrument_id, p.pricing_policy_id): p
                for p in PriceHistory.objects.filter(instrument__in=instruments_pk, date=self.date_to)
            }

            instrument_price_missed_objects = []
            for instrument_id, pricing_policy_id in instrument_price_missed:
                op = existed_instrument_prices.get((instrument_id, pricing_policy_id), None)
                if op is None:
                    op = PriceHistory(
                        instrument_id=instrument_id,
                        pricing_policy_id=pricing_policy_id,
                        date=self.date_to,
                    )
                instrument_price_missed_objects.append(op)
            return instrument_price_missed_objects
        return []

    @property
    def currency_price_missed(self):
        if not self.is_yesterday:
            return []
        result = getattr(self.task_object, "result_object", {})
        currency_price_missed = result.get("currency_price_missed", None)
        if currency_price_missed:
            currencies_pk = [instr_id for instr_id, _ in currency_price_missed]
            existed_currency_prices = {
                (p.currency_id, p.pricing_policy_id): p
                for p in CurrencyHistory.objects.filter(currency__in=currencies_pk, date=self.date_to)
            }
            currency_price_missed_objects = []
            for currency_id, pricing_policy_id in currency_price_missed:
                op = existed_currency_prices.get((currency_id, pricing_policy_id), None)
                if op is None:
                    op = CurrencyHistory(
                        currency_id=currency_id,
                        pricing_policy_id=pricing_policy_id,
                        date=self.date_to,
                    )
                currency_price_missed_objects.append(op)
            return currency_price_missed_objects
        return []


class TestCertificateSerializer(serializers.Serializer):
    master_user = MasterUserField()
    member = HiddenMemberField()

    task = serializers.IntegerField(required=False, allow_null=True)
    task_object = CeleryTaskSerializer(read_only=True)

    provider_id = serializers.ReadOnlyField()

    def validate(self, attrs):
        attrs = super().validate(attrs)

        return attrs

    def create(self, validated_data):
        from poms.integrations.tasks import test_certificate

        instance = ImportTestCertificate(**validated_data)

        if instance.task:
            task, is_ready = test_certificate(
                master_user=instance.master_user,
                member=instance.member,
                task=instance.task_object,
            )
        else:
            task, is_ready = test_certificate(master_user=instance.master_user, member=instance.member)

        instance.task_object = task
        return instance


class ComplexTransactionImportSchemeInputSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=False, required=False, allow_null=True)

    name_expr = ExpressionField(max_length=EXPRESSION_FIELD_LENGTH)

    class Meta:
        model = ComplexTransactionImportSchemeInput
        fields = ["id", "name", "column", "name_expr", "column_name"]


class ComplexTransactionImportSchemeCalculatedInputSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=False, required=False, allow_null=True)

    name_expr = ExpressionField(max_length=EXPRESSION_FIELD_LENGTH)

    class Meta:
        model = ComplexTransactionImportSchemeCalculatedInput
        fields = ["id", "name", "column", "name_expr"]


class ComplexTransactionImportSchemeSelectorValueSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=False, required=False, allow_null=True)

    class Meta:
        model = ComplexTransactionImportSchemeSelectorValue
        fields = ["id", "value", "notes", "order"]


class ComplexTransactionImportSchemeReconFieldSerializer(serializers.ModelSerializer):
    value_string = ExpressionField(max_length=EXPRESSION_FIELD_LENGTH, allow_blank=True)
    value_float = ExpressionField(max_length=EXPRESSION_FIELD_LENGTH, allow_blank=True)
    value_date = ExpressionField(max_length=EXPRESSION_FIELD_LENGTH, allow_blank=True)

    class Meta:
        model = ComplexTransactionImportSchemeReconField
        fields = [
            "id",
            "reference_name",
            "description",
            "value_string",
            "value_float",
            "value_date",
        ]


class ComplexTransactionImportSchemeReconScenarioSerializer(serializers.ModelSerializer):
    line_reference_id = ExpressionField(max_length=EXPRESSION_FIELD_LENGTH)
    reference_date = ExpressionField(max_length=EXPRESSION_FIELD_LENGTH)

    fields = ComplexTransactionImportSchemeReconFieldSerializer(many=True, read_only=False)

    class Meta:
        model = ComplexTransactionImportSchemeReconScenario
        fields = [
            "id",
            "name",
            "line_reference_id",
            "reference_date",
            "fields",
            "selector_values",
        ]

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        ret["selector_values"] = []

        for item in list(instance.selector_values.all()):
            ret["selector_values"].append(item.value)

        return ret

    def to_internal_value(self, data):
        selector_values = data.pop("selector_values", [])

        ret = super().to_internal_value(data)

        # Special thing to ignore selector values type check
        ret["selector_values"] = selector_values

        return ret


class ComplexTransactionImportSchemeFieldSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=False, required=False, allow_null=True)

    # transaction_type_input = TransactionTypeInputField()

    class Meta:
        model = ComplexTransactionImportSchemeField
        fields = [
            "id",
            "transaction_type_input",
            "value_expr",
        ]

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        if instance.transaction_type_input:
            try:
                from poms.transactions.models import TransactionTypeInput
                from poms.transactions.serializers import (
                    TransactionTypeInputViewSerializer,
                )

                instance = TransactionTypeInput.objects.get(
                    transaction_type__user_code=instance.rule_scenario.transaction_type,
                    name=instance.transaction_type_input,
                )

                s = TransactionTypeInputViewSerializer(instance=instance, read_only=True, context=self.context)
                ret["transaction_type_input_object"] = s.data
            except Exception as e:
                _l.error(
                    f"Error in to_representation instance.rule_scenario.transaction_type: "
                    f"{instance.rule_scenario.transaction_type}"
                )
                _l.error(
                    f"Error in to_representation instance.transaction_type_input: {instance.transaction_type_input}"
                )
                _l.error(f"Error in to_representation: {e} trace {traceback.format_exc()}")

                ret["transaction_type_input_object"] = None

        return ret


class ComplexTransactionImportSchemeRuleScenarioSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=False, required=False, allow_null=True)
    fields = ComplexTransactionImportSchemeFieldSerializer(many=True, read_only=False)

    # selector_values = serializers.SerializerMethodField()

    class Meta:
        model = ComplexTransactionImportSchemeRuleScenario
        fields = [
            "id",
            "is_default_rule_scenario",
            "is_error_rule_scenario",
            "name",
            "selector_values",
            "transaction_type",
            "fields",
            "status",
        ]

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        selector_values = []

        selector_values.extend(item.value for item in list(instance.selector_values.all()))
        ret["selector_values"] = selector_values

        inputs = []

        try:
            from poms.transactions.models import TransactionType

            transaction_type = TransactionType.objects.get(user_code=instance.transaction_type)

            for input in transaction_type.inputs.all():
                result = {
                    "id": input.id,
                    "name": input.name,
                    "verbose_name": input.verbose_name,
                    "value_type": input.value_type,
                }

                inputs.append(result)

            ret["transaction_type_object"] = {
                "id": transaction_type.id,
                "name": transaction_type.name,
                "user_code": transaction_type.user_code,
                "inputs": inputs,
            }

        except Exception as e:
            _l.error(
                f"ComplexTransactionImportSchemeRuleScenarioSerializer.instance.transaction_type "
                f"{instance.transaction_type} error {e} trace {traceback.format_exc()}"
            )
            ret["transaction_type_object"] = None

        return ret

    def to_internal_value(self, data):
        selector_values = data.pop("selector_values", [])

        ret = super().to_internal_value(data)

        # Special thing to ignore selector values type check
        ret["selector_values"] = selector_values

        return ret


class ComplexTransactionImportSchemeSerializer(
    ModelWithTimeStampSerializer, ModelWithUserCodeSerializer, ModelMetaSerializer
):
    master_user = MasterUserField()
    rule_expr = ExpressionField(max_length=EXPRESSION_FIELD_LENGTH)
    data_preprocess_expression = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        default="",
        allow_blank=True,
        allow_null=True,
    )

    inputs = ComplexTransactionImportSchemeInputSerializer(many=True, read_only=False)
    calculated_inputs = ComplexTransactionImportSchemeCalculatedInputSerializer(
        many=True, read_only=False, required=False
    )
    selector_values = ComplexTransactionImportSchemeSelectorValueSerializer(many=True, read_only=False)
    rule_scenarios = ComplexTransactionImportSchemeRuleScenarioSerializer(many=True, read_only=False)
    recon_scenarios = ComplexTransactionImportSchemeReconScenarioSerializer(many=True, read_only=False)
    recon_layout = serializers.JSONField(required=False, allow_null=True)
    delimiter = serializers.CharField(max_length=3, required=False, initial=",", default=",")
    column_matcher = serializers.CharField(max_length=255, required=False, initial="index", default="index")

    class Meta:
        model = ComplexTransactionImportScheme
        fields = [
            "id",
            "master_user",
            "user_code",
            "configuration_code",
            "name",
            "short_name",
            "public_name",
            "notes",
            "rule_expr",
            "spreadsheet_start_cell",
            "spreadsheet_active_tab_name",
            "book_uniqueness_settings",
            "expression_iterations_count",
            "inputs",
            "calculated_inputs",
            "rule_scenarios",
            "selector_values",
            "recon_scenarios",
            "recon_layout",
            "delimiter",
            "error_handler",
            "missing_data_handler",
            "column_matcher",
            "filter_expression",
            "has_header_row",
            "data_preprocess_expression",
        ]

    def create(self, validated_data):
        inputs = validated_data.pop("inputs", empty) or []
        calculated_inputs = validated_data.pop("calculated_inputs", empty) or []
        rule_scenarios = validated_data.pop("rule_scenarios", empty) or []
        selector_values = validated_data.pop("selector_values", empty) or []
        recon_scenarios = validated_data.pop("recon_scenarios", empty) or []
        instance = super().create(validated_data)
        if selector_values is not empty:
            self.save_selector_values(instance, selector_values)
        if inputs is not empty:
            self.save_inputs(instance, inputs)
        if calculated_inputs is not empty:
            self.save_calculated_inputs(instance, calculated_inputs)
        if rule_scenarios is not empty:
            self.save_rule_scenarios(instance, rule_scenarios)
        if recon_scenarios is not empty:
            self.save_recon_scenarios(instance, recon_scenarios)
        return instance

    def update(self, instance, validated_data):
        inputs = validated_data.pop("inputs", empty)
        calculated_inputs = validated_data.pop("calculated_inputs", None) or []
        rule_scenarios = validated_data.pop("rule_scenarios", empty)
        selector_values = validated_data.pop("selector_values", empty)
        recon_scenarios = validated_data.pop("recon_scenarios", empty)
        instance = super().update(instance, validated_data)

        if selector_values is not empty:
            self.save_selector_values(instance, selector_values)

        if inputs is not empty:
            self.save_inputs(instance, inputs)
        if calculated_inputs is not empty:
            self.save_calculated_inputs(instance, calculated_inputs)
        if rule_scenarios is not empty:
            self.save_rule_scenarios(instance, rule_scenarios)
        if recon_scenarios is not empty:
            self.save_recon_scenarios(instance, recon_scenarios)

        return instance

    def save_selector_values(self, instance, selector_values):
        pk_set = []

        for selector_value in selector_values:
            selector_id = selector_value.pop("id", None)
            selector0 = None

            if selector_id:
                with contextlib.suppress(ObjectDoesNotExist):
                    selector0 = instance.selector_values.get(pk=selector_id)
            if selector0 is None:
                selector0 = ComplexTransactionImportSchemeSelectorValue(scheme=instance)
            for name, value in selector_value.items():
                setattr(selector0, name, value)
            selector0.save()
            pk_set.append(selector0.id)

        instance.selector_values.exclude(pk__in=pk_set).delete()

    def save_inputs(self, instance, inputs):
        # _l.info("inputs %s" % inputs[0])
        # _l.info("======================")
        # _l.info("inputs %s" % inputs)

        pk_set = []
        for input_values in inputs:
            input_id = input_values.pop("id", None)
            input0 = None
            if input_id:
                with contextlib.suppress(ObjectDoesNotExist):
                    input0 = ComplexTransactionImportSchemeInput.objects.get(pk=input_id)

            if input0 is None:
                input0 = ComplexTransactionImportSchemeInput(scheme=instance)
            for name, value in input_values.items():
                setattr(input0, name, value)
            input0.save()
            pk_set.append(input0.id)

        instance.inputs.exclude(pk__in=pk_set).delete()

    def save_calculated_inputs(self, instance, inputs):
        pk_set = []

        for input_values in inputs:
            input_id = input_values.pop("id", None)
            input0 = None
            if input_id:
                with contextlib.suppress(ObjectDoesNotExist):
                    input0 = ComplexTransactionImportSchemeCalculatedInput.objects.get(pk=input_id)

            if input0 is None:
                input0 = ComplexTransactionImportSchemeCalculatedInput(scheme=instance)
            for name, value in input_values.items():
                setattr(input0, name, value)
            input0.save()
            pk_set.append(input0.id)
        instance.calculated_inputs.exclude(pk__in=pk_set).delete()

    def save_rule_scenarios(self, instance, rules):
        pk_set = []

        default_transaction_type = EcosystemDefault.cache.get_cache(  # noqa: F841
            master_user_pk=instance.master_user.pk
        ).transaction_type

        for rule_values in rules:
            # TODO: remove in release 1.9.0 after testing
            # that there are no complexTransactionImportScheme
            # without field `is_error_rule_scenario`
            if "is_error_rule_scenario" not in rule_values:
                rule_values["is_error_rule_scenario"] = False

            rule_id = rule_values.pop("id", None)
            rule = None
            if rule_id:
                try:  # noqa: SIM105
                    rule = instance.rule_scenarios.get(pk=rule_id)
                except ObjectDoesNotExist:
                    pass
            else:
                rule = ComplexTransactionImportSchemeRuleScenario(scheme=instance)

            fields = rule_values.pop("fields", []) or []

            _l.info(f"rule_values before {rule_values}")

            selector_values = rule_values.pop("selector_values", []) or []
            for name, value in rule_values.items():
                setattr(rule, name, value)
            rule.save()

            if selector_values:
                selector_values_instances = []

                for val in selector_values:
                    try:
                        selector = ComplexTransactionImportSchemeSelectorValue.objects.get(scheme=instance, value=val)
                        selector_values_instances.append(selector.id)
                    except ComplexTransactionImportSchemeSelectorValue.DoesNotExist:
                        pass

                rule.selector_values.set(selector_values_instances)
            else:
                rule.selector_values.set([])
            self.save_fields(rule, fields)
            # self.save_rule_selector_values(rule0, selector_values)
            pk_set.append(rule.id)

        instance.rule_scenarios.exclude(pk__in=pk_set).delete()

    def save_recon_scenarios(self, instance, recons):
        pk_set = []
        for recon_values in recons:
            recon_id = recon_values.pop("id", None)
            recon0 = None
            if recon_id:
                with contextlib.suppress(ObjectDoesNotExist):
                    recon0 = instance.recon_scenarios.get(pk=recon_id)

            if recon0 is None:
                recon0 = ComplexTransactionImportSchemeReconScenario(scheme=instance)

            fields = recon_values.pop("fields", empty) or []
            selector_values = recon_values.pop("selector_values", []) or []
            for name, value in recon_values.items():
                setattr(recon0, name, value)

            recon0.save()

            if selector_values:
                selector_values_instances = []

                for val in selector_values:
                    try:
                        selector = ComplexTransactionImportSchemeSelectorValue.objects.get(scheme=instance, value=val)
                        selector_values_instances.append(selector.id)
                    except ComplexTransactionImportSchemeSelectorValue.DoesNotExist:
                        pass

                recon0.selector_values.set(selector_values_instances)

            self.save_recon_fields(recon0, fields)
            pk_set.append(recon0.id)
        instance.recon_scenarios.exclude(pk__in=pk_set).delete()

    def save_recon_fields(self, recon, fields):
        pk_set = set()
        for field_values in fields:
            field_id = field_values.pop("id", None)
            field0 = None
            if field_id:
                try:  # noqa: SIM105
                    field0 = recon.fields.get(pk=field_id)
                except ObjectDoesNotExist:
                    pass
            if field0 is None:
                field0 = ComplexTransactionImportSchemeReconField(recon_scenario=recon)
            for name, value in field_values.items():
                setattr(field0, name, value)

            field0.save()
            pk_set.add(field0.id)

        recon.fields.exclude(pk__in=pk_set).delete()

    def save_fields(self, rule_scenario, fields):
        pk_set = set()

        # print('save_fie fields %s' % fields)

        from poms.transactions.models import TransactionTypeInput

        if fields:
            for field_values in fields:
                try:
                    """This is required to save only existing inputs"""
                    input = TransactionTypeInput.objects.get(
                        name=field_values["transaction_type_input"],
                        transaction_type__user_code=rule_scenario.transaction_type,
                    )

                    _l.debug(f"Input exists {input} ")

                    field_id = field_values.pop("id", None)
                    field0 = None
                    if field_id:
                        with contextlib.suppress(ObjectDoesNotExist):
                            field0 = rule_scenario.fields.get(pk=field_id)

                    if field0 is None:
                        field0 = ComplexTransactionImportSchemeField(rule_scenario=rule_scenario)

                    if field_values.get("transaction_type_input", None):
                        field0.transaction_type_input = field_values["transaction_type_input"]

                    if field_values.get("value_expr", None):
                        field0.value_expr = field_values["value_expr"]

                    field0.save()
                    pk_set.add(field0.id)

                except Exception as e:
                    _l.error(f"Input does not exists {e} ")

        rule_scenario.fields.exclude(pk__in=pk_set).delete()


class ComplexTransactionImportSchemeLightSerializer(serializers.ModelSerializer):
    master_user = MasterUserField()
    rule_expr = ExpressionField(max_length=EXPRESSION_FIELD_LENGTH)

    class Meta:
        model = ComplexTransactionImportScheme
        fields = [
            "id",
            "master_user",
            "user_code",
            "name",
            "rule_expr",
            "configuration_code",
        ]


class ComplexTransactionCsvFileImport:
    def __init__(
        self,
        task_id=None,
        task_status=None,
        master_user=None,
        member=None,
        scheme=None,
        file_path=None,
        skip_first_line=None,
        delimiter=None,
        quotechar=None,
        encoding=None,
        error_handling=None,
        missing_data_handler=None,
        error=None,
        error_message=None,
        error_row_index=None,
        error_rows=None,
        total_rows=None,
        processed_rows=None,
        file_name=None,
        stats_file_report=None,
    ):
        self.task_id = task_id
        self.task_status = task_status

        self.file_name = file_name

        self.master_user = master_user
        self.member = member

        self.scheme = scheme
        self.file_path = file_path
        self.skip_first_line = bool(skip_first_line)
        self.delimiter = delimiter or ","
        self.quotechar = quotechar or '"'
        self.encoding = encoding or "utf-8"

        self.error_handling = error_handling or "continue"
        self.missing_data_handler = missing_data_handler or "throw_error"
        self.error = error
        self.error_message = error_message
        self.error_row_index = error_row_index
        self.error_rows = error_rows
        self.total_rows = total_rows
        self.processed_rows = processed_rows
        self.stats_file_report = stats_file_report

    def __str__(self):
        return f"{getattr(self.master_user, 'id', None)}-{getattr(self.member, 'id', None)}:{self.file_path}"

    @property
    def break_on_error(self):
        return self.error_handling == "break"

    @property
    def continue_on_error(self):
        return self.error_handling == "continue"


class ComplexTransactionCsvFileImportSerializer(serializers.Serializer):
    master_user = MasterUserField()
    member = HiddenMemberField()
    task_id = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    scheme = ComplexTransactionImportSchemeRestField(required=False)
    file = serializers.FileField(required=False, allow_null=True)

    stats_file_report = serializers.ReadOnlyField()
    task_status = serializers.ReadOnlyField()

    def create(self, validated_data):
        if "scheme" in validated_data:
            validated_data["delimiter"] = validated_data["scheme"].delimiter
            validated_data["error_handling"] = validated_data["scheme"].error_handler
            validated_data["missing_data_handler"] = validated_data["scheme"].missing_data_handler

            _l.debug(f"scheme missing data helper: {validated_data['scheme'].missing_data_handler}")

        _l.debug(f"validated_data {validated_data}")

        filetmp = validated_data.get("file", None)

        print(f"filetmp {filetmp}")

        if validated_data.get("task_id", None):
            validated_data.pop("file", None)
        else:
            file = validated_data.pop("file", None)
            if file:
                master_user = validated_data["master_user"]

                file_path = self._get_path(master_user, file.name)

                storage.save(file_path, file)
                validated_data["file_path"] = file_path
                validated_data["file_name"] = filetmp.name
            else:
                raise serializers.ValidationError({"file": gettext_lazy("Required field.")})

        return ComplexTransactionCsvFileImport(**validated_data)

    def _get_path(self, master_user, file_name):
        return f"{master_user.space_code}/public/{file_name}"


class TransactionFileResultSerializer(ModelWithTimeStampSerializer):
    master_user = MasterUserField()

    class Meta:
        model = TransactionFileResult
        fields = [
            "id",
            "master_user",
            "provider",
            "scheme_user_code",
            "file_path",
            "file_name",
        ]


class DataProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataProvider
        fields = ["id", "name", "user_code", "notes"]
