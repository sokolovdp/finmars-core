import contextlib
import datetime
import logging
import time
import traceback

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty

from poms.accounts.fields import AccountDefault, AccountField
from poms.accounts.models import Account
from poms.common.fields import ExpressionField, name_validator
from poms.common.models import EXPRESSION_FIELD_LENGTH
from poms.common.serializers import (
    ModelMetaSerializer,
    ModelWithTimeStampSerializer,
    ModelWithUserCodeSerializer,
    PomsClassSerializer,
)
from poms.counterparties.fields import (
    CounterpartyDefault,
    CounterpartyField,
    ResponsibleDefault,
    ResponsibleField,
)
from poms.counterparties.models import Counterparty, Responsible
from poms.currencies.fields import CurrencyDefault, CurrencyField, SystemCurrencyDefault
from poms.currencies.models import Currency
from poms.expressions_engine import formula
from poms.instruments.fields import (
    AccrualCalculationModelField,
    EventClassField,
    EventScheduleField,
    InstrumentDefault,
    InstrumentField,
    InstrumentTypeField,
    NotificationClassField,
    PeriodicityField,
    PricingPolicyField,
)
from poms.instruments.models import (
    AccrualCalculationModel,
    DailyPricingModel,
    EventSchedule,
    Instrument,
    InstrumentType,
    PaymentSizeDetail,
    Periodicity,
    PricingPolicy,
)
from poms.integrations.fields import PriceDownloadSchemeField
from poms.integrations.models import PriceDownloadScheme
from poms.obj_attrs.serializers import ModelWithAttributesSerializer
from poms.portfolios.fields import PortfolioDefault, PortfolioField
from poms.portfolios.models import Portfolio
from poms.reconciliation.models import TransactionTypeReconField
from poms.reconciliation.serializers import (
    ReconciliationComplexTransactionFieldSerializer,
    TransactionTypeReconFieldSerializer,
)
from poms.strategies.fields import (
    Strategy1Default,
    Strategy1Field,
    Strategy2Default,
    Strategy2Field,
    Strategy3Default,
    Strategy3Field,
)
from poms.strategies.models import Strategy1, Strategy2, Strategy3
from poms.transactions.fields import (
    ReadOnlyContentTypeField,
    TransactionTypeGroupField,
    TransactionTypeInputContentTypeField,
    TransactionTypeInputField,
)
from poms.transactions.handlers import TransactionTypeProcess
from poms.transactions.models import (
    ComplexTransaction,
    ComplexTransactionInput,
    ComplexTransactionStatus,
    EventClass,
    NotificationClass,
    Transaction,
    TransactionClass,
    TransactionType,
    TransactionTypeAction,
    TransactionTypeActionExecuteCommand,
    TransactionTypeActionInstrument,
    TransactionTypeActionInstrumentAccrualCalculationSchedules,
    TransactionTypeActionInstrumentEventSchedule,
    TransactionTypeActionInstrumentEventScheduleAction,
    TransactionTypeActionInstrumentFactorSchedule,
    TransactionTypeActionInstrumentManualPricingFormula,
    TransactionTypeActionTransaction,
    TransactionTypeContextParameter,
    TransactionTypeGroup,
    TransactionTypeInput,
    TransactionTypeInputSettings,
)
from poms.users.fields import HiddenMemberField, MasterUserField
from poms.users.utils import get_member_from_context

_l = logging.getLogger("poms.transactions")


class EventClassSerializer(PomsClassSerializer):
    class Meta(PomsClassSerializer.Meta):
        model = EventClass


class NotificationClassSerializer(PomsClassSerializer):
    class Meta(PomsClassSerializer.Meta):
        model = NotificationClass


class TransactionClassSerializer(PomsClassSerializer):
    class Meta(PomsClassSerializer.Meta):
        model = TransactionClass


class ComplexTransactionStatusSerializer(PomsClassSerializer):
    class Meta(PomsClassSerializer.Meta):
        model = ComplexTransactionStatus


class TransactionTypeGroupSerializer(ModelWithUserCodeSerializer, ModelMetaSerializer):
    master_user = MasterUserField()

    class Meta:
        model = TransactionTypeGroup
        fields = [
            "id",
            "master_user",
            "user_code",
            "configuration_code",
            "name",
            "short_name",
            "public_name",
            "notes",
            "is_deleted",
            "is_enabled",
        ]


class TransactionTypeGroupViewSerializer(ModelWithUserCodeSerializer):
    class Meta:
        model = TransactionTypeGroup
        fields = [
            "id",
            "user_code",
            "name",
            "short_name",
            "public_name",
            "notes",
            "is_deleted",
        ]


class TransactionInputField(serializers.CharField):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_representation(self, value):
        return value.name if value else None


class TransactionTypeActionInstrumentPhantomField(serializers.IntegerField):
    def to_representation(self, value):
        return value.order if value else None


class TransactionTypeActionInstrumentEventSchedulePhantomField(serializers.IntegerField):
    def to_representation(self, value):
        return value.order if value else None


class TransactionTypeContextParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionTypeContextParameter
        fields = [
            "user_code",
            "name",
            "value_type",
            "order",
        ]


class TransactionTypeInputSettingsSerializer(serializers.ModelSerializer):
    linked_inputs_names = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    recalc_on_change_linked_inputs = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    def __init__(self, **kwargs):
        kwargs["required"] = False
        kwargs["default"] = False
        super().__init__(**kwargs)

    class Meta:
        model = TransactionTypeInputSettings
        fields = [
            "linked_inputs_names",
            "recalc_on_change_linked_inputs",
        ]


class TransactionTypeInputSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(
        read_only=False,
        required=False,
        allow_null=True,
    )
    name = serializers.CharField(
        max_length=255,
        allow_null=False,
        allow_blank=False,
        validators=[name_validator],
    )
    content_type = TransactionTypeInputContentTypeField(
        required=False,
        allow_null=True,
        allow_empty=True,
    )
    can_recalculate = serializers.BooleanField(read_only=True)
    value_expr = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_null=True,
        allow_blank=True,
        default="",
    )
    value = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_null=True,
        allow_blank=True,
        default="",
    )
    settings = TransactionTypeInputSettingsSerializer(
        allow_null=True,
        required=False,
    )
    button_data = serializers.JSONField(
        allow_null=True,
        required=False,
    )

    class Meta:
        model = TransactionTypeInput
        fields = [
            "id",
            "name",
            "verbose_name",
            "value_type",
            "reference_table",
            "content_type",
            "order",
            "can_recalculate",
            "value_expr",
            "tooltip",
            "value",
            "settings",
            "button_data",
            "expression_iterations_count",
        ]
        read_only_fields = ["order"]

    def __init__(self, *args, **kwargs):
        from poms.accounts.serializers import AccountViewSerializer
        from poms.counterparties.serializers import (
            CounterpartyViewSerializer,
            ResponsibleViewSerializer,
        )
        from poms.currencies.serializers import CurrencyViewSerializer
        from poms.instruments.serializers import (
            AccrualCalculationModelSerializer,
            DailyPricingModelSerializer,
            InstrumentTypeViewSerializer,
            InstrumentViewSerializer,
            PaymentSizeDetailSerializer,
            PeriodicitySerializer,
            PricingPolicySerializer,
        )
        from poms.portfolios.serializers import PortfolioViewSerializer
        from poms.strategies.serializers import (
            Strategy1ViewSerializer,
            Strategy2ViewSerializer,
            Strategy3ViewSerializer,
        )

        super().__init__(*args, **kwargs)

        self.fields["account_object"] = AccountViewSerializer(source="account", read_only=True)
        self.fields["instrument_object"] = InstrumentViewSerializer(source="instrument", read_only=True)
        self.fields["instrument_type_object"] = InstrumentTypeViewSerializer(source="instrument_type", read_only=True)
        self.fields["daily_pricing_model_object"] = DailyPricingModelSerializer(
            source="daily_pricing_model", read_only=True
        )
        self.fields["payment_size_detail_object"] = PaymentSizeDetailSerializer(
            source="payment_size_detail", read_only=True
        )
        self.fields["currency_object"] = CurrencyViewSerializer(source="currency", read_only=True)
        self.fields["counterparty_object"] = CounterpartyViewSerializer(source="counterparty", read_only=True)
        self.fields["responsible_object"] = ResponsibleViewSerializer(source="responsible", read_only=True)
        self.fields["portfolio_object"] = PortfolioViewSerializer(source="portfolio", read_only=True)
        self.fields["strategy1_object"] = Strategy1ViewSerializer(source="strategy1", read_only=True)
        self.fields["strategy2_object"] = Strategy2ViewSerializer(source="strategy2", read_only=True)
        self.fields["strategy3_object"] = Strategy3ViewSerializer(source="strategy3", read_only=True)
        self.fields["pricing_policy_object"] = PricingPolicySerializer(source="pricing_policy", read_only=True)
        self.fields["periodicity_object"] = PeriodicitySerializer(source="periodicity", read_only=True)
        self.fields["accrual_calculation_model_object"] = AccrualCalculationModelSerializer(
            source="accrual_calculation_model", read_only=True
        )

    def validate(self, data):
        return data

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)

        return instance


class TransactionTypeInputViewOnlySerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=False, required=False, allow_null=True)
    name = serializers.CharField(max_length=255, allow_null=False, allow_blank=False, validators=[name_validator])
    content_type = TransactionTypeInputContentTypeField(
        required=False,
        allow_null=True,
        allow_empty=True,
    )

    class Meta:
        model = TransactionTypeInput
        fields = [
            "id",
            "name",
            "verbose_name",
            "value_type",
            "content_type",
            "order",
            "tooltip",
            "reference_table",
        ]
        read_only_fields = ["order"]


class TransactionTypeInputViewSerializer(serializers.ModelSerializer):
    content_type = ReadOnlyContentTypeField()

    class Meta:
        model = TransactionTypeInput
        fields = [
            "id",
            "name",
            "verbose_name",
            "value_type",
            "content_type",
            "order",
        ]
        read_only_fields = fields


