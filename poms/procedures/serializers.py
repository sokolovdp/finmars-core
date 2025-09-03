import contextlib

from rest_framework import serializers

from poms.common.fields import ExpressionField
from poms.common.models import EXPRESSION_FIELD_LENGTH
from poms.common.serializers import (
    ModelMetaSerializer,
    ModelWithTimeStampSerializer,
    ModelWithUserCodeSerializer,
)
from poms.expressions_engine import formula
from poms.procedures.models import (
    ExpressionProcedure,
    ExpressionProcedureContextVariable,
    PricingParentProcedureInstance,
    PricingProcedure,
    PricingProcedureInstance,
    RequestDataFileProcedure,
    RequestDataFileProcedureInstance,
)
from poms.users.fields import MasterUserField


class PricingProcedureSerializer(ModelWithTimeStampSerializer, ModelWithUserCodeSerializer, ModelMetaSerializer):
    master_user = MasterUserField()

    price_date_from_expr = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_null=True,
        allow_blank=True,
        default="",
    )
    price_date_to_expr = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_null=True,
        allow_blank=True,
        default="",
    )

    class Meta:
        model = PricingProcedure
        fields = (
            "master_user",
            "id",
            "name",
            "notes",
            "notes_for_users",
            "user_code",
            "type",
            "price_date_from",
            "price_date_to",
            "price_date_from_expr",
            "price_date_to_expr",
            "price_fill_days",
            "price_get_principal_prices",
            "price_get_accrued_prices",
            "price_get_fx_rates",
            "price_overwrite_principal_prices",
            "price_overwrite_accrued_prices",
            "price_overwrite_fx_rates",
            "instrument_filters",
            "currency_filters",
            "pricing_policy_filters",
            "portfolio_filters",
            "instrument_type_filters",
            "instrument_pricing_scheme_filters",
            "instrument_pricing_condition_filters",
            "currency_pricing_scheme_filters",
            "currency_pricing_condition_filters",
            "configuration_code",
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)

        if data["price_date_from_expr"]:
            try:
                data["price_date_from_calculated"] = str(formula.safe_eval(data["price_date_from_expr"], names={}))
            except formula.InvalidExpression:
                data["price_date_from_calculated"] = "Invalid Expression"
        else:
            data["price_date_from_calculated"] = str(data["price_date_from"])

        if data["price_date_to_expr"]:
            try:
                data["price_date_to_calculated"] = str(formula.safe_eval(data["price_date_to_expr"], names={}))
            except formula.InvalidExpression:
                data["price_date_to_calculated"] = "Invalid Expression"
        else:
            data["price_date_to_calculated"] = str(data["price_date_to"])

        return data


class PricingProcedureInstanceSerializer(serializers.ModelSerializer):
    procedure_object = PricingProcedureSerializer(source="procedure", read_only=True)

    request_data = serializers.JSONField(allow_null=True, required=False)
    response_data = serializers.JSONField(allow_null=True, required=False)

    class Meta:
        model = PricingProcedureInstance
        fields = (
            "master_user",
            "id",
            "parent_procedure_instance",
            "created_at",
            "modified_at",
            "status",
            "procedure",
            "procedure_object",
            "provider_verbose",
            "action_verbose",
            "successful_prices_count",
            "error_prices_count",
            "error_code",
            "error_message",
            "request_data",
            "response_data",
        )


class PricingParentProcedureInstanceSerializer(serializers.ModelSerializer):
    procedure_object = PricingProcedureSerializer(source="procedure", read_only=True)

    procedures = PricingProcedureInstanceSerializer(many=True, read_only=True)

    class Meta:
        model = PricingParentProcedureInstance
        fields = (
            "master_user",
            "id",
            "created_at",
            "modified_at",
            "procedure",
            "procedure_object",
            "procedures",
        )


class RunProcedureSerializer(serializers.Serializer):
    def __init__(self, **kwargs):
        kwargs["context"] = context = kwargs.get("context", {}) or {}
        super().__init__(**kwargs)
        context["instance"] = self.instance

        self.fields["procedure"] = serializers.PrimaryKeyRelatedField(read_only=True)


class RequestDataFileProcedureSerializer(
    ModelWithTimeStampSerializer, ModelWithUserCodeSerializer, ModelMetaSerializer
):
    master_user = MasterUserField()
    data = serializers.JSONField(allow_null=True, required=False)

    date_from_expr = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_null=True,
        allow_blank=True,
        default="",
    )
    date_to_expr = ExpressionField(
        max_length=EXPRESSION_FIELD_LENGTH,
        required=False,
        allow_null=True,
        allow_blank=True,
        default="",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        from poms.integrations.serializers import DataProviderSerializer

        self.fields["provider_object"] = DataProviderSerializer(source="provider", read_only=True)

    class Meta:
        model = RequestDataFileProcedure
        fields = [
            "id",
            "master_user",
            "name",
            "user_code",
            "notes",
            "provider",
            "scheme_user_code",
            "scheme_type",
            "data",
            "date_from_expr",
            "date_to_expr",
            "date_from",
            "date_to",
            "configuration_code",
        ]


class RequestDataFileProcedureInstanceSerializer(serializers.ModelSerializer):
    procedure_object = RequestDataFileProcedureSerializer(source="procedure", read_only=True)

    request_data = serializers.JSONField(allow_null=True, required=False)

    class Meta:
        model = RequestDataFileProcedureInstance
        fields = (
            "master_user",
            "id",
            "request_data",
            "status",
            "error_code",
            "error_message",
            "linked_import_task",
            "created_at",
            "modified_at",
            "response_data",
            "procedure",
            "procedure_object",
        )


class ExpressionProcedureContextVariableSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpressionProcedureContextVariable
        fields = ("id", "order", "name", "expression", "notes")


class ExpressionProcedureSerializer(ModelWithTimeStampSerializer, ModelWithUserCodeSerializer, ModelMetaSerializer):
    context_variables = ExpressionProcedureContextVariableSerializer(
        many=True, allow_null=True, required=False, read_only=False
    )

    master_user = MasterUserField()
    data = serializers.JSONField(allow_null=True, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = ExpressionProcedure
        fields = [
            "id",
            "master_user",
            "name",
            "user_code",
            "notes",
            "data",
            "context_variables",
            "code",
            "configuration_code",
        ]

    def save_context_variables(self, instance, items):
        pk_set = set()

        for item_values in items:
            item_id = item_values.pop("id", None)
            item = None
            if item_id:
                with contextlib.suppress(Exception):
                    item = instance.context_variables.get(pk=item_id)

            if item is None:
                item = ExpressionProcedureContextVariable(procedure=instance)
            for name, value in item_values.items():
                setattr(item, name, value)
            item.save()
            pk_set.add(item.id)

        instance.context_variables.exclude(pk__in=pk_set).delete()

    def create(self, validated_data):
        context_variables = validated_data.pop("context_variables", None) or []

        instance = super().create(validated_data)

        self.save_context_variables(instance, context_variables)

        return instance

    def update(self, instance, validated_data):
        context_variables = validated_data.pop("context_variables", None) or []

        instance = super().update(instance, validated_data)

        self.save_context_variables(instance, context_variables)

        return instance


class RunExpressionProcedureSerializer(serializers.Serializer):
    def __init__(self, **kwargs):
        kwargs["context"] = context = kwargs.get("context", {}) or {}
        super().__init__(**kwargs)
        context["instance"] = self.instance

        self.fields["procedure"] = serializers.PrimaryKeyRelatedField(read_only=True)
