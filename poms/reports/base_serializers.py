import logging

from django.core.cache import cache
from rest_framework import serializers

from poms.accounts.models import Account, AccountType
from poms.common.fields import ExpressionField
from poms.common.models import EXPRESSION_FIELD_LENGTH
from poms.common.serializers import ModelMetaSerializer, ModelWithUserCodeSerializer
from poms.counterparties.serializers import (
    CounterpartySerializer,
    ResponsibleSerializer,
)
from poms.currencies.models import Currency, CurrencyHistory
from poms.instruments.models import Country, Instrument, InstrumentType, PriceHistory
from poms.instruments.serializers import (
    AccrualCalculationScheduleSerializer,
    InstrumentClassSerializer,
)
from poms.obj_attrs.models import GenericAttribute, GenericAttributeType
from poms.obj_attrs.serializers import (
    GenericClassifierViewSerializer,
    ModelWithAttributesSerializer,
)
from poms.portfolios.models import Portfolio
from poms.strategies.models import Strategy1, Strategy2, Strategy3
from poms.transactions.models import ComplexTransaction
from poms.transactions.serializers import TransactionTypeViewSerializer
from poms.users.utils import get_space_code_from_context

_l = logging.getLogger("poms.reports")


# TODO IMPORTANT
# TODO HERE WE HAVE ONLY OBJECTS THAT ALREADY PASSED PERMISSIONS CHECK
# TODO SO, WE DEFINE HERE OWN SERIALIZERS WITHOUT ModelWithObjectPermissionSerializer


class ReportGenericAttributeTypeSerializer(ModelWithUserCodeSerializer):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("read_only", True)
        super().__init__(*args, **kwargs)

    class Meta:
        model = GenericAttributeType
        fields = [
            "id",
            "user_code",
            "name",
            "short_name",
            "public_name",
            "notes",
            "value_type",
        ]

        read_only_fields = fields


class ReportGenericAttributeSerializer(serializers.ModelSerializer):
    attribute_type_object = ReportGenericAttributeTypeSerializer(source="attribute_type", read_only=True)
    classifier_object = GenericClassifierViewSerializer(source="classifier", read_only=True)

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("read_only", True)
        super().__init__(*args, **kwargs)

    class Meta:
        model = GenericAttribute
        fields = [
            "id",
            "value_string",
            "value_float",
            "value_date",
            "classifier",
            "classifier_object",
            "attribute_type",
            "attribute_type_object",
        ]

        read_only_fields = fields


class ReportAccrualCalculationScheduleSerializer(AccrualCalculationScheduleSerializer):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("read_only", True)
        super().__init__(*args, **kwargs)


class ReportPriceHistorySerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("read_only", True)
        super().__init__(*args, **kwargs)

    class Meta:
        model = PriceHistory
        fields = [
            "id",
            "instrument",
            "pricing_policy",
            "date",
            "principal_price",
            "accrued_price",
        ]
        read_only_fields = fields


class ReportCurrencySerializer(ModelWithUserCodeSerializer, ModelWithAttributesSerializer):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("read_only", True)
        super().__init__(*args, **kwargs)
        self.fields["attributes"] = ReportGenericAttributeSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = Currency
        fields = [
            "id",
            "user_code",
            "name",
            "short_name",
            "notes",
            "reference_for_pricing",
            "default_fx_rate",
            "country",
        ]
        read_only_fields = fields


class ReportInstrumentTypeSerializer(ModelWithUserCodeSerializer):
    instrument_class_object = InstrumentClassSerializer(source="instrument_class", read_only=True)

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("read_only", True)
        super().__init__(*args, **kwargs)

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
            "notes",
            "maturity_date",
        ]
        read_only_fields = fields


class ReportCountrySerializer(ModelMetaSerializer):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("read_only", True)
        super().__init__(*args, **kwargs)

    class Meta:
        model = Country
        fields = [
            "id",
            "country_code",
            "name",
            "region",
            "region_code",
            "sub_region",
            "sub_region_code",
            "user_code",
            "short_name",
        ]
        read_only_fields = fields


class ReportInstrumentSerializer(ModelWithAttributesSerializer, ModelWithUserCodeSerializer):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("read_only", True)
        super().__init__(*args, **kwargs)
        self.fields["attributes"] = ReportGenericAttributeSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = Instrument
        fields = [
            "id",
            "instrument_type",
            "user_code",
            "name",
            "short_name",
            "public_name",
            "notes",
            "pricing_currency",
            "price_multiplier",
            "accrued_currency",
            "accrued_multiplier",
            "default_price",
            "default_accrued",
            "user_text_1",
            "user_text_2",
            "user_text_3",
            "reference_for_pricing",
            # 'payment_size_detail',
            # 'daily_pricing_model',
            "maturity_date",
            "maturity_price",
            "country",
        ]
        read_only_fields = fields

    def to_representation(self, instance):
        space_code = get_space_code_from_context(self.context)
        cache_key = f"{space_code}_serialized_report_instrument_{instance.id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return cached_data

        serialized_data = super().to_representation(instance)
        cache.set(cache_key, serialized_data, timeout=3600)  # Cache for 1 hour
        return serialized_data


class ReportCurrencyHistorySerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("read_only", True)
        super().__init__(*args, **kwargs)

    class Meta:
        model = CurrencyHistory
        fields = [
            "id",
            "currency",
            "pricing_policy",
            "date",
            "fx_rate",
        ]
        read_only_fields = fields