class TransactionTypeActionInstrumentSerializer(serializers.ModelSerializer):
    user_code = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        default="",
    )
    name = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        default="",
    )
    public_name = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        default="",
    )
    short_name = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        default="",
    )
    notes = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        default="",
    )
    instrument_type_input = TransactionInputField(
        required=False,
        allow_null=True,
    )
    pricing_currency_input = TransactionInputField(
        required=False,
        allow_null=True,
    )
    price_multiplier = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        default="1.0",
    )
    accrued_currency_input = TransactionInputField(
        required=False,
        allow_null=True,
    )
    accrued_multiplier = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        default="1.0",
    )
    default_price = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        default="0.0",
    )
    default_accrued = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        default="0.0",
    )
    user_text_1 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        default="",
    )
    user_text_2 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        default="",
    )
    user_text_3 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        default="",
    )
    reference_for_pricing = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        default="",
    )
    payment_size_detail_input = TransactionInputField(
        required=False,
        allow_null=True,
    )
    maturity_date = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
    )
    maturity_price = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        default="0.0",
    )

    class Meta:
        model = TransactionTypeActionInstrument
        fields = [
            "user_code",
            "name",
            "public_name",
            "short_name",
            "notes",
            "instrument_type",
            "instrument_type_input",
            "pricing_currency",
            "pricing_currency_input",
            "price_multiplier",
            "accrued_currency",
            "accrued_currency_input",
            "accrued_multiplier",
            "payment_size_detail",
            "payment_size_detail_input",
            "pricing_condition",
            "pricing_condition_input",
            "default_price",
            "default_accrued",
            "user_text_1",
            "user_text_2",
            "user_text_3",
            "reference_for_pricing",
            "maturity_date",
            "maturity_price",
            "action_notes",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def lookup_for_relation_object(self, master_user, data, key, Model, Serializer):
        result = None
        field_instance = None

        try:
            if key in data and data[key]:
                try:
                    if Model._meta.get_field("master_user"):
                        field_instance = Model.objects.get(master_user=master_user, user_code=data[key])
                except Exception:
                    field_instance = Model.objects.get(user_code=data[key])

                result = Serializer(instance=field_instance, context=self.context).data
        except Exception:
            result = None

        return result

    def to_representation(self, instance):
        from poms.currencies.models import Currency
        from poms.currencies.serializers import CurrencyViewSerializer
        from poms.instruments.models import (
            InstrumentType,
            PaymentSizeDetail,
            PricingCondition,
        )
        from poms.instruments.serializers import (
            InstrumentTypeViewSerializer,
            PaymentSizeDetailSerializer,
            PricingConditionSerializer,
        )

        representation = super().to_representation(instance)

        master_user = instance.transaction_type.master_user

        representation["instrument_type_object"] = self.lookup_for_relation_object(
            master_user,
            representation,
            "instrument_type",
            InstrumentType,
            InstrumentTypeViewSerializer,
        )
        representation["pricing_currency_object"] = self.lookup_for_relation_object(
            master_user,
            representation,
            "pricing_currency",
            Currency,
            CurrencyViewSerializer,
        )
        representation["accrued_currency_object"] = self.lookup_for_relation_object(
            master_user,
            representation,
            "accrued_currency",
            Currency,
            CurrencyViewSerializer,
        )
        representation["payment_size_detail_object"] = self.lookup_for_relation_object(
            master_user,
            representation,
            "payment_size_detail",
            PaymentSizeDetail,
            PaymentSizeDetailSerializer,
        )
        representation["pricing_condition_object"] = self.lookup_for_relation_object(
            master_user,
            representation,
            "pricing_condition",
            PricingCondition,
            PricingConditionSerializer,
        )

        return representation


class TransactionTypeActionTransactionSerializer(serializers.ModelSerializer):
    instrument_input = TransactionInputField(
        required=False,
        allow_null=True,
    )
    instrument_phantom = TransactionTypeActionInstrumentPhantomField(
        required=False,
        allow_null=True,
    )
    transaction_currency_input = TransactionInputField(
        required=False,
        allow_null=True,
    )
    position_size_with_sign = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        default="0.0",
    )
    settlement_currency_input = TransactionInputField(
        required=False,
        allow_null=True,
    )
    cash_consideration = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        default="0.0",
    )
    principal_with_sign = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        default="0.0",
    )
    carry_with_sign = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        default="0.0",
    )
    overheads_with_sign = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        default="0.0",
    )
    portfolio_input = TransactionInputField(
        required=False,
        allow_null=True,
    )
    account_position_input = TransactionInputField(
        required=False,
        allow_null=True,
    )
    account_cash_input = TransactionInputField(
        required=False,
        allow_null=True,
    )
    account_interim_input = TransactionInputField(
        required=False,
        allow_null=True,
    )
    accounting_date = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        default="now()",
    )
    cash_date = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        default="now()",
    )
    strategy1_position_input = TransactionInputField(
        required=False,
        allow_null=True,
    )
    strategy1_cash_input = TransactionInputField(
        required=False,
        allow_null=True,
    )
    strategy2_position_input = TransactionInputField(
        required=False,
        allow_null=True,
    )
    strategy2_cash_input = TransactionInputField(
        required=False,
        allow_null=True,
    )
    strategy3_position_input = TransactionInputField(
        required=False,
        allow_null=True,
    )
    strategy3_cash_input = TransactionInputField(
        required=False,
        allow_null=True,
    )
    responsible_input = TransactionInputField(
        required=False,
        allow_null=True,
    )
    counterparty_input = TransactionInputField(
        required=False,
        allow_null=True,
    )
    linked_instrument_input = TransactionInputField(
        required=False,
        allow_null=True,
    )
    linked_instrument_phantom = TransactionTypeActionInstrumentPhantomField(
        required=False,
        allow_null=True,
    )
    allocation_balance_input = TransactionInputField(
        required=False,
        allow_null=True,
    )
    allocation_balance_phantom = TransactionTypeActionInstrumentPhantomField(
        required=False,
        allow_null=True,
    )
    allocation_pl_input = TransactionInputField(
        required=False,
        allow_null=True,
    )
    allocation_pl_phantom = TransactionTypeActionInstrumentPhantomField(
        required=False,
        allow_null=True,
    )
    reference_fx_rate = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        default="0.0",
    )
    factor = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        default="0.0",
    )
    trade_price = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        default="0.0",
    )
    position_amount = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        default="0.0",
    )
    principal_amount = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        default="0.0",
    )
    carry_amount = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        default="0.0",
    )
    overheads = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        default="0.0",
    )
    notes = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        default="",
    )
    user_text_1 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        default="",
    )
    user_text_2 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        default="",
    )
    user_text_3 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        default="",
    )
    user_number_1 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        default="",
    )
    user_number_2 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        default="",
    )
    user_number_3 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        default="",
    )
    user_date_1 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        default="",
    )
    user_date_2 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        default="",
    )
    user_date_3 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        default="",
    )

    class Meta:
        model = TransactionTypeActionTransaction
        fields = [
            "transaction_class",
            "instrument",
            "instrument_input",
            "instrument_phantom",
            "transaction_currency",
            "transaction_currency_input",
            "position_size_with_sign",
            "settlement_currency",
            "settlement_currency_input",
            "cash_consideration",
            "principal_with_sign",
            "carry_with_sign",
            "overheads_with_sign",
            "reference_fx_rate",
            "portfolio",
            "portfolio_input",
            "account_position",
            "account_position_input",
            "account_cash",
            "account_cash_input",
            "account_interim",
            "account_interim_input",
            "accounting_date",
            "cash_date",
            "strategy1_position",
            "strategy1_position_input",
            "strategy1_cash",
            "strategy1_cash_input",
            "strategy2_position",
            "strategy2_position_input",
            "strategy2_cash",
            "strategy2_cash_input",
            "strategy3_position",
            "strategy3_position_input",
            "strategy3_cash",
            "strategy3_cash_input",
            "linked_instrument",
            "linked_instrument_input",
            "linked_instrument_phantom",
            "allocation_balance",
            "allocation_balance_input",
            "allocation_balance_phantom",
            "allocation_pl",
            "allocation_pl_input",
            "allocation_pl_phantom",
            "responsible",
            "responsible_input",
            "counterparty",
            "counterparty_input",
            "factor",
            "trade_price",
            "position_amount",
            "principal_amount",
            "carry_amount",
            "overheads",
            "notes",
            "user_text_1",
            "user_text_2",
            "user_text_3",
            "user_number_1",
            "user_number_2",
            "user_number_3",
            "user_date_1",
            "user_date_2",
            "user_date_3",
            "action_notes",
            "is_canceled",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["transaction_class_object"] = TransactionClassSerializer(
            source="transaction_class", read_only=True
        )

    def lookup_for_relation_object(self, master_user, data, key, Model, Serializer):
        result = None
        field_instance = None

        try:
            if key in data and data[key]:
                try:
                    if Model._meta.get_field("master_user"):
                        field_instance = Model.objects.get(master_user=master_user, user_code=data[key])
                except Exception:
                    field_instance = Model.objects.get(user_code=data[key])

                result = Serializer(instance=field_instance, context=self.context).data
        except Exception:
            result = None

        return result

    def to_representation(self, instance):
        from poms.accounts.models import Account
        from poms.accounts.serializers import AccountViewSerializer
        from poms.counterparties.models import Counterparty, Responsible
        from poms.counterparties.serializers import (
            CounterpartyViewSerializer,
            ResponsibleViewSerializer,
        )
        from poms.currencies.models import Currency
        from poms.currencies.serializers import CurrencyViewSerializer
        from poms.instruments.models import Instrument
        from poms.instruments.serializers import InstrumentViewSerializer
        from poms.portfolios.models import Portfolio
        from poms.portfolios.serializers import PortfolioViewSerializer
        from poms.strategies.models import Strategy1, Strategy2, Strategy3
        from poms.strategies.serializers import (
            Strategy1ViewSerializer,
            Strategy2ViewSerializer,
            Strategy3ViewSerializer,
        )

        representation = super().to_representation(instance)

        master_user = instance.transaction_type.master_user

        representation["instrument_object"] = self.lookup_for_relation_object(
            master_user,
            representation,
            "instrument",
            Instrument,
            InstrumentViewSerializer,
        )
        representation["transaction_currency_object"] = self.lookup_for_relation_object(
            master_user,
            representation,
            "transaction_currency",
            Currency,
            CurrencyViewSerializer,
        )
        representation["settlement_currency_object"] = self.lookup_for_relation_object(
            master_user,
            representation,
            "settlement_currency",
            Currency,
            CurrencyViewSerializer,
        )
        representation["portfolio_object"] = self.lookup_for_relation_object(
            master_user, representation, "portfolio", Portfolio, PortfolioViewSerializer
        )
        representation["account_position_object"] = self.lookup_for_relation_object(
            master_user,
            representation,
            "account_position",
            Account,
            AccountViewSerializer,
        )
        representation["account_cash_object"] = self.lookup_for_relation_object(
            master_user, representation, "account_cash", Account, AccountViewSerializer
        )
        representation["account_interim_object"] = self.lookup_for_relation_object(
            master_user,
            representation,
            "account_interim",
            Account,
            AccountViewSerializer,
        )
        representation["strategy1_position_object"] = self.lookup_for_relation_object(
            master_user,
            representation,
            "strategy1_position",
            Strategy1,
            Strategy1ViewSerializer,
        )
        representation["strategy1_cash_object"] = self.lookup_for_relation_object(
            master_user,
            representation,
            "strategy1_cash",
            Strategy1,
            Strategy1ViewSerializer,
        )
        representation["strategy2_position_object"] = self.lookup_for_relation_object(
            master_user,
            representation,
            "strategy2_position",
            Strategy2,
            Strategy2ViewSerializer,
        )
        representation["strategy2_cash_object"] = self.lookup_for_relation_object(
            master_user,
            representation,
            "strategy2_cash",
            Strategy2,
            Strategy2ViewSerializer,
        )
        representation["strategy3_position_object"] = self.lookup_for_relation_object(
            master_user,
            representation,
            "strategy3_position",
            Strategy3,
            Strategy3ViewSerializer,
        )
        representation["strategy3_cash_object"] = self.lookup_for_relation_object(
            master_user,
            representation,
            "strategy3_cash",
            Strategy3,
            Strategy3ViewSerializer,
        )
        representation["responsible_object"] = self.lookup_for_relation_object(
            master_user,
            representation,
            "responsible",
            Responsible,
            ResponsibleViewSerializer,
        )
        representation["counterparty_object"] = self.lookup_for_relation_object(
            master_user,
            representation,
            "counterparty",
            Counterparty,
            CounterpartyViewSerializer,
        )
        representation["linked_instrument_object"] = self.lookup_for_relation_object(
            master_user,
            representation,
            "linked_instrument",
            Instrument,
            InstrumentViewSerializer,
        )
        representation["allocation_balance_object"] = self.lookup_for_relation_object(
            master_user,
            representation,
            "allocation_balance",
            Instrument,
            InstrumentViewSerializer,
        )
        representation["allocation_pl_object"] = self.lookup_for_relation_object(
            master_user,
            representation,
            "allocation_pl",
            Instrument,
            InstrumentViewSerializer,
        )

        return representation


class TransactionTypeActionInstrumentFactorScheduleSerializer(serializers.ModelSerializer):
    instrument_input = TransactionInputField(
        required=False,
        allow_null=True,
    )
    instrument_phantom = TransactionTypeActionInstrumentPhantomField(
        required=False,
        allow_null=True,
    )
    effective_date = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
    )
    factor_value = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        default="0.0",
    )

    class Meta:
        model = TransactionTypeActionInstrumentFactorSchedule
        fields = [
            "instrument",
            "instrument_input",
            "instrument_phantom",
            "effective_date",
            "factor_value",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def lookup_for_relation_object(self, master_user, data, key, Model, Serializer):
        result = None
        field_instance = None

        try:
            if key in data and data[key]:
                try:
                    if Model._meta.get_field("master_user"):
                        field_instance = Model.objects.get(master_user=master_user, user_code=data[key])
                except Exception:
                    field_instance = Model.objects.get(user_code=data[key])

                result = Serializer(instance=field_instance, context=self.context).data
        except Exception:
            result = None

        return result

    def to_representation(self, instance):
        from poms.instruments.models import Instrument
        from poms.instruments.serializers import InstrumentViewSerializer

        representation = super().to_representation(instance)

        master_user = instance.transaction_type.master_user

        representation["instrument_object"] = self.lookup_for_relation_object(
            master_user,
            representation,
            "instrument",
            Instrument,
            InstrumentViewSerializer,
        )

        return representation


# DEPRECATED
class TransactionTypeActionInstrumentManualPricingFormulaSerializer(serializers.ModelSerializer):
    instrument_input = TransactionInputField(
        required=False,
        allow_null=True,
    )
    instrument_phantom = TransactionTypeActionInstrumentPhantomField(
        required=False,
        allow_null=True,
    )
    pricing_policy = PricingPolicyField(
        required=False,
        allow_null=True,
    )
    pricing_policy_input = TransactionInputField(
        required=False,
        allow_null=True,
    )
    expr = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
    )
    notes = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        default="",
        allow_null=True,
        allow_blank=True,
    )

    class Meta:
        model = TransactionTypeActionInstrumentFactorSchedule
        fields = [
            "instrument",
            "instrument_input",
            "instrument_phantom",
            "pricing_policy",
            "pricing_policy_input",
            "expr",
            "notes",
        ]

    def __init__(self, *args, **kwargs):
        from poms.instruments.serializers import PricingPolicySerializer

        super().__init__(*args, **kwargs)

        self.fields["pricing_policy_object"] = PricingPolicySerializer(source="pricing_policy", read_only=True)


class TransactionTypeActionInstrumentAccrualCalculationSchedulesSerializer(serializers.ModelSerializer):
    instrument_input = TransactionInputField(
        required=False,
        allow_null=True,
    )
    instrument_phantom = TransactionTypeActionInstrumentPhantomField(
        required=False,
        allow_null=True,
    )
    accrual_calculation_model_input = TransactionInputField(
        required=False,
        allow_null=True,
    )
    periodicity_input = TransactionInputField(
        required=False,
        allow_null=True,
    )
    accrual_start_date = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
    )
    first_payment_date = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
    )
    accrual_size = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        default="0.0",
    )
    periodicity_n = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
    )
    notes = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_null=True,
        allow_blank=True,
    )

    class Meta:
        model = TransactionTypeActionInstrumentAccrualCalculationSchedules
        fields = [
            "instrument",
            "instrument_input",
            "instrument_phantom",
            "accrual_calculation_model",
            "accrual_calculation_model_input",
            "periodicity",
            "periodicity_input",
            "accrual_start_date",
            "first_payment_date",
            "accrual_size",
            "periodicity_n",
            "notes",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def lookup_for_relation_object(self, master_user, data, key, Model, Serializer):
        result = None
        field_instance = None

        try:
            if key in data and data[key]:
                try:
                    if Model._meta.get_field("master_user"):
                        field_instance = Model.objects.get(master_user=master_user, user_code=data[key])
                except Exception:
                    field_instance = Model.objects.get(user_code=data[key])

                result = Serializer(instance=field_instance, context=self.context).data
        except Exception:
            result = None

        return result

    def to_representation(self, instance):
        from poms.instruments.models import AccrualCalculationModel, Periodicity
        from poms.instruments.serializers import (
            AccrualCalculationModelSerializer,
            InstrumentViewSerializer,
            PeriodicitySerializer,
        )

        representation = super().to_representation(instance)

        master_user = instance.transaction_type.master_user

        representation["instrument_object"] = self.lookup_for_relation_object(
            master_user,
            representation,
            "instrument",
            Instrument,
            InstrumentViewSerializer,
        )
        representation["periodicity_object"] = self.lookup_for_relation_object(
            master_user,
            representation,
            "periodicity",
            Periodicity,
            PeriodicitySerializer,
        )
        representation["accrual_calculation_model_object"] = self.lookup_for_relation_object(
            master_user,
            representation,
            "accrual_calculation_model",
            AccrualCalculationModel,
            AccrualCalculationModelSerializer,
        )

        return representation


class TransactionTypeActionInstrumentEventScheduleSerializer(serializers.ModelSerializer):
    instrument_input = TransactionInputField(
        required=False,
        allow_null=True,
    )
    instrument_phantom = TransactionTypeActionInstrumentPhantomField(
        required=False,
        allow_null=True,
    )
    periodicity_input = TransactionInputField(
        required=False,
        allow_null=True,
    )
    notification_class_input = TransactionInputField(
        required=False,
        allow_null=True,
    )
    event_class_input = TransactionInputField(
        required=False,
        allow_null=True,
    )
    effective_date = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
    )
    final_date = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
    )
    notify_in_n_days = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
    )
    is_auto_generated = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
    )
    periodicity_n = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
    )
    name = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
    )
    description = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
    )

    class Meta:
        model = TransactionTypeActionInstrumentEventSchedule
        fields = [
            "instrument",
            "instrument_input",
            "instrument_phantom",
            "periodicity",
            "periodicity_input",
            "notification_class",
            "notification_class_input",
            "event_class",
            "event_class_input",
            "effective_date",
            "final_date",
            "notify_in_n_days",
            "is_auto_generated",
            "periodicity_n",
            "name",
            "description",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def lookup_for_relation_object(self, master_user, data, key, Model, Serializer):
        result = None
        field_instance = None

        try:
            if key in data and data[key]:
                try:
                    if Model._meta.get_field("master_user"):
                        field_instance = Model.objects.get(master_user=master_user, user_code=data[key])
                except Exception:
                    field_instance = Model.objects.get(user_code=data[key])

                result = Serializer(instance=field_instance, context=self.context).data
        except Exception:
            result = None

        return result

    def to_representation(self, instance):
        from poms.instruments.models import Periodicity
        from poms.instruments.serializers import (
            InstrumentViewSerializer,
            PeriodicitySerializer,
        )

        representation = super().to_representation(instance)

        master_user = instance.transaction_type.master_user

        representation["instrument_object"] = self.lookup_for_relation_object(
            master_user,
            representation,
            "instrument",
            Instrument,
            InstrumentViewSerializer,
        )
        representation["periodicity_object"] = self.lookup_for_relation_object(
            master_user,
            representation,
            "periodicity",
            Periodicity,
            PeriodicitySerializer,
        )
        representation["notification_class_object"] = self.lookup_for_relation_object(
            master_user,
            representation,
            "notification_class",
            NotificationClass,
            NotificationClassSerializer,
        )
        representation["event_class_object"] = self.lookup_for_relation_object(
            master_user, representation, "event_class", EventClass, EventClassSerializer
        )

        return representation


class TransactionTypeActionInstrumentEventScheduleActionSerializer(serializers.ModelSerializer):
    event_schedule = EventScheduleField(
        required=False,
        allow_null=True,
    )
    event_schedule_input = TransactionInputField(
        required=False,
        allow_null=True,
    )
    event_schedule_phantom = TransactionTypeActionInstrumentEventSchedulePhantomField(
        required=False,
        allow_null=True,
    )
    transaction_type_from_instrument_type = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
    )
    is_book_automatic = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
    )
    is_sent_to_pending = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
    )
    button_position = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
    )
    text = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
    )

    class Meta:
        model = TransactionTypeActionInstrumentEventScheduleAction
        fields = [
            "event_schedule",
            "event_schedule_input",
            "event_schedule_phantom",
            "transaction_type_from_instrument_type",
            "is_book_automatic",
            "is_sent_to_pending",
            "button_position",
            "text",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class TransactionTypeActionExecuteCommandSerializer(serializers.ModelSerializer):
    expr = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
    )

    class Meta:
        model = TransactionTypeActionExecuteCommand
        fields = ["expr"]


class TransactionTypeActionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(
        required=False,
        allow_null=True,
    )
    rebook_reaction = serializers.IntegerField(
        required=False,
        allow_null=True,
    )
    condition_expr = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    transaction = TransactionTypeActionTransactionSerializer(
        source="transactiontypeactiontransaction",
        required=False,
        allow_null=True,
    )
    instrument = TransactionTypeActionInstrumentSerializer(
        source="transactiontypeactioninstrument",
        required=False,
        allow_null=True,
    )
    instrument_factor_schedule = TransactionTypeActionInstrumentFactorScheduleSerializer(
        source="transactiontypeactioninstrumentfactorschedule",
        required=False,
        allow_null=True,
    )
    instrument_manual_pricing_formula = TransactionTypeActionInstrumentManualPricingFormulaSerializer(
        source="transactiontypeactioninstrumentmanualpricingformula",
        required=False,
        allow_null=True,
    )
    instrument_accrual_calculation_schedules = TransactionTypeActionInstrumentAccrualCalculationSchedulesSerializer(
        source="transactiontypeactioninstrumentaccrualcalculationschedules",
        required=False,
        allow_null=True,
    )
    instrument_event_schedule = TransactionTypeActionInstrumentEventScheduleSerializer(
        source="transactiontypeactioninstrumenteventschedule",
        required=False,
        allow_null=True,
    )
    instrument_event_schedule_action = TransactionTypeActionInstrumentEventScheduleActionSerializer(
        source="transactiontypeactioninstrumenteventscheduleaction",
        required=False,
        allow_null=True,
    )
    execute_command = TransactionTypeActionExecuteCommandSerializer(
        source="transactiontypeactionexecutecommand",
        required=False,
        allow_null=True,
    )

    class Meta:
        model = TransactionTypeAction
        fields = [
            "id",
            "order",
            "rebook_reaction",
            "condition_expr",
            "action_notes",
            "transaction",
            "instrument",
            "instrument_factor_schedule",
            "instrument_manual_pricing_formula",
            "instrument_accrual_calculation_schedules",
            "instrument_event_schedule",
            "instrument_event_schedule_action",
            "execute_command",
        ]

    def validate(self, attrs):
        # TODO: transaction or instrument present
        return attrs


class TransactionTypeLightSerializer(ModelWithUserCodeSerializer):
    master_user = MasterUserField()
    group = TransactionTypeGroupField(
        required=False,
        allow_null=False,
    )
    date_expr = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="now()",
    )
    display_expr = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    transaction_unique_code_expr = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_1 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_2 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_3 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_4 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_5 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_6 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_7 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_8 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_9 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_10 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_11 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_12 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_13 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_14 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_15 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_16 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_17 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_18 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_19 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_20 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_21 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_22 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_23 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_24 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_25 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_26 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_27 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_28 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_29 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_30 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_1 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_2 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_3 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_4 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_5 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_6 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_7 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_8 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_9 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_10 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_11 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_12 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_13 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_14 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_15 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_16 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_17 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_18 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_19 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_20 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_date_1 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_date_2 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_date_3 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_date_4 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_date_5 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    instrument_types = InstrumentTypeField(
        required=False,
        allow_null=True,
        many=True,
    )
    portfolios = PortfolioField(
        required=False,
        allow_null=True,
        many=True,
    )

    def __init__(self, *args, **kwargs):
        from poms.instruments.serializers import InstrumentTypeViewSerializer
        from poms.portfolios.serializers import PortfolioViewSerializer

        super().__init__(*args, **kwargs)

        self.fields["instrument_types_object"] = InstrumentTypeViewSerializer(
            source="instrument_types", many=True, read_only=True
        )
        self.fields["portfolios_object"] = PortfolioViewSerializer(source="portfolios", many=True, read_only=True)

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        try:
            instance = TransactionTypeGroup.objects.get(id=representation["group"])

            s = TransactionTypeGroupViewSerializer(instance=instance, read_only=True, context=self.context)
            representation["group_object"] = s.data
        except Exception:
            # _l.info(f"Error in to_representation: {repr(e)} {traceback.format_exc()}")

            representation["group_object"] = None

        return representation

    class Meta:
        model = TransactionType
        fields = [
            "id",
            "master_user",
            "group",
            "user_code",
            "name",
            "short_name",
            "public_name",
            "notes",
            "date_expr",
            "display_expr",
            "transaction_unique_code_expr",
            "transaction_unique_code_options",
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
            "user_text_21",
            "user_text_22",
            "user_text_23",
            "user_text_24",
            "user_text_25",
            "user_text_26",
            "user_text_27",
            "user_text_28",
            "user_text_29",
            "user_text_30",
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
            "is_valid_for_all_portfolios",
            "is_valid_for_all_instruments",
            "is_deleted",
            "instrument_types",
            "portfolios",
            "configuration_code",
        ]


class TransactionTypeLightSerializerWithInputs(TransactionTypeLightSerializer):
    inputs = TransactionTypeInputSerializer(
        required=False,
        many=True,
    )
    context_parameters = TransactionTypeContextParameterSerializer(
        required=False,
        many=True,
    )

    class Meta:
        model = TransactionType
        fields = [
            "id",
            "master_user",
            "group",
            "user_code",
            "name",
            "short_name",
            "public_name",
            "notes",
            "date_expr",
            "display_expr",
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
            "user_text_21",
            "user_text_22",
            "user_text_23",
            "user_text_24",
            "user_text_25",
            "user_text_26",
            "user_text_27",
            "user_text_28",
            "user_text_29",
            "user_text_30",
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
            "is_valid_for_all_portfolios",
            "is_valid_for_all_instruments",
            "is_deleted",
            "instrument_types",
            "portfolios",
            "inputs",
            "context_parameters_notes",
            "context_parameters",
        ]