class ReportPortfolioSerializer(ModelWithAttributesSerializer, ModelWithUserCodeSerializer):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("read_only", True)
        super().__init__(*args, **kwargs)
        self.fields["attributes"] = ReportGenericAttributeSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = Portfolio
        fields = [
            "id",
            "user_code",
            "name",
            "short_name",
            "public_name",
            "notes",
            "first_transaction_date",
            "first_cash_flow_date",
        ]
        read_only_fields = fields

    def to_representation(self, instance):
        space_code = get_space_code_from_context(self.context)
        cache_key = f"{space_code}_serialized_report_portfolio_{instance.id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return cached_data

        serialized_data = super().to_representation(instance)
        cache.set(cache_key, serialized_data, timeout=3600)  # Cache for 1 hour
        return serialized_data


class ReportAccountTypeSerializer(ModelWithUserCodeSerializer):
    transaction_details_expr = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default='""',
    )

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("read_only", True)
        super().__init__(*args, **kwargs)

    class Meta:
        model = AccountType
        fields = [
            "id",
            "user_code",
            "name",
            "short_name",
            "public_name",
            "notes",
            "show_transaction_details",
            "transaction_details_expr",
        ]
        read_only_fields = fields


class ReportAccountSerializer(ModelWithAttributesSerializer, ModelWithUserCodeSerializer):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("read_only", True)
        super().__init__(*args, **kwargs)
        self.fields["attributes"] = ReportGenericAttributeSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = Account
        fields = [
            "id",
            "type",
            "user_code",
            "name",
            "short_name",
            "public_name",
            "notes",
        ]
        read_only_fields = fields

    def to_representation(self, instance):
        space_code = get_space_code_from_context(self.context)
        cache_key = f"{space_code}_serialized_report_account_{instance.id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return cached_data

        serialized_data = super().to_representation(instance)
        cache.set(cache_key, serialized_data, timeout=3600)  # Cache for 1 hour
        return serialized_data


class ReportStrategy1Serializer(ModelWithUserCodeSerializer):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("read_only", True)
        super().__init__(*args, **kwargs)

    class Meta:
        model = Strategy1
        fields = [
            "id",
            "subgroup",
            "user_code",
            "name",
            "short_name",
            "public_name",
            "notes",
        ]
        read_only_fields = fields


class ReportStrategy2Serializer(ModelWithUserCodeSerializer):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("read_only", True)
        super().__init__(*args, **kwargs)

    class Meta:
        model = Strategy2
        fields = [
            "id",
            "subgroup",
            "user_code",
            "name",
            "short_name",
            "public_name",
            "notes",
        ]
        read_only_fields = fields


class ReportStrategy3Serializer(ModelWithUserCodeSerializer):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("read_only", True)
        super().__init__(*args, **kwargs)

    class Meta:
        model = Strategy3
        fields = [
            "id",
            "subgroup",
            "user_code",
            "name",
            "short_name",
            "public_name",
            "notes",
        ]
        read_only_fields = fields


class ReportResponsibleSerializer(ResponsibleSerializer):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("read_only", True)
        super().__init__(*args, **kwargs)

        self.fields["attributes"] = ReportGenericAttributeSerializer(many=True, required=False, allow_null=True)
        self.fields.pop("portfolios")
        self.fields.pop("portfolios_object")
        self.fields.pop("is_default")


class ReportCounterpartySerializer(CounterpartySerializer):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("read_only", True)
        super().__init__(*args, **kwargs)

        self.fields["attributes"] = ReportGenericAttributeSerializer(many=True, required=False, allow_null=True)
        self.fields.pop("portfolios")
        self.fields.pop("portfolios_object")
        self.fields.pop("is_default")


class ReportComplexTransactionSerializer(ModelWithAttributesSerializer):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("read_only", True)
        super().__init__(*args, **kwargs)

        self.fields["attributes"] = ReportGenericAttributeSerializer(many=True, required=False, allow_null=True)

        for k in list(self.fields.keys()):
            if str(k).endswith("_object"):
                self.fields.pop(k)

        self.fields["transaction_type_object"] = TransactionTypeViewSerializer(
            source="transaction_type", read_only=True
        )

    class Meta:
        model = ComplexTransaction
        fields = [
            "id",
            "date",
            "status",
            "code",
            "text",
            "transaction_type",
            "master_user",
            "is_locked",
            "is_canceled",
            "error_code",
            "user_text_1",
            "user_text_2",
            "user_text_3",
            "user_text_4",
            "user_text_5",
            "user_text_6",
            "user_text_7",
            "user_text_8",
            "user_text_9",
            "user_text_10",
            "user_text_11",
            "user_text_12",
            "user_text_13",
            "user_text_14",
            "user_text_15",
            "user_text_16",
            "user_text_17",
            "user_text_18",
            "user_text_19",
            "user_text_20",
            "user_number_1",
            "user_number_2",
            "user_number_3",
            "user_number_4",
            "user_number_5",
            "user_number_6",
            "user_number_7",
            "user_number_8",
            "user_number_9",
            "user_number_10",
            "user_number_11",
            "user_number_12",
            "user_number_13",
            "user_number_14",
            "user_number_15",
            "user_number_16",
            "user_number_17",
            "user_number_18",
            "user_number_19",
            "user_number_20",
            "user_date_1",
            "user_date_2",
            "user_date_3",
            "user_date_4",
            "user_date_5",
        ]