class TransactionTypeSerializer(
    ModelWithUserCodeSerializer,
    ModelWithAttributesSerializer,
    ModelWithTimeStampSerializer,
    ModelMetaSerializer,
):
    master_user = MasterUserField()
    group = TransactionTypeGroupField(
        required=False,
        allow_null=False,
    )
    date_expr = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="now()",
    )
    display_expr = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    transaction_unique_code_expr = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_1 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_2 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_3 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_4 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_5 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_6 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_7 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_8 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_9 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_10 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_11 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_12 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_13 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_14 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_15 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_16 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_17 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_18 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_19 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_20 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )

    user_text_21 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_22 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_23 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_24 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_25 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_26 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_27 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_28 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_29 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_text_30 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )

    user_number_1 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_2 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_3 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_4 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_5 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_6 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_7 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_8 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_9 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_10 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_11 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_12 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_13 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_14 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_15 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_16 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_17 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_18 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_19 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_number_20 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_date_1 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_date_2 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_date_3 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_date_4 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    user_date_5 = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    instrument_types = InstrumentTypeField(
        required=False,
        allow_null=True,
        many=True,
    )
    portfolios = PortfolioField(
        required=False,
        allow_null=True,
        many=True,
    )
    inputs = TransactionTypeInputSerializer(
        required=False,
        many=True,
    )
    recon_fields = TransactionTypeReconFieldSerializer(
        required=False,
        many=True,
    )
    context_parameters = TransactionTypeContextParameterSerializer(
        required=False,
        many=True,
    )
    actions = TransactionTypeActionSerializer(
        required=False,
        many=True,
        read_only=False,
    )
    book_transaction_layout = serializers.JSONField(
        required=False,
        allow_null=True,
    )
    visibility_status = serializers.ChoiceField(
        default=TransactionType.SHOW_PARAMETERS,
        initial=TransactionType.SHOW_PARAMETERS,
        required=False,
        choices=TransactionType.VISIBILITY_STATUS_CHOICES,
    )
    type = serializers.ChoiceField(
        default=TransactionType.TYPE_DEFAULT,
        initial=TransactionType.TYPE_DEFAULT,
        required=False,
        choices=TransactionType.TYPE_CHOICES,
    )

    def __init__(self, *args, **kwargs):
        from poms.instruments.serializers import InstrumentTypeViewSerializer
        from poms.portfolios.serializers import PortfolioViewSerializer

        super().__init__(*args, **kwargs)

        self.fields["instrument_types_object"] = InstrumentTypeViewSerializer(
            source="instrument_types", many=True, read_only=True
        )
        self.fields["portfolios_object"] = PortfolioViewSerializer(source="portfolios", many=True, read_only=True)

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        try:
            instance = TransactionTypeGroup.objects.get(
                id=representation["group"]
            )  # should be already converted to id

            s = TransactionTypeGroupViewSerializer(instance=instance, read_only=True, context=self.context)
            representation["group_object"] = s.data
        except Exception as e:
            _l.error(f"Error in to_representation error: {e} {traceback.format_exc()}")

            representation["group_object"] = None

        return representation

    class Meta:
        model = TransactionType
        fields = [
            "id",
            "master_user",
            "group",
            "user_code",
            "name",
            "short_name",
            "public_name",
            "notes",
            "date_expr",
            "display_expr",
            "visibility_status",
            "type",
            "transaction_unique_code_expr",
            "transaction_unique_code_options",
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
            "user_text_21",
            "user_text_22",
            "user_text_23",
            "user_text_24",
            "user_text_25",
            "user_text_26",
            "user_text_27",
            "user_text_28",
            "user_text_29",
            "user_text_30",
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
            "is_valid_for_all_portfolios",
            "is_valid_for_all_instruments",
            "is_deleted",
            "book_transaction_layout",
            "instrument_types",
            "portfolios",
            "inputs",
            "actions",
            "recon_fields",
            "context_parameters",
            "context_parameters_notes",
            # 'group_object',
            "is_enabled",
            "configuration_code",
        ]

    def validate(self, attrs):
        # TODO: validate *_input...
        return attrs

    def create(self, validated_data):
        inputs = validated_data.pop("inputs", empty)
        actions = validated_data.pop("actions", empty)
        recon_fields = validated_data.pop("recon_fields", empty)
        context_parameters = validated_data.pop("context_parameters", empty)
        instance = super().create(validated_data)

        if inputs is not empty:
            inputs = self.save_inputs(instance, inputs)
        if actions is not empty:
            self.save_actions(instance, actions, inputs)
        if recon_fields is not empty:
            self.save_recon_fields(instance, recon_fields)
        if context_parameters is not empty:
            self.save_context_parameters(instance, context_parameters)

        return instance

    def update(self, instance, validated_data):
        inputs = validated_data.pop("inputs", empty)
        actions = validated_data.pop("actions", empty)
        recon_fields = validated_data.pop("recon_fields", empty)
        context_parameters = validated_data.pop("context_parameters", empty)

        instance = super().update(instance, validated_data)

        if inputs is not empty:
            inputs = self.save_inputs(instance, inputs)
        if actions is not empty:
            actions = self.save_actions(instance, actions, inputs)
        if recon_fields is not empty:
            recon_fields = self.save_recon_fields(instance, recon_fields)
        if context_parameters is not empty:
            context_parameters = self.save_context_parameters(instance, context_parameters)

        if inputs is not empty:
            instance.inputs.exclude(id__in=[i.id for i in inputs]).delete()
        if actions is not empty:
            instance.actions.exclude(id__in=[a.id for a in actions]).delete()
        if recon_fields is not empty:
            instance.recon_fields.exclude(id__in=[a.id for a in recon_fields]).delete()
        if context_parameters is not empty:
            instance.context_parameters.exclude(id__in=[a.id for a in context_parameters]).delete()

        return instance

    def save_inputs(self, instance, inputs_data):
        cur_inputs = {i.id: i for i in instance.inputs.all()}
        new_inputs = []

        for order, inp_data in enumerate(inputs_data):
            pk = inp_data.pop("id", None)
            inp = cur_inputs.pop(pk, None)
            settings_data = inp_data.pop("settings", None)
            if inp is None:
                try:
                    inp = TransactionTypeInput.objects.get(transaction_type=instance, name=inp_data["name"])
                except TransactionTypeInput.DoesNotExist:
                    inp = TransactionTypeInput(transaction_type=instance)

            inp.order = order
            for attr, value in inp_data.items():
                setattr(inp, attr, value)
            inp.save()

            if settings_data:
                if inp.settings:
                    if "linked_inputs_names" in settings_data:
                        inp.settings.linked_inputs_names = settings_data["linked_inputs_names"]

                    if "recalc_on_change_linked_inputs" in settings_data:
                        inp.settings.recalc_on_change_linked_inputs = settings_data["recalc_on_change_linked_inputs"]

                    inp.settings.save()

                else:
                    item = TransactionTypeInputSettings.objects.create(transaction_type_input=inp)

                    if "linked_inputs_names" in settings_data:
                        item.linked_inputs_names = settings_data["linked_inputs_names"]

                    if "recalc_on_change_linked_inputs" in settings_data:
                        item.recalc_on_change_linked_inputs = settings_data["recalc_on_change_linked_inputs"]

                    item.save()

                    inp.settings = item

            inp.save()

            new_inputs.append(inp)
        return new_inputs

    def save_recon_fields(self, instance, recon_fields_data):
        cur_recon_fields = {i.id: i for i in instance.recon_fields.all()}
        new_recon_fields = []

        for order, rec_field_data in enumerate(recon_fields_data):  # noqa: B007
            pk = rec_field_data.pop("id", None)
            recon_field = cur_recon_fields.pop(pk, None)
            if recon_field is None:
                try:
                    recon_field = TransactionTypeReconField.objects.get(
                        transaction_type=instance,
                        reference_name=rec_field_data["reference_name"],
                    )
                except TransactionTypeReconField.DoesNotExist:
                    recon_field = TransactionTypeReconField(transaction_type=instance)

            for attr, value in rec_field_data.items():
                setattr(recon_field, attr, value)
            recon_field.save()
            new_recon_fields.append(recon_field)
        return new_recon_fields

    def save_context_parameters(self, instance, context_parameters_data):
        cur_context_parameters = {i.id: i for i in instance.context_parameters.all()}
        new_context_parameters = []

        for order, context_parameter_field_data in enumerate(context_parameters_data):  # noqa: B007
            pk = context_parameter_field_data.pop("id", None)
            context_parameter = cur_context_parameters.pop(pk, None)
            if context_parameter is None:
                try:
                    context_parameter = TransactionTypeContextParameter.objects.get(
                        transaction_type=instance,
                        order=context_parameter_field_data["order"],
                        user_code=context_parameter_field_data["user_code"],
                        name=context_parameter_field_data["name"],
                    )
                except TransactionTypeContextParameter.DoesNotExist:
                    context_parameter = TransactionTypeContextParameter(transaction_type=instance)

            for attr, value in context_parameter_field_data.items():
                setattr(context_parameter, attr, value)
            context_parameter.save()
            new_context_parameters.append(context_parameter)
        return new_context_parameters

    def save_actions_instrument(self, instance, inputs, actions, existed_actions, actions_data):
        for order, action_data in enumerate(actions_data):
            pk = action_data.pop("id", None)
            action = existed_actions.get(pk, None)

            action_instrument_data = action_data.get("instrument", action_data.get("transactiontypeactioninstrument"))
            if action_instrument_data:
                for attr, value in action_instrument_data.items():
                    if attr.endswith("_input") and value:
                        try:
                            action_instrument_data[attr] = inputs[value]
                        except KeyError as e:
                            raise ValidationError(f'Invalid input "{value}"') from e

                action_instrument = None
                if action:
                    with contextlib.suppress(ObjectDoesNotExist):
                        action_instrument = action.transactiontypeactioninstrument

                if action_instrument is None:
                    action_instrument = TransactionTypeActionInstrument(transaction_type=instance)

                for attr, value in action_instrument_data.items():
                    setattr(action_instrument, attr, value)

                action_instrument.order = order
                action_instrument.rebook_reaction = action_data.get(
                    "rebook_reaction", action_instrument.rebook_reaction
                )
                action_instrument.action_notes = action_data.get("action_notes", action_instrument.action_notes)
                action_instrument.condition_expr = action_data.get("condition_expr", action_instrument.condition_expr)
                action_instrument.save()
                actions[order] = action_instrument

    def save_actions_transaction(self, instance, inputs, actions, existed_actions, actions_data):  # noqa: PLR0912
        for order, action_data in enumerate(actions_data):
            pk = action_data.pop("id", None)
            action = existed_actions.get(pk, None)
            action_transaction_data = action_data.get(
                "transaction", action_data.get("transactiontypeactiontransaction")
            )

            if action_transaction_data:
                for attr, value in action_transaction_data.items():
                    if attr.endswith("_input") and value:
                        try:
                            action_transaction_data[attr] = inputs[value]
                        except KeyError as e:
                            raise ValidationError(f'Invalid input "{value}"') from e
                    if attr == "instrument_phantom" and value is not None:
                        try:
                            action_transaction_data[attr] = actions[value]
                        except IndexError as exc:
                            raise ValidationError(f'Invalid action order "{value}"') from exc

                    if attr == "linked_instrument_phantom" and value is not None:
                        try:
                            action_transaction_data[attr] = actions[value]
                        except IndexError as err:
                            raise ValidationError(f'Invalid action order "{value}"') from err

                    if attr == "allocation_balance_phantom" and value is not None:
                        try:
                            action_transaction_data[attr] = actions[value]
                        except IndexError as err:
                            raise ValidationError(f'Invalid action order "{value}"') from err

                    if attr == "allocation_pl_phantom" and value is not None:
                        try:
                            action_transaction_data[attr] = actions[value]
                        except IndexError as err:
                            raise ValidationError(f'Invalid action order "{value}"') from err

                action_transaction = None
                if action:
                    with contextlib.suppress(ObjectDoesNotExist):
                        action_transaction = action.transactiontypeactiontransaction

                if action_transaction is None:
                    action_transaction = TransactionTypeActionTransaction(transaction_type=instance)

                for attr, value in action_transaction_data.items():
                    setattr(action_transaction, attr, value)

                action_transaction.order = order
                action_transaction.rebook_reaction = action_data.get(
                    "rebook_reaction", action_transaction.rebook_reaction
                )
                action_transaction.action_notes = action_data.get("action_notes", action_transaction.action_notes)
                action_transaction.condition_expr = action_data.get(
                    "condition_expr", action_transaction.condition_expr
                )
                action_transaction.save()
                actions[order] = action_transaction

    def save_actions_instrument_factor_schedule(self, instance, inputs, actions, existed_actions, actions_data):
        for order, action_data in enumerate(actions_data):
            pk = action_data.pop("id", None)
            action = existed_actions.get(pk, None)

            item_data = action_data.get(
                "instrument_factor_schedule",
                action_data.get("transactiontypeactioninstrumentfactorschedule"),
            )
            if item_data:
                for attr, value in item_data.items():
                    if attr.endswith("_input") and value:
                        try:
                            item_data[attr] = inputs[value]
                        except KeyError as e:
                            raise ValidationError(f'Invalid input "{value}"') from e

                    if attr == "instrument_phantom" and value is not None:
                        try:
                            item_data[attr] = actions[value]
                        except IndexError as exc:
                            raise ValidationError(f'Invalid action order "{value}"') from exc

                item = None
                if action:
                    with contextlib.suppress(ObjectDoesNotExist):
                        item = action.transactiontypeactioninstrumentfactorschedule

                if item is None:
                    item = TransactionTypeActionInstrumentFactorSchedule(transaction_type=instance)

                for attr, value in item_data.items():
                    setattr(item, attr, value)

                item.order = order
                item.rebook_reaction = action_data.get("rebook_reaction", item.rebook_reaction)
                item.action_notes = action_data.get("action_notes", item.action_notes)
                item.condition_expr = action_data.get("condition_expr", item.condition_expr)

                item.save()
                actions[order] = item

    def save_actions_execute_command(self, instance, inputs, actions, existed_actions, actions_data):
        for order, action_data in enumerate(actions_data):
            pk = action_data.pop("id", None)
            action = existed_actions.get(pk, None)

            item_data = action_data.get(
                "execute_command",
                action_data.get("transactiontypeactionexecutecommand"),
            )
            if item_data:
                item = None
                if action:
                    with contextlib.suppress(ObjectDoesNotExist):
                        item = action.transactiontypeactionexecutecommand

                if item is None:
                    item = TransactionTypeActionExecuteCommand(transaction_type=instance)

                for attr, value in item_data.items():
                    setattr(item, attr, value)

                item.order = order
                item.rebook_reaction = action_data.get("rebook_reaction", item.rebook_reaction)
                item.action_notes = action_data.get("action_notes", item.action_notes)
                item.condition_expr = action_data.get("condition_expr", item.condition_expr)

                item.save()
                actions[order] = item

    def save_actions_instrument_manual_pricing_formula(self, instance, inputs, actions, existed_actions, actions_data):
        for order, action_data in enumerate(actions_data):
            pk = action_data.pop("id", None)
            action = existed_actions.get(pk, None)

            item_data = action_data.get(
                "instrument_manual_pricing_formula",
                action_data.get("transactiontypeactioninstrumentmanualpricingformula"),
            )
            if item_data:
                for attr, value in item_data.items():
                    if attr.endswith("_input") and value:
                        try:
                            item_data[attr] = inputs[value]
                        except KeyError as e:
                            raise ValidationError(f'Invalid input "{value}"') from e

                    if attr == "instrument_phantom" and value is not None:
                        try:
                            item_data[attr] = actions[value]
                        except IndexError as exc:
                            raise ValidationError(f'Invalid action order "{value}"') from exc

                item = None
                if action:
                    with contextlib.suppress(ObjectDoesNotExist):
                        item = action.transactiontypeactioninstrumentmanualpricingformula

                if item is None:
                    item = TransactionTypeActionInstrumentManualPricingFormula(transaction_type=instance)

                for attr, value in item_data.items():
                    setattr(item, attr, value)

                item.order = order
                item.rebook_reaction = action_data.get("rebook_reaction", item.rebook_reaction)
                item.action_notes = action_data.get("action_notes", item.action_notes)
                item.condition_expr = action_data.get("condition_expr", item.condition_expr)

                item.save()
                actions[order] = item

    def save_actions_instrument_accrual_calculation_schedule(
        self, instance, inputs, actions, existed_actions, actions_data
    ):
        for order, action_data in enumerate(actions_data):
            pk = action_data.pop("id", None)
            action = existed_actions.get(pk, None)

            item_data = action_data.get(
                "instrument_accrual_calculation_schedules",
                action_data.get("transactiontypeactioninstrumentaccrualcalculationschedules"),
            )
            if item_data:
                for attr, value in item_data.items():
                    if attr.endswith("_input") and value:
                        try:
                            item_data[attr] = inputs[value]
                        except KeyError as e:
                            raise ValidationError(f'Invalid input "{value}"') from e

                    if attr == "instrument_phantom" and value is not None:
                        try:
                            item_data[attr] = actions[value]
                        except IndexError as exc:
                            raise ValidationError(f'Invalid action order "{value}"') from exc

                item = None
                if action:
                    with contextlib.suppress(ObjectDoesNotExist):
                        item = action.transactiontypeactioninstrumentaccrualcalculationschedules

                if item is None:
                    item = TransactionTypeActionInstrumentAccrualCalculationSchedules(transaction_type=instance)

                for attr, value in item_data.items():
                    setattr(item, attr, value)

                item.order = order
                item.rebook_reaction = action_data.get("rebook_reaction", item.rebook_reaction)
                item.action_notes = action_data.get("action_notes", item.action_notes)
                item.condition_expr = action_data.get("condition_expr", item.condition_expr)

                item.save()
                actions[order] = item

    def save_actions_instrument_event_schedule(self, instance, inputs, actions, existed_actions, actions_data):
        for order, action_data in enumerate(actions_data):
            pk = action_data.pop("id", None)
            action = existed_actions.get(pk, None)

            item_data = action_data.get(
                "instrument_event_schedule",
                action_data.get("transactiontypeactioninstrumenteventschedule"),
            )
            if item_data:
                for attr, value in item_data.items():
                    if attr.endswith("_input") and value:
                        try:
                            item_data[attr] = inputs[value]
                        except KeyError as e:
                            raise ValidationError(f'Invalid input "{value}"') from e

                    if attr == "instrument_phantom" and value is not None:
                        try:
                            item_data[attr] = actions[value]
                        except IndexError as exc:
                            raise ValidationError(f'Invalid action order "{value}"') from exc

                item = None
                if action:
                    with contextlib.suppress(ObjectDoesNotExist):
                        item = action.transactiontypeactioninstrumenteventschedule

                if item is None:
                    item = TransactionTypeActionInstrumentEventSchedule(transaction_type=instance)

                for attr, value in item_data.items():
                    setattr(item, attr, value)

                item.order = order
                item.rebook_reaction = action_data.get("rebook_reaction", item.rebook_reaction)
                item.action_notes = action_data.get("action_notes", item.action_notes)
                item.condition_expr = action_data.get("condition_expr", item.condition_expr)

                item.save()
                actions[order] = item

    def save_actions_instrument_event_schedule_action(self, instance, inputs, actions, existed_actions, actions_data):
        for order, action_data in enumerate(actions_data):
            pk = action_data.pop("id", None)
            action = existed_actions.get(pk, None)

            item_data = action_data.get(
                "instrument_event_schedule_action",
                action_data.get("transactiontypeactioninstrumenteventscheduleaction"),
            )
            if item_data:
                for attr, value in item_data.items():
                    if attr.endswith("_input") and value:
                        try:
                            item_data[attr] = inputs[value]
                        except KeyError as e:
                            raise ValidationError(f'Invalid input "{value}"') from e

                    if attr == "event_schedule_phantom" and value is not None:
                        try:
                            item_data[attr] = actions[value]
                        except IndexError as e:
                            raise ValidationError(f'Invalid action order "{value}"') from e

                item = None
                if action:
                    with contextlib.suppress(ObjectDoesNotExist):
                        item = action.transactiontypeactioninstrumenteventscheduleaction

                if item is None:
                    item = TransactionTypeActionInstrumentEventScheduleAction(transaction_type=instance)

                for attr, value in item_data.items():
                    setattr(item, attr, value)

                item.order = order
                item.rebook_reaction = action_data.get("rebook_reaction", item.rebook_reaction)
                item.action_notes = action_data.get("action_notes", item.action_notes)
                item.condition_expr = action_data.get("condition_expr", item.condition_expr)

                item.save()
                actions[order] = item

    def save_actions(self, instance, actions_data, inputs):
        actions_qs = instance.actions.select_related(
            "transactiontypeactioninstrument",
            "transactiontypeactiontransaction",
            "transactiontypeactioninstrumentfactorschedule",
            "transactiontypeactioninstrumentmanualpricingformula",
            "transactiontypeactioninstrumentaccrualcalculationschedules",
            "transactiontypeactioninstrumenteventschedule",
            "transactiontypeactioninstrumenteventscheduleaction",
            "transactiontypeactionexecutecommand",
        ).order_by("order", "id")
        existed_actions = {a.id: a for a in actions_qs}

        if inputs is None or inputs is empty:
            inputs = {i.name: i for i in instance.inputs.all()}
        else:
            inputs = {i.name: i for i in inputs}

        actions = [None for _ in actions_data]

        self.save_actions_instrument(instance, inputs, actions, existed_actions, actions_data)

        self.save_actions_transaction(instance, inputs, actions, existed_actions, actions_data)

        self.save_actions_instrument_factor_schedule(instance, inputs, actions, existed_actions, actions_data)

        self.save_actions_instrument_manual_pricing_formula(instance, inputs, actions, existed_actions, actions_data)

        self.save_actions_instrument_accrual_calculation_schedule(
            instance, inputs, actions, existed_actions, actions_data
        )

        self.save_actions_instrument_event_schedule(instance, inputs, actions, existed_actions, actions_data)

        self.save_actions_instrument_event_schedule_action(instance, inputs, actions, existed_actions, actions_data)

        self.save_actions_execute_command(instance, inputs, actions, existed_actions, actions_data)

        return actions


class TransactionTypeViewSerializer(ModelWithUserCodeSerializer):
    group = TransactionTypeGroupField(required=False, allow_null=False)

    # group_object = TransactionTypeGroupViewSerializer(source='group', read_only=True)

    class Meta:
        model = TransactionType
        fields = [
            "id",
            "group",
            "user_code",
            "name",
            "short_name",
            "public_name",
            "notes",
            "is_valid_for_all_portfolios",
            "is_valid_for_all_instruments",
            "is_deleted",
            "transaction_unique_code_expr",
            "transaction_unique_code_options",
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
            "user_text_21",
            "user_text_22",
            "user_text_23",
            "user_text_24",
            "user_text_25",
            "user_text_26",
            "user_text_27",
            "user_text_28",
            "user_text_29",
            "user_text_30",
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

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        try:
            if isinstance(representation["group"], int):
                instance = TransactionTypeGroup.objects.get(id=representation["group"])
            else:
                instance = TransactionTypeGroup.objects.get(user_code=representation["group"])

            s = TransactionTypeGroupViewSerializer(instance=instance, read_only=True, context=self.context)
            representation["group_object"] = s.data
        except TransactionTypeGroup.DoesNotExist:
            representation["group_object"] = None

        return representation


class TransactionTypeViewOnlySerializer(ModelWithUserCodeSerializer):
    inputs = TransactionTypeInputViewOnlySerializer(required=False, many=True)

    class Meta:
        model = TransactionType
        fields = [
            "id",
            "master_user",
            "group",
            "user_code",
            "name",
            "short_name",
            "public_name",
            "notes",
            "inputs",
        ]


class TransactionSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            "id",
        ]


class TransactionSerializer(serializers.ModelSerializer):
    master_user = MasterUserField()
    complex_transaction = serializers.PrimaryKeyRelatedField(read_only=True)
    complex_transaction_order = serializers.IntegerField(read_only=True)
    instrument = InstrumentField(required=False, allow_null=True)
    transaction_currency = CurrencyField(default=CurrencyDefault(), required=False, allow_null=True)
    settlement_currency = CurrencyField(default=SystemCurrencyDefault())
    portfolio = PortfolioField(default=PortfolioDefault())
    account_cash = AccountField(default=AccountDefault())
    account_position = AccountField(default=AccountDefault())
    account_interim = AccountField(default=AccountDefault())
    strategy1_position = Strategy1Field(default=Strategy1Default())
    strategy1_cash = Strategy1Field(default=Strategy1Default())
    strategy2_position = Strategy2Field(default=Strategy2Default())
    strategy2_cash = Strategy2Field(default=Strategy2Default())
    strategy3_position = Strategy3Field(default=Strategy3Default())
    strategy3_cash = Strategy3Field(default=Strategy3Default())
    responsible = ResponsibleField(default=ResponsibleDefault())
    counterparty = CounterpartyField(default=CounterpartyDefault())
    linked_instrument = InstrumentField(default=InstrumentDefault())
    allocation_balance = InstrumentField(default=InstrumentDefault())
    allocation_pl = InstrumentField(default=InstrumentDefault())

    class Meta:
        model = Transaction
        fields = [
            "id",
            "master_user",
            "transaction_code",
            "complex_transaction",
            "complex_transaction_order",
            "transaction_class",
            "instrument",
            "transaction_currency",
            "position_size_with_sign",
            "settlement_currency",
            "cash_consideration",
            "principal_with_sign",
            "carry_with_sign",
            "overheads_with_sign",
            "reference_fx_rate",
            "accounting_date",
            "cash_date",
            "transaction_date",
            "portfolio",
            "account_cash",
            "account_position",
            "account_interim",
            "strategy1_position",
            "strategy1_cash",
            "strategy2_position",
            "strategy2_cash",
            "strategy3_position",
            "strategy3_cash",
            "responsible",
            "counterparty",
            "linked_instrument",
            "allocation_balance",
            "allocation_pl",
            # 'is_locked',
            "is_canceled",
            "is_deleted",
            "error_code",
            "factor",
            "trade_price",
            "position_amount",
            "principal_amount",
            "carry_amount",
            "overheads",
            "ytm_at_cost",
            "notes",
            "user_text_1",
            "user_text_2",
            "user_text_3",
            "user_number_1",
            "user_number_2",
            "user_number_3",
            "user_date_1",
            "user_date_2",
            "user_date_3",
        ]

    def __init__(self, *args, **kwargs):
        skip_complex_transaction = kwargs.pop("skip_complex_transaction", False)
        super().__init__(*args, **kwargs)

        from poms.accounts.serializers import AccountViewSerializer
        from poms.counterparties.serializers import (
            CounterpartyViewSerializer,
            ResponsibleViewSerializer,
        )
        from poms.currencies.serializers import CurrencyViewSerializer
        from poms.instruments.serializers import InstrumentViewSerializer
        from poms.portfolios.serializers import PortfolioViewSerializer
        from poms.strategies.serializers import (
            Strategy1ViewSerializer,
            Strategy2ViewSerializer,
            Strategy3ViewSerializer,
        )

        self.fields["transaction_class_object"] = TransactionClassSerializer(
            source="transaction_class", read_only=True
        )

        if not skip_complex_transaction:
            self.fields["complex_transaction_object"] = ComplexTransactionViewSerializer(
                source="complex_transaction", read_only=True
            )

        self.fields["instrument_object"] = InstrumentViewSerializer(source="instrument", read_only=True)
        self.fields["transaction_currency_object"] = CurrencyViewSerializer(
            source="transaction_currency", read_only=True
        )
        self.fields["settlement_currency_object"] = CurrencyViewSerializer(
            source="settlement_currency", read_only=True
        )

        self.fields["portfolio_object"] = PortfolioViewSerializer(source="portfolio", read_only=True)

        self.fields["account_position_object"] = AccountViewSerializer(source="account_position", read_only=True)
        self.fields["account_cash_object"] = AccountViewSerializer(source="account_cash", read_only=True)
        self.fields["account_interim_object"] = AccountViewSerializer(source="account_interim", read_only=True)

        self.fields["strategy1_position_object"] = Strategy1ViewSerializer(source="strategy1_position", read_only=True)
        self.fields["strategy1_cash_object"] = Strategy1ViewSerializer(source="strategy1_cash", read_only=True)
        self.fields["strategy2_position_object"] = Strategy2ViewSerializer(source="strategy2_position", read_only=True)
        self.fields["strategy2_cash_object"] = Strategy2ViewSerializer(source="strategy2_cash", read_only=True)
        self.fields["strategy3_position_object"] = Strategy3ViewSerializer(source="strategy3_position", read_only=True)
        self.fields["strategy3_cash_object"] = Strategy3ViewSerializer(source="strategy3_cash", read_only=True)

        self.fields["responsible_object"] = ResponsibleViewSerializer(source="responsible", read_only=True)
        self.fields["counterparty_object"] = CounterpartyViewSerializer(source="counterparty", read_only=True)

        self.fields["linked_instrument_object"] = InstrumentViewSerializer(source="linked_instrument", read_only=True)
        self.fields["allocation_balance_object"] = InstrumentViewSerializer(
            source="allocation_balance", read_only=True
        )
        self.fields["allocation_pl_object"] = InstrumentViewSerializer(source="allocation_pl", read_only=True)


# TODO check permissions?
class TransactionViewOnlySerializer(serializers.ModelSerializer):
    master_user = MasterUserField()
    complex_transaction = serializers.PrimaryKeyRelatedField(read_only=True)
    complex_transaction_order = serializers.IntegerField(read_only=True)

    instrument = InstrumentField(required=False, allow_null=True)
    settlement_currency = CurrencyField(default=SystemCurrencyDefault())
    portfolio = PortfolioField(default=PortfolioDefault())
    account_position = AccountField(default=AccountDefault())

    class Meta:
        model = Transaction
        fields = [
            "id",
            "master_user",
            "transaction_code",
            "complex_transaction",
            "complex_transaction_order",
            "transaction_class",
            "instrument",
            "settlement_currency",
            "portfolio",
            "account_position",
        ]

    def __init__(self, *args, **kwargs):
        from poms.accounts.serializers import AccountViewSerializer
        from poms.currencies.serializers import CurrencyViewSerializer
        from poms.instruments.serializers import InstrumentViewSerializer
        from poms.portfolios.serializers import PortfolioViewSerializer

        skip_complex_transaction = kwargs.pop("skip_complex_transaction", False)  # noqa: F841
        super().__init__(*args, **kwargs)

        self.fields["transaction_class_object"] = TransactionClassSerializer(
            source="transaction_class", read_only=True
        )

        self.fields["instrument_object"] = InstrumentViewSerializer(source="instrument", read_only=True)
        self.fields["settlement_currency_object"] = CurrencyViewSerializer(
            source="settlement_currency", read_only=True
        )

        self.fields["portfolio_object"] = PortfolioViewSerializer(source="portfolio", read_only=True)

        self.fields["account_position_object"] = AccountViewSerializer(source="account_position", read_only=True)


class InstrumentSimpleViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instrument
        fields = [
            "id",
            "user_code",
            "name",
            "short_name",
            "public_name",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class AccountSimpleViewSerializer(ModelWithUserCodeSerializer):
    class Meta:
        model = Account
        fields = [
            "id",
            "user_code",
            "name",
            "short_name",
            "public_name",
        ]


class ResponsibleSimpleViewSerializer(ModelWithUserCodeSerializer):
    class Meta:
        model = Responsible
        fields = [
            "id",
            "user_code",
            "name",
            "short_name",
            "public_name",
        ]


class CounterpartySimpleViewSerializer(ModelWithUserCodeSerializer):
    class Meta:
        model = Counterparty
        fields = [
            "id",
            "user_code",
            "name",
            "short_name",
            "public_name",
        ]


class Strategy1SimpleViewSerializer(ModelWithUserCodeSerializer):
    class Meta:
        model = Strategy1
        fields = [
            "id",
            "user_code",
            "name",
            "short_name",
            "public_name",
            "is_deleted",
        ]


class Strategy2SimpleViewSerializer(ModelWithUserCodeSerializer):
    class Meta:
        model = Strategy2
        fields = [
            "id",
            "user_code",
            "name",
            "short_name",
            "public_name",
            "is_deleted",
        ]


class Strategy3SimpleViewSerializer(ModelWithUserCodeSerializer):
    class Meta:
        model = Strategy3
        fields = [
            "id",
            "user_code",
            "name",
            "short_name",
            "public_name",
            "is_deleted",
        ]


class TransactionTextRenderSerializer(TransactionSerializer):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("skip_complex_transaction", True)
        super().__init__(*args, **kwargs)

    class Meta(TransactionSerializer.Meta):
        fields = [
            "id",
            "master_user",
            "transaction_code",
            "complex_transaction",
            "complex_transaction_order",
            "transaction_class",
            "instrument",
            "transaction_currency",
            "position_size_with_sign",
            "settlement_currency",
            "cash_consideration",
            "principal_with_sign",
            "carry_with_sign",
            "overheads_with_sign",
            "reference_fx_rate",
            "accounting_date",
            "cash_date",
            "transaction_date",
            "portfolio",
            "account_cash",
            "account_position",
            "account_interim",
            "strategy1_position",
            "strategy1_cash",
            "strategy2_position",
            "strategy2_cash",
            "strategy3_position",
            "strategy3_cash",
            "responsible",
            "counterparty",
            "linked_instrument",
            "allocation_balance",
            "allocation_pl",
            # 'is_locked',
            "is_canceled",
            # 'is_deleted',
            "error_code",
            "factor",
            "trade_price",
            "position_amount",
            "principal_amount",
            "carry_amount",
            "overheads",
            "ytm_at_cost",
            "notes",
        ]

        read_only_fields = fields


# noinspection PyUnresolvedReferences
class ComplexTransactionMixin:
    def get_text(self, obj):
        return None

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if "text" in self.fields:
            if instance.transaction_type.display_expr:
                ctrn = formula.value_prepare(representation)
                trns = ctrn.get("transactions", None)
                names = {
                    "complex_transaction": ctrn,
                    "transactions": trns,
                }
                try:
                    instance._cached_text = formula.safe_eval(
                        instance.transaction_type.display_expr,
                        names=names,
                        context=self.context,
                    )
                except formula.InvalidExpression:
                    instance._cached_text = "<InvalidExpression>"
            else:
                instance._cached_text = ""
            representation["text"] = instance._cached_text
        return representation


class ComplexTransactionInputSerializer(serializers.ModelSerializer):
    transaction_type_input = TransactionTypeInputField()
    transaction_type_input_object = TransactionTypeInputSerializer(source="transaction_type_input")
    value_type = serializers.SerializerMethodField(read_only=True)
    content_type = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ComplexTransactionInput
        fields = [
            "transaction_type_input",
            "transaction_type_input_object",
            "content_type",
            "value_type",
            "value_string",
            "value_float",
            "value_date",
            "value_relation",
        ]

    def get_value_type(self, instance):
        return instance.transaction_type_input.value_type

    def get_content_type(self, instance):
        return (
            f"{instance.transaction_type_input.content_type.app_label}.{instance.transaction_type_input.content_type.model}"
            if instance.transaction_type_input.content_type
            else None
        )


def remove_user_fields_from_representation(data: dict) -> dict:
    for i in range(1, 31):
        data.pop(f"user_text_{i}", None)

    for i in range(1, 21):
        data.pop(f"user_number_{i}", None)

    for i in range(1, 6):
        data.pop(f"user_date_{i}", None)

    return data


class ComplexTransactionSerializer(ModelWithAttributesSerializer, ModelWithTimeStampSerializer, ModelMetaSerializer):
    master_user = MasterUserField()
    transaction_type = serializers.PrimaryKeyRelatedField(read_only=True)
    transactions = serializers.PrimaryKeyRelatedField(read_only=True, many=True)
    recon_fields = ReconciliationComplexTransactionFieldSerializer(required=False, many=True)
    source = serializers.JSONField(read_only=True, allow_null=True)
    inputs = ComplexTransactionInputSerializer(many=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["transaction_type_object"] = TransactionTypeViewSerializer(
            source="transaction_type", read_only=True
        )
        self.fields["transactions_object"] = TransactionSerializer(source="transactions", many=True, read_only=True)

    class Meta:
        model = ComplexTransaction
        fields = [
            "id",
            "date",
            "status",
            "code",
            "text",
            "transaction_type",
            "transactions",
            "master_user",
            "transaction_unique_code",
            "is_locked",
            "is_canceled",
            "error_code",
            "is_deleted",
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
            "user_text_21",
            "user_text_22",
            "user_text_23",
            "user_text_24",
            "user_text_25",
            "user_text_26",
            "user_text_27",
            "user_text_28",
            "user_text_29",
            "user_text_30",
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
            "recon_fields",
            "execution_log",
            "source",
            "inputs",
        ]

    def to_representation(self, instance):
        member = get_member_from_context(self.context)
        hide_parameters = not member.is_admin and not member.is_owner

        representation = super().to_representation(instance)
        if hide_parameters:
            remove_user_fields_from_representation(representation)

        return representation


class ComplexTransactionSimpleSerializer(ModelWithAttributesSerializer):
    class Meta:
        model = ComplexTransaction
        fields = ["id", "is_locked", "is_canceled", "status", "is_deleted"]

    def update_base_transactions_permissions(self, instance, complex_transaction_permissions):
        view_permissions = []

        for perm in complex_transaction_permissions:
            values = list(perm.values())

            permission = values[2]
            if "change" in permission.codename:
                group = values[0]
                if group:
                    view_permissions.append(
                        {
                            "member": None,
                            "group": group.id,
                            "permission": "view_transaction",
                        }
                    )

        transactions = Transaction.objects.filter(complex_transaction__id=instance.id)

        for transaction in transactions:
            serializer = TransactionSimpleSerializer(
                instance=transaction,
                data={"object_permissions": view_permissions},
                context=self.context,
            )

            serializer.is_valid(raise_exception=True)

            serializer.save()

    def update(self, instance, validated_data):
        print(f"here? {validated_data}")

        transactions = Transaction.objects.filter(complex_transaction=instance.id)

        for transaction in transactions:
            if "is_locked" in validated_data:
                transaction.is_locked = validated_data["is_locked"]
                transaction.save()

            if "is_canceled" in validated_data:
                transaction.is_canceled = validated_data["is_canceled"]
                transaction.save()

        if "object_permissions" in validated_data:
            self.update_base_transactions_permissions(instance, validated_data["object_permissions"])

        instance = super().update(instance, validated_data)

        return instance


class ComplexTransactionViewSerializer(ComplexTransactionMixin, serializers.ModelSerializer):
    transaction_type = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = ComplexTransaction
        fields = [
            "id",
            "date",
            "status",
            "code",
            "text",
            "transaction_type",
            "transaction_unique_code",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["transaction_type_object"] = TransactionTypeViewSerializer(
            source="transaction_type", read_only=True
        )
        self.fields["transactions_object"] = TransactionSerializer(
            source="transactions",
            many=True,
            read_only=True,
            skip_complex_transaction=True,
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.pop("transactions_object", None)
        return data


class ComplexTransactionLightSerializer(ModelWithAttributesSerializer):
    master_user = MasterUserField()
    transaction_type = serializers.PrimaryKeyRelatedField(read_only=True)
    first_transaction_accounting_date = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["transaction_type_object"] = TransactionTypeViewSerializer(
            source="transaction_type", read_only=True
        )

    class Meta:
        model = ComplexTransaction
        fields = [
            "id",
            "date",
            "first_transaction_accounting_date",
            "status",
            "code",
            "text",
            "transaction_type",
            "master_user",
            "visibility_status",
            "is_locked",
            "is_canceled",
            "is_deleted",
            "transaction_unique_code",
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
            "user_text_21",
            "user_text_22",
            "user_text_23",
            "user_text_24",
            "user_text_25",
            "user_text_26",
            "user_text_27",
            "user_text_28",
            "user_text_29",
            "user_text_30",
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

    def get_first_transaction_accounting_date(self, instance):
        if instance.transactions.count():
            return instance.transactions.first().accounting_date

        return None

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        member = get_member_from_context(self.context)

        hide_parameters = not member.is_admin and not member.is_owner
        if hide_parameters:
            remove_user_fields_from_representation(representation)

        return representation


class ComplexTransactionEvItemSerializer(ModelWithAttributesSerializer):
    master_user = MasterUserField()
    transaction_type = serializers.PrimaryKeyRelatedField(read_only=True)
    first_transaction_accounting_date = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["transaction_type_object"] = TransactionTypeViewSerializer(
            source="transaction_type", read_only=True
        )

    class Meta:
        model = ComplexTransaction
        fields = [
            "id",
            "date",
            "first_transaction_accounting_date",
            "status",
            "code",
            "text",
            "transaction_type",
            "master_user",
            "visibility_status",
            "is_locked",
            "is_canceled",
            "is_deleted",
            "transaction_unique_code",
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
            "user_text_21",
            "user_text_22",
            "user_text_23",
            "user_text_24",
            "user_text_25",
            "user_text_26",
            "user_text_27",
            "user_text_28",
            "user_text_29",
            "user_text_30",
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

    def get_first_transaction_accounting_date(self, instance):
        if instance.transactions.count():
            return instance.transactions.first().accounting_date

        return None

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        member = get_member_from_context(self.context)

        hide_parameters = not member.is_admin and not member.is_owner
        if hide_parameters:
            remove_user_fields_from_representation(representation)

        return representation


# TransactionType processing --------------------------------------------------------


class TransactionTypeProcessValuesSerializer(serializers.Serializer):
    def __init__(self, **kwargs):  # noqa: PLR0912, PLR0915
        from poms.accounts.serializers import AccountViewSerializer
        from poms.counterparties.serializers import (
            CounterpartyViewSerializer,
            ResponsibleViewSerializer,
        )
        from poms.currencies.serializers import CurrencyViewSerializer
        from poms.instruments.serializers import (
            DailyPricingModelSerializer,
            EventScheduleSerializer,
            InstrumentTypeViewSerializer,
            InstrumentViewSerializer,
            PaymentSizeDetailSerializer,
            PricingPolicyViewSerializer,
        )
        from poms.integrations.serializers import PriceDownloadSchemeViewSerializer
        from poms.portfolios.serializers import PortfolioViewSerializer
        from poms.strategies.serializers import (
            Strategy1ViewSerializer,
            Strategy2ViewSerializer,
            Strategy3ViewSerializer,
        )

        super().__init__(**kwargs)

        _st = time.perf_counter()

        for i in self.instance.inputs:
            name = i.name
            name_object = f"{name}_object"
            field = None
            field_object = None

            if i.value_type in (
                TransactionTypeInput.STRING,
                TransactionTypeInput.SELECTOR,
            ):
                field = serializers.CharField(
                    required=False,
                    allow_blank=True,
                    allow_null=True,
                    label=i.name,
                    help_text=i.verbose_name,
                )

            elif i.value_type == TransactionTypeInput.NUMBER:
                field = serializers.FloatField(
                    required=False,
                    allow_null=True,
                    label=i.name,
                    help_text=i.verbose_name,
                )

            elif i.value_type == TransactionTypeInput.DATE:
                field = serializers.DateField(
                    required=False,
                    allow_null=True,
                    label=i.name,
                    help_text=i.verbose_name,
                )

            elif i.value_type == TransactionTypeInput.RELATION:
                model_class = i.content_type.model_class()

                if issubclass(model_class, Account):
                    field = AccountField(
                        required=False,
                        allow_null=True,
                        label=i.name,
                        help_text=i.verbose_name,
                    )
                    field_object = AccountViewSerializer(source=name, read_only=True)

                elif issubclass(model_class, Currency):
                    field = CurrencyField(
                        required=False,
                        allow_null=True,
                        label=i.name,
                        help_text=i.verbose_name,
                    )
                    field_object = CurrencyViewSerializer(source=name, read_only=True)

                elif issubclass(model_class, Instrument):
                    field = InstrumentField(
                        required=False,
                        allow_null=True,
                        label=i.name,
                        help_text=i.verbose_name,
                    )
                    field_object = InstrumentViewSerializer(source=name, read_only=True)

                elif issubclass(model_class, InstrumentType):
                    field = InstrumentTypeField(
                        required=False,
                        allow_null=True,
                        label=i.name,
                        help_text=i.verbose_name,
                    )
                    field_object = InstrumentTypeViewSerializer(source=name, read_only=True)

                elif issubclass(model_class, Counterparty):
                    field = CounterpartyField(
                        required=False,
                        allow_null=True,
                        label=i.name,
                        help_text=i.verbose_name,
                    )
                    field_object = CounterpartyViewSerializer(source=name, read_only=True)

                elif issubclass(model_class, Responsible):
                    field = ResponsibleField(
                        required=False,
                        allow_null=True,
                        label=i.name,
                        help_text=i.verbose_name,
                    )
                    field_object = ResponsibleViewSerializer(source=name, read_only=True)

                elif issubclass(model_class, Strategy1):
                    field = Strategy1Field(
                        required=False,
                        allow_null=True,
                        label=i.name,
                        help_text=i.verbose_name,
                    )
                    field_object = Strategy1ViewSerializer(source=name, read_only=True)

                elif issubclass(model_class, Strategy2):
                    field = Strategy2Field(
                        required=False,
                        allow_null=True,
                        label=i.name,
                        help_text=i.verbose_name,
                    )
                    field_object = Strategy2ViewSerializer(source=name, read_only=True)

                elif issubclass(model_class, Strategy3):
                    field = Strategy3Field(
                        required=False,
                        allow_null=True,
                        label=i.name,
                        help_text=i.verbose_name,
                    )
                    field_object = Strategy3ViewSerializer(source=name, read_only=True)

                elif issubclass(model_class, DailyPricingModel):
                    field = serializers.PrimaryKeyRelatedField(
                        queryset=DailyPricingModel.objects,
                        required=False,
                        allow_null=True,
                        label=i.name,
                        help_text=i.verbose_name,
                    )
                    field_object = DailyPricingModelSerializer(source=name, read_only=True)

                elif issubclass(model_class, PaymentSizeDetail):
                    field = serializers.PrimaryKeyRelatedField(
                        queryset=PaymentSizeDetail.objects,
                        required=False,
                        allow_null=True,
                        label=i.name,
                        help_text=i.verbose_name,
                    )
                    field_object = PaymentSizeDetailSerializer(source=name, read_only=True)

                elif issubclass(model_class, Portfolio):
                    field = PortfolioField(
                        required=False,
                        allow_null=True,
                        label=i.name,
                        help_text=i.verbose_name,
                    )
                    field_object = PortfolioViewSerializer(source=name, read_only=True)

                elif issubclass(model_class, PriceDownloadScheme):
                    field = PriceDownloadSchemeField(
                        required=False,
                        allow_null=True,
                        label=i.name,
                        help_text=i.verbose_name,
                    )
                    field_object = PriceDownloadSchemeViewSerializer(source=name, read_only=True)

                elif issubclass(model_class, PricingPolicy):
                    field = PricingPolicyField(
                        required=False,
                        allow_null=True,
                        label=i.name,
                        help_text=i.verbose_name,
                    )
                    field_object = PricingPolicyViewSerializer(source=name, read_only=True)

                elif issubclass(model_class, Periodicity):
                    field = PeriodicityField(
                        required=False,
                        allow_null=True,
                        label=i.name,
                        help_text=i.verbose_name,
                    )
                    from poms.instruments.serializers import PeriodicitySerializer

                    field_object = PeriodicitySerializer(source=name, read_only=True)

                elif issubclass(model_class, AccrualCalculationModel):
                    field = AccrualCalculationModelField(
                        required=False,
                        allow_null=True,
                        label=i.name,
                        help_text=i.verbose_name,
                    )
                    from poms.instruments.serializers import (
                        AccrualCalculationModelSerializer,
                    )

                    field_object = AccrualCalculationModelSerializer(source=name, read_only=True)

                elif issubclass(model_class, EventClass):
                    field = EventClassField(
                        required=False,
                        allow_null=True,
                        label=i.name,
                        help_text=i.verbose_name,
                    )
                    field_object = EventClassSerializer(source=name, read_only=True)

                elif issubclass(model_class, NotificationClass):
                    field = NotificationClassField(
                        required=False,
                        allow_null=True,
                        label=i.name,
                        help_text=i.verbose_name,
                    )
                    field_object = NotificationClassSerializer(source=name, read_only=True)

                elif issubclass(model_class, EventSchedule):
                    field = EventScheduleField(
                        required=False,
                        allow_null=True,
                        label=i.name,
                        help_text=i.verbose_name,
                    )
                    field_object = EventScheduleSerializer(source=name, read_only=True)

            elif i.value_type == TransactionTypeInput.BUTTON:
                field = serializers.JSONField(allow_null=True, required=False)

            if not field:
                raise RuntimeError(f"Unknown value type {i.value_type}")

            self.fields[name] = field
            if field_object:
                self.fields[name_object] = field_object

        result_time = f"{time.perf_counter() - _st:3.3f}"
        _l.info(f"TransactionTypeProcessValuesSerializer serialize {result_time}")


class PhantomInstrumentField(InstrumentField):
    def to_internal_value(self, value):
        pk = value
        if self.pk_field is not None:
            pk = self.pk_field.to_internal_value(value)

        return Instrument(id=pk) if pk and pk < 0 else super().to_internal_value(value)


class PhantomTransactionSerializer(TransactionSerializer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fields["instrument"] = PhantomInstrumentField(required=False)
        self.fields.pop("attributes")


class TransactionTypeComplexTransactionSerializer(ModelWithAttributesSerializer):
    master_user = MasterUserField()
    transaction_type = serializers.PrimaryKeyRelatedField(read_only=True)
    transactions = serializers.PrimaryKeyRelatedField(read_only=True, many=True)
    date = serializers.DateField(required=False, allow_null=True)
    code = serializers.IntegerField(
        default=0,
        initial=0,
        min_value=0,
        required=False,
        allow_null=True,
    )
    visibility_status = serializers.ChoiceField(
        default=ComplexTransaction.SHOW_PARAMETERS,
        initial=ComplexTransaction.SHOW_PARAMETERS,
        required=False,
        choices=ComplexTransaction.VISIBILITY_STATUS_CHOICES,
    )
    recon_fields = ReconciliationComplexTransactionFieldSerializer(
        read_only=True,
        many=True,
    )
    source = serializers.JSONField(read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["transaction_type_object"] = TransactionTypeViewSerializer(
            source="transaction_type", read_only=True
        )
        self.fields["transactions_object"] = TransactionSerializer(source="transactions", many=True, read_only=True)

    class Meta:
        model = ComplexTransaction
        fields = [
            "id",
            "date",
            "status",
            "code",
            "text",
            "transaction_type",
            "transactions",
            "master_user",
            "is_locked",
            "is_canceled",
            "is_deleted",
            "error_code",
            "visibility_status",
            "transaction_unique_code",
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
            "user_text_21",
            "user_text_22",
            "user_text_23",
            "user_text_24",
            "user_text_25",
            "user_text_26",
            "user_text_27",
            "user_text_28",
            "user_text_29",
            "user_text_30",
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
            "recon_fields",
            "execution_log",
            "source",
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        member = get_member_from_context(self.context)

        hide_parameters = not member.is_admin and not member.is_owner
        if hide_parameters:
            remove_user_fields_from_representation(representation)

        return representation


class ComplexTransactionViewOnlyComplexTransactionSerializer(serializers.ModelSerializer):
    source = serializers.JSONField(read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["transactions_object"] = TransactionViewOnlySerializer(
            source="transactions", many=True, read_only=True
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
            "transactions",
            "master_user",
            "is_locked",
            "is_canceled",
            "error_code",
            "visibility_status",
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
            "user_text_21",
            "user_text_22",
            "user_text_23",
            "user_text_24",
            "user_text_25",
            "user_text_26",
            "user_text_27",
            "user_text_28",
            "user_text_29",
            "user_text_30",
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
            "execution_log",
            "source",
        ]


class ComplexTransactionViewOnly:
    def __init__(self, complex_transaction, transaction_type):
        _st = time.perf_counter()

        self.complex_transaction = complex_transaction
        self.transaction_type = transaction_type

        self.inputs = list(self.transaction_type.inputs.all())

        self.values = {}

        for ci in self.complex_transaction.inputs.all():
            i = ci.transaction_type_input
            value = None
            if i.value_type in (
                TransactionTypeInput.STRING,
                TransactionTypeInput.SELECTOR,
            ):
                value = ci.value_string
            elif i.value_type == TransactionTypeInput.NUMBER:
                value = ci.value_float
            elif i.value_type == TransactionTypeInput.DATE:
                value = ci.value_date
            elif i.value_type == TransactionTypeInput.RELATION:
                value = self._get_val_by_model_cls_for_complex_transaction_input(
                    self.complex_transaction.master_user,
                    ci,
                    i.content_type.model_class(),
                )
            if value is not None:
                self.values[i.name] = value

        result_time = f"{time.perf_counter() - _st:3.3f}"
        _l.debug(f"ComplexTransactionViewOnly.init {result_time}")

    def _get_val_by_model_cls_for_complex_transaction_input(self, master_user, obj, model_class):  # noqa: PLR0911, PLR0912
        try:
            if issubclass(model_class, Account):
                return Account.objects.get(master_user=master_user, user_code=obj.value_relation)
            elif issubclass(model_class, Currency):
                return Currency.objects.get(master_user=master_user, user_code=obj.value_relation)
            elif issubclass(model_class, Instrument):
                return Instrument.objects.get(master_user=master_user, user_code=obj.value_relation)
            elif issubclass(model_class, InstrumentType):
                return InstrumentType.objects.get(master_user=master_user, user_code=obj.value_relation)
            elif issubclass(model_class, Counterparty):
                return Counterparty.objects.get(master_user=master_user, user_code=obj.value_relation)
            elif issubclass(model_class, Responsible):
                return Responsible.objects.get(master_user=master_user, user_code=obj.value_relation)
            elif issubclass(model_class, Strategy1):
                return Strategy1.objects.get(master_user=master_user, user_code=obj.value_relation)
            elif issubclass(model_class, Strategy2):
                return Strategy2.objects.get(master_user=master_user, user_code=obj.value_relation)
            elif issubclass(model_class, Strategy3):
                return Strategy3.objects.get(master_user=master_user, user_code=obj.value_relation)
            elif issubclass(model_class, PaymentSizeDetail):
                return PaymentSizeDetail.objects.get(user_code=obj.value_relation)
            elif issubclass(model_class, Portfolio):
                return Portfolio.objects.get(master_user=master_user, user_code=obj.value_relation)
            elif issubclass(model_class, PricingPolicy):
                return PricingPolicy.objects.get(master_user=master_user, user_code=obj.value_relation)
            elif issubclass(model_class, Periodicity):
                return Periodicity.objects.get(user_code=obj.value_relation)
            elif issubclass(model_class, AccrualCalculationModel):
                return AccrualCalculationModel.objects.get(user_code=obj.value_relation)
            elif issubclass(model_class, EventClass):
                return EventClass.objects.get(user_code=obj.value_relation)
            elif issubclass(model_class, NotificationClass):
                return NotificationClass.objects.get(user_code=obj.value_relation)

        except Exception:
            _l.info(f"Could not find default value relation {obj.value_relation} ")
            return None


class ComplexTransactionViewOnlySerializer(serializers.Serializer):
    def __init__(self, **kwargs):
        kwargs["context"] = context = kwargs.get("context", {}) or {}
        super().__init__(**kwargs)
        context["instance"] = self.instance

        self.fields["transaction_type"] = serializers.PrimaryKeyRelatedField(read_only=True)
        self.fields["transaction_type_object"] = TransactionTypeViewOnlySerializer(
            source="transaction_type", read_only=True
        )
        self.fields["book_transaction_layout"] = serializers.SerializerMethodField()
        self.fields["complex_transaction_status"] = serializers.ChoiceField(
            required=False,
            allow_null=True,
            initial=ComplexTransaction.PRODUCTION,
            default=ComplexTransaction.PRODUCTION,
            choices=(
                (ComplexTransaction.PRODUCTION, "Production"),
                (ComplexTransaction.PENDING, "Pending"),
                (ComplexTransaction.IGNORE, "Ignore"),
            ),
        )
        self.fields["complex_transaction"] = ComplexTransactionViewOnlyComplexTransactionSerializer(
            read_only=False, required=False, allow_null=True
        )
        self.fields["values"] = TransactionTypeProcessValuesSerializer(instance=self.instance, required=False)

    def get_book_transaction_layout(self, obj):
        return obj.transaction_type.book_transaction_layout


class TransactionTypeProcessSerializer(serializers.Serializer):
    def __init__(self, **kwargs):
        from poms.instruments.serializers import InstrumentSerializer

        kwargs["context"] = context = kwargs.get("context", {}) or {}
        super().__init__(**kwargs)

        context["instance"] = self.instance

        self.fields["transaction_type"] = serializers.PrimaryKeyRelatedField(read_only=True)
        self.fields["complex_transaction_status"] = serializers.ChoiceField(
            required=False,
            allow_null=True,
            initial=ComplexTransaction.PRODUCTION,
            default=ComplexTransaction.PRODUCTION,
            choices=(
                (ComplexTransaction.PRODUCTION, "Production"),
                (ComplexTransaction.PENDING, "Pending"),
                (ComplexTransaction.IGNORE, "Ignore"),
            ),
        )
        self.fields["process_mode"] = serializers.ChoiceField(
            required=False,
            allow_null=True,
            initial=TransactionTypeProcess.MODE_BOOK,
            default=TransactionTypeProcess.MODE_BOOK,
            choices=(
                (TransactionTypeProcess.MODE_BOOK, "Book"),
                (TransactionTypeProcess.MODE_RECALCULATE, "Recalculate fields values"),
                (TransactionTypeProcess.MODE_REBOOK, "Rebook"),
            ),
        )

        if self.instance:
            self.fields["values"] = TransactionTypeProcessValuesSerializer(instance=self.instance, required=False)

        if self.instance:
            recalculate_inputs = [(i.name, i.verbose_name) for i in self.instance.inputs]
            self.fields["recalculate_inputs"] = serializers.ListField(
                required=False,
                allow_null=True,
                child=serializers.ChoiceField(choices=recalculate_inputs),
            )
        else:
            self.fields["recalculate_inputs"] = serializers.MultipleChoiceField(
                required=False, allow_null=True, choices=[]
            )

        self.fields["has_errors"] = serializers.BooleanField(read_only=True)
        self.fields["value_errors"] = serializers.ReadOnlyField()
        self.fields["instruments_errors"] = serializers.ReadOnlyField()
        self.fields["complex_transaction_errors"] = serializers.ReadOnlyField()
        self.fields["transactions_errors"] = serializers.ReadOnlyField()
        self.fields["general_errors"] = serializers.ReadOnlyField()
        self.fields["instruments"] = InstrumentSerializer(many=True, read_only=True, required=False, allow_null=True)
        self.fields["complex_transaction"] = TransactionTypeComplexTransactionSerializer(
            read_only=False, required=False, allow_null=True
        )
        self.fields["transaction_type_object"] = TransactionTypeSerializer(source="transaction_type", read_only=True)

        self.fields["book_transaction_layout"] = serializers.SerializerMethodField()

    def validate(self, attrs):
        return attrs

    def get_book_transaction_layout(self, obj):
        return obj.transaction_type.book_transaction_layout

    def create(self, validated_data):
        return validated_data

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            if key != "complex_transaction":
                setattr(instance, key, value)

        instance.value_errors = []

        _l.info("==== PROCESS REBOOK ====")
        instance.process()

        return instance


class TransactionTypeRecalculateSerializer(serializers.Serializer):
    def __init__(self, **kwargs):
        st = time.perf_counter()

        kwargs["context"] = context = kwargs.get("context", {}) or {}
        super().__init__(**kwargs)

        context["instance"] = self.instance

        self.fields["transaction_type"] = serializers.PrimaryKeyRelatedField(read_only=True)

        self.fields["process_mode"] = serializers.ChoiceField(
            required=False,
            allow_null=True,
            initial=TransactionTypeProcess.MODE_BOOK,
            default=TransactionTypeProcess.MODE_BOOK,
            choices=(
                (TransactionTypeProcess.MODE_BOOK, "Book"),
                (TransactionTypeProcess.MODE_RECALCULATE, "Recalculate fields values"),
                (TransactionTypeProcess.MODE_REBOOK, "Rebook"),
            ),
        )

        if self.instance:
            self.fields["values"] = TransactionTypeProcessValuesSerializer(instance=self.instance, required=False)

        if self.instance:
            recalculate_inputs = [(i.name, i.verbose_name) for i in self.instance.inputs]
            self.fields["recalculate_inputs"] = serializers.ListField(
                required=False,
                allow_null=True,
                child=serializers.ChoiceField(choices=recalculate_inputs),
            )
        else:
            self.fields["recalculate_inputs"] = serializers.MultipleChoiceField(
                required=False, allow_null=True, choices=[]
            )

        self.fields["complex_transaction"] = serializers.PrimaryKeyRelatedField(read_only=True)

        _l.debug(
            "TransactionTypeRecalculateSerializer init done: %s",
            f"{time.perf_counter() - st:3.3f}",
        )

    def validate(self, attrs):
        if attrs["process_mode"] == TransactionTypeProcess.MODE_BOOK:
            values = attrs["values"]
            fvalues = self.fields["values"]
            errors = {}
            for k, v in values.items():
                if v is None or v == "":
                    try:
                        if fvalues.fields[k].label != "notes":
                            fvalues.fields[k].fail("required")

                    except ValidationError as e:
                        errors[k] = e.detail
            if errors:
                raise ValidationError({"values": errors})
        return attrs

    def get_book_transaction_layout(self, obj):
        return obj.transaction_type.book_transaction_layout

    def create(self, validated_data):
        return validated_data

    def update(self, instance, validated_data):
        st = time.perf_counter()

        for key, value in validated_data.items():
            if key not in [
                "complex_transaction",
            ]:
                setattr(instance, key, value)
        instance.value_errors = []

        ctrn_values = validated_data.get("complex_transaction", None)
        if ctrn_values:
            instance.complex_transaction = self._create_complex_transaction(
                instance,
                ctrn_values,
            )

        instance.process()

        _l.debug(
            "TransactionTypeRecalculateSerializer done: %s",
            f"{time.perf_counter() - st:3.3f}",
        )

        return instance

    def _create_complex_transaction(self, instance, ctrn_values) -> ComplexTransaction:
        ctrn_ser = ComplexTransactionSerializer(instance=instance.complex_transaction, context=self.context)
        ctrn_values = ctrn_values.copy()

        is_date_was_empty = False
        if not ctrn_values.get("date", None):
            ctrn_values["date"] = datetime.date.min
            is_date_was_empty = True

        ctrn = (
            ctrn_ser.update(ctrn_ser.instance, ctrn_values)
            if instance.complex_transaction
            else ctrn_ser.create(ctrn_values)
        )
        if is_date_was_empty:
            ctrn.date = None

        return ctrn

    def to_representation(self, instance):
        st = time.perf_counter()

        representation = super().to_representation(instance)

        result_st = time.perf_counter() - st

        _l.debug(f"TransactionTypeRecalculateSerializer to representation done {result_st}")

        return representation


class RecalculatePermission:
    def __init__(self, task_id=None, task_status=None, master_user=None, member=None):
        self.task_id = task_id
        self.task_status = task_status

        self.master_user = master_user
        self.member = member


class RecalculatePermissionTransactionSerializer(serializers.Serializer):
    task_id = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    task_status = serializers.ReadOnlyField()

    master_user = MasterUserField()
    member = HiddenMemberField()

    content_type = serializers.ReadOnlyField()

    def create(self, validated_data):
        return RecalculatePermission(**validated_data)


class RecalculatePermissionComplexTransactionSerializer(serializers.Serializer):
    task_id = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    task_status = serializers.ReadOnlyField()

    master_user = MasterUserField()
    member = HiddenMemberField()

    content_type = serializers.ReadOnlyField()

    def create(self, validated_data):
        return RecalculatePermission(**validated_data)


class RecalculateUserFields:
    def __init__(
        self,
        task_id=None,
        task_status=None,
        master_user=None,
        member=None,
        transaction_type_id=None,
        key=None,
        total_rows=None,
        processed_rows=None,
        stats_file_report=None,
        stats=None,
    ):
        self.task_id = task_id
        self.task_status = task_status

        self.key = key

        self.master_user = master_user
        self.member = member
        self.transaction_type_id = transaction_type_id

        self.total_rows = total_rows
        self.processed_rows = processed_rows

        self.stats = stats
        self.stats_file_report = stats_file_report

    def __str__(self):
        return f"{getattr(self.master_user, 'name', None)}"


class RecalculateUserFieldsSerializer(serializers.Serializer):
    task_id = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    task_status = serializers.ReadOnlyField()

    master_user = MasterUserField()
    member = HiddenMemberField()
    transaction_type_id = serializers.IntegerField(allow_null=True, required=False)
    key = serializers.CharField(allow_null=True, allow_blank=True, required=False)

    processed_rows = serializers.ReadOnlyField()
    total_rows = serializers.ReadOnlyField()

    stats = serializers.ReadOnlyField()
    stats_file_report = serializers.ReadOnlyField()

    def create(self, validated_data):
        return RecalculateUserFields(**validated_data)


class TransactionEvalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            "id",
            "master_user",
            "transaction_code",
            "complex_transaction",
            "complex_transaction_order",
            "transaction_class",
            "instrument",
            "transaction_currency",
            "position_size_with_sign",
            "settlement_currency",
            "cash_consideration",
            "principal_with_sign",
            "carry_with_sign",
            "overheads_with_sign",
            "reference_fx_rate",
            "accounting_date",
            "cash_date",
            "transaction_date",
            "portfolio",
            "account_cash",
            "account_position",
            "account_interim",
            "strategy1_position",
            "strategy1_cash",
            "strategy2_position",
            "strategy2_cash",
            "strategy3_position",
            "strategy3_cash",
            "responsible",
            "counterparty",
            "linked_instrument",
            "allocation_balance",
            "allocation_pl",
            "is_canceled",
            "error_code",
            "factor",
            "trade_price",
            "position_amount",
            "principal_amount",
            "carry_amount",
            "overheads",
            "ytm_at_cost",
            "notes",
        ]

        read_only_fields = fields

    def __init__(self, *args, **kwargs):
        from poms.accounts.serializers import AccountEvalSerializer
        from poms.counterparties.serializers import (
            CounterpartyEvalSerializer,
            ResponsibleEvalSerializer,
        )
        from poms.currencies.serializers import CurrencyEvalSerializer
        from poms.instruments.serializers import InstrumentEvalSerializer
        from poms.portfolios.serializers import PortfolioEvalSerializer
        from poms.strategies.serializers import (
            Strategy1EvalSerializer,
            Strategy2EvalSerializer,
            Strategy3EvalSerializer,
        )

        skip_complex_transaction = kwargs.pop("skip_complex_transaction", False)  # noqa: F841
        super().__init__(*args, **kwargs)

        self.fields["portfolio"] = PortfolioEvalSerializer(read_only=True)

        self.fields["transaction_currency"] = CurrencyEvalSerializer(read_only=True)
        self.fields["settlement_currency"] = CurrencyEvalSerializer(read_only=True)

        self.fields["responsible"] = ResponsibleEvalSerializer(read_only=True)

        self.fields["counterparty"] = CounterpartyEvalSerializer(read_only=True)

        self.fields["account_cash"] = AccountEvalSerializer(read_only=True)
        self.fields["account_position"] = AccountEvalSerializer(read_only=True)
        self.fields["account_interim"] = AccountEvalSerializer(read_only=True)

        self.fields["strategy1_position"] = Strategy1EvalSerializer(read_only=True)
        self.fields["strategy1_cash"] = Strategy1EvalSerializer(read_only=True)

        self.fields["strategy2_position"] = Strategy2EvalSerializer(read_only=True)
        self.fields["strategy2_cash"] = Strategy2EvalSerializer(read_only=True)

        self.fields["strategy3_position"] = Strategy3EvalSerializer(read_only=True)
        self.fields["strategy3_cash"] = Strategy3EvalSerializer(read_only=True)

        self.fields["instrument"] = InstrumentEvalSerializer(read_only=True)
        self.fields["linked_instrument"] = InstrumentEvalSerializer(read_only=True)
        self.fields["allocation_balance"] = InstrumentEvalSerializer(read_only=True)
        self.fields["allocation_pl"] = InstrumentEvalSerializer(read_only=True)


class ComplexTransactionEvalSerializer(ComplexTransactionSerializer):
    transactions = TransactionEvalSerializer(many=True, read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("text", None)

    class Meta(ComplexTransactionSerializer.Meta):
        model = ComplexTransaction
        fields = [
            "id",
            "date",
            "status",
            "code",
            "text",
            "transaction_type",
            "transactions",
            "master_user",
            "transaction_unique_code",
            "is_locked",
            "is_canceled",
            "error_code",
            "is_deleted",
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
            "user_text_21",
            "user_text_22",
            "user_text_23",
            "user_text_24",
            "user_text_25",
            "user_text_26",
            "user_text_27",
            "user_text_28",
            "user_text_29",
            "user_text_30",
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

        read_only_fields = fields


class ComplexTransactionDeleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplexTransaction
        fields = [
            "id",
            "code",
            "date",
            "transaction_unique_code",
            "deleted_transaction_unique_code",
            "modified_at",
            "text",
            "user_text_1",
            "user_text_2",
            "user_text_3",
            "user_text_4",
            "user_text_5",
        ]

        read_only_fields = fields
