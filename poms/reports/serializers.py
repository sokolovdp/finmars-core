from __future__ import unicode_literals

from datetime import timedelta

from django.conf import settings
from django.utils.translation import ugettext_lazy
from rest_framework import serializers

from poms.accounts.fields import AccountField
from poms.common.fields import ExpressionField
from poms.common.utils import date_now
from poms.currencies.fields import CurrencyField, SystemCurrencyDefault
from poms.instruments.fields import PricingPolicyField
from poms.instruments.models import CostMethod
from poms.portfolios.fields import PortfolioField
from poms.reports.builders import Report, ReportItem
from poms.reports.fields import CustomFieldField
from poms.reports.models import BalanceReport, BalanceReportItem, BalanceReportSummary, PLReportItem, PLReport, \
    PLReportSummary, CostReport, BaseReport, CustomField
from poms.strategies.fields import Strategy1Field, Strategy2Field, Strategy3Field
from poms.transactions.models import Transaction, TransactionClass
from poms.users.fields import MasterUserField


# class ReportClassSerializer(PomsClassSerializer):
#     class Meta(PomsClassSerializer.Meta):
#         model = ReportClass


class CustomFieldSerializer(serializers.ModelSerializer):
    master_user = MasterUserField()
    # report_class = ReportClassField()
    expr = ExpressionField(required=False, allow_blank=True, default='""')

    class Meta:
        model = CustomField
        fields = [
            'id', 'master_user', 'name', 'expr'
        ]


class CustomFieldViewSerializer(serializers.ModelSerializer):
    master_user = MasterUserField()

    class Meta:
        model = CustomField
        fields = [
            'id', 'master_user', 'name'
        ]


# new reports...


class ReportItemCustomFieldSerializer(serializers.Serializer):
    custom_field = serializers.PrimaryKeyRelatedField(read_only=True)
    value = serializers.ReadOnlyField()

    def __init__(self, *args, **kwargs):
        super(ReportItemCustomFieldSerializer, self).__init__(*args, **kwargs)

        self.fields['custom_field_object'] = CustomFieldViewSerializer(source='custom_field', read_only=True)


class ReportItemSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)

    type = serializers.ChoiceField(
        choices=ReportItem.TYPE_CHOICES
    )
    user_code = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField()

    instrument = serializers.PrimaryKeyRelatedField(read_only=True)
    currency = serializers.PrimaryKeyRelatedField(read_only=True)

    portfolio = serializers.PrimaryKeyRelatedField(read_only=True)
    account = serializers.PrimaryKeyRelatedField(read_only=True)
    strategy1 = serializers.PrimaryKeyRelatedField(read_only=True)
    strategy2 = serializers.PrimaryKeyRelatedField(read_only=True)
    strategy3 = serializers.PrimaryKeyRelatedField(read_only=True)

    position_size_with_sign = serializers.ReadOnlyField()

    market_value_system_ccy = serializers.ReadOnlyField()
    market_value_report_ccy = serializers.ReadOnlyField()

    principal_with_sign_system_ccy = serializers.ReadOnlyField()
    carry_with_sign_system_ccy = serializers.ReadOnlyField()
    overheads_with_sign_system_ccy = serializers.ReadOnlyField()
    total_with_sign_system_ccy = serializers.ReadOnlyField()

    principal_with_sign_report_ccy = serializers.ReadOnlyField()
    carry_with_sign_report_ccy = serializers.ReadOnlyField()
    overheads_with_sign_report_ccy = serializers.ReadOnlyField()
    total_with_sign_report_ccy = serializers.ReadOnlyField()

    custom_fields = ReportItemCustomFieldSerializer(many=True, read_only=True)

    def __init__(self, *args, **kwargs):
        super(ReportItemSerializer, self).__init__(*args, **kwargs)

        from poms.currencies.serializers import CurrencySerializer
        from poms.instruments.serializers import InstrumentSerializer
        from poms.portfolios.serializers import PortfolioViewSerializer
        from poms.accounts.serializers import AccountViewSerializer
        from poms.strategies.serializers import Strategy1ViewSerializer, Strategy2ViewSerializer, \
            Strategy3ViewSerializer

        self.fields['instrument_object'] = InstrumentSerializer(source='instrument', read_only=True)
        self.fields['currency_object'] = CurrencySerializer(source='currency', read_only=True)
        self.fields['portfolio_object'] = PortfolioViewSerializer(source='portfolio', read_only=True)
        self.fields['account_object'] = AccountViewSerializer(source='account', read_only=True)
        self.fields['strategy1_object'] = Strategy1ViewSerializer(source='strategy1', read_only=True)
        self.fields['strategy2_object'] = Strategy2ViewSerializer(source='strategy2', read_only=True)
        self.fields['strategy3_object'] = Strategy3ViewSerializer(source='strategy3', read_only=True)


class ReportSummarySerializer(serializers.Serializer):
    market_value_system_ccy = serializers.FloatField(read_only=True)
    market_value_report_ccy = serializers.FloatField(read_only=True)

    principal_with_sign_system_ccy = serializers.FloatField(read_only=True)
    carry_with_sign_system_ccy = serializers.FloatField(read_only=True)
    overheads_with_sign_system_ccy = serializers.FloatField(read_only=True)
    total_with_sign_system_ccy = serializers.FloatField(read_only=True)

    principal_with_sign_report_ccy = serializers.FloatField(read_only=True)
    carry_with_sign_report_ccy = serializers.FloatField(read_only=True)
    overheads_with_sign_report_ccy = serializers.FloatField(read_only=True)
    total_with_sign_report_ccy = serializers.FloatField(read_only=True)

    def __init__(self, *args, **kwargs):
        super(ReportSummarySerializer, self).__init__(*args, **kwargs)


class ReportSerializer(serializers.Serializer):
    task_id = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    task_status = serializers.ReadOnlyField()

    master_user = MasterUserField()

    pricing_policy = PricingPolicyField()
    report_date = serializers.DateField(required=False, allow_null=True, default=date_now)
    report_currency = CurrencyField(required=False, allow_null=True, default=SystemCurrencyDefault())
    cost_method = serializers.PrimaryKeyRelatedField(queryset=CostMethod.objects, allow_null=True, allow_empty=True)

    detail_by_portfolio = serializers.BooleanField(default=False)
    detail_by_account = serializers.BooleanField(default=False)
    detail_by_strategy1 = serializers.BooleanField(default=False)
    detail_by_strategy2 = serializers.BooleanField(default=False)
    detail_by_strategy3 = serializers.BooleanField(default=False)
    show_transaction_details = serializers.BooleanField(default=False)

    custom_fields = CustomFieldField(many=True, allow_empty=True, allow_null=True, required=False)

    portfolios = PortfolioField(many=True, required=False, allow_null=True, allow_empty=True)
    accounts = AccountField(many=True, required=False, allow_null=True, allow_empty=True)
    strategies1 = Strategy1Field(many=True, required=False, allow_null=True, allow_empty=True)
    strategies2 = Strategy2Field(many=True, required=False, allow_null=True, allow_empty=True)
    strategies3 = Strategy3Field(many=True, required=False, allow_null=True, allow_empty=True)
    transaction_classes = serializers.PrimaryKeyRelatedField(queryset=TransactionClass.objects.all(),
                                                             many=True, required=False, allow_null=True,
                                                             allow_empty=True)
    date_field = serializers.ChoiceField(required=False, allow_null=True,
                                         initial='transaction_date', default='transaction_date',
                                         choices=(
                                             ('transaction_date', 'transaction_date'),
                                             ('accounting_date', 'accounting_date'),
                                         ))

    items = ReportItemSerializer(many=True, read_only=True)
    summary = ReportSummarySerializer(read_only=True)

    # transactions = ReportTransactionSerializer(many=True, read_only=True)

    def __init__(self, *args, **kwargs):
        super(ReportSerializer, self).__init__(*args, **kwargs)

    def validate(self, attrs):
        if not attrs.get('report_date', None):
            attrs['report_date'] = date_now() - timedelta(days=1)

        if not attrs.get('report_currency', None):
            attrs['report_currency'] = attrs['master_user'].system_currency

        if not attrs.get('cost_method', None):
            attrs['cost_method'] = CostMethod.objects.get(pk=CostMethod.AVCO)

        return attrs

    def create(self, validated_data):
        return Report(**validated_data)


# reports

class ReportTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id']


class BaseReportItemSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True, source='pk')

    portfolio = serializers.PrimaryKeyRelatedField(read_only=True)
    account = serializers.PrimaryKeyRelatedField(read_only=True)
    strategy1 = serializers.PrimaryKeyRelatedField(read_only=True)
    strategy2 = serializers.PrimaryKeyRelatedField(read_only=True)
    strategy3 = serializers.PrimaryKeyRelatedField(read_only=True)
    instrument = serializers.PrimaryKeyRelatedField(read_only=True)
    currency = serializers.PrimaryKeyRelatedField(read_only=True)

    def __init__(self, *args, **kwargs):
        super(BaseReportItemSerializer, self).__init__(*args, **kwargs)


class BaseReportSerializer(serializers.Serializer):
    task_id = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    task_status = serializers.ReadOnlyField()

    master_user = MasterUserField()

    pricing_policy = PricingPolicyField()
    report_date = serializers.DateField(required=False, allow_null=True, default=date_now)
    report_currency = CurrencyField(required=False, allow_null=True, default=SystemCurrencyDefault())
    cost_method = serializers.PrimaryKeyRelatedField(queryset=CostMethod.objects, allow_null=True, allow_empty=True)

    detail_by_portfolio = serializers.BooleanField(default=False)
    detail_by_account = serializers.BooleanField(default=False)
    detail_by_strategy1 = serializers.BooleanField(default=False)
    detail_by_strategy2 = serializers.BooleanField(default=False)
    detail_by_strategy3 = serializers.BooleanField(default=False)
    show_transaction_details = serializers.BooleanField(default=False)

    custom_fields = CustomFieldField(many=True, allow_empty=True, allow_null=True, required=False)

    portfolios = PortfolioField(many=True, required=False, allow_null=True, allow_empty=True)
    accounts = AccountField(many=True, required=False, allow_null=True, allow_empty=True)
    strategies1 = Strategy1Field(many=True, required=False, allow_null=True, allow_empty=True)
    strategies2 = Strategy2Field(many=True, required=False, allow_null=True, allow_empty=True)
    strategies3 = Strategy3Field(many=True, required=False, allow_null=True, allow_empty=True)

    transactions = ReportTransactionSerializer(many=True, read_only=True)

    def __init__(self, *args, **kwargs):
        super(BaseReportSerializer, self).__init__(*args, **kwargs)

    def validate(self, attrs):
        if not attrs.get('report_date', None):
            attrs['report_date'] = date_now() - timedelta(days=1)

        if not attrs.get('report_currency', None):
            attrs['report_currency'] = attrs['master_user'].system_currency

        if not attrs.get('cost_method', None):
            attrs['cost_method'] = CostMethod.objects.get(pk=CostMethod.AVCO)

        return attrs


# ----------------------------------------------------------------------------------------------------------------------


class BalanceReportItemSerializer(BaseReportItemSerializer):
    # currency_name = serializers.SerializerMethodField()

    position = serializers.FloatField(read_only=True, help_text=ugettext_lazy('Position'))

    principal_value_system_ccy = serializers.FloatField(read_only=True)
    accrued_value_system_ccy = serializers.FloatField(read_only=True)
    market_value_system_ccy = serializers.FloatField(read_only=True)

    principal_value_report_ccy = serializers.FloatField(read_only=True)
    accrued_value_report_ccy = serializers.FloatField(read_only=True)
    market_value_report_ccy = serializers.FloatField(read_only=True)

    transaction = serializers.PrimaryKeyRelatedField(read_only=True,
                                                     help_text=ugettext_lazy('Transaction for case 1&2'))

    if settings.DEV:
        # currency_history = serializers.PrimaryKeyRelatedField(read_only=True, help_text=ugettext_lazy('Currency history'))
        # currency_fx_rate = serializers.FloatField(read_only=True)
        # instrument_principal_pricing_ccy = serializers.SerializerMethodField()
        # instrument_price_multiplier = serializers.FloatField(read_only=True)
        # instrument_accrued_pricing_ccy = serializers.SerializerMethodField()
        # instrument_accrued_multiplier = serializers.FloatField(read_only=True)
        # price_history = serializers.PrimaryKeyRelatedField(read_only=True)
        # instrument_principal_price = serializers.FloatField(read_only=True)
        # instrument_accrued_price = serializers.FloatField(read_only=True)
        # principal_value_instrument_principal_ccy = serializers.FloatField(read_only=True)
        # accrued_value_instrument_accrued_ccy = serializers.FloatField(read_only=True)
        # instrument_principal_currency_history = serializers.PrimaryKeyRelatedField(read_only=True)
        # instrument_principal_fx_rate = serializers.FloatField(read_only=True)
        # instrument_accrued_currency_history = serializers.PrimaryKeyRelatedField(read_only=True)
        # instrument_accrued_fx_rate = serializers.FloatField(read_only=True)
        pass

    def __init__(self, *args, **kwargs):
        super(BalanceReportItemSerializer, self).__init__(*args, **kwargs)

        # from poms.currencies.serializers import CurrencyHistorySerializer
        # self.fields['currency_history_object'] = CurrencyHistorySerializer(source='currency_history', read_only=True)

    def create(self, validated_data):
        return BalanceReportItem(**validated_data)

    def update(self, instance, validated_data):
        return instance

        # def get_currency_name(self, instance):
        #     return getattr(instance.currency, 'name', None)

        # def get_instrument_principal_pricing_ccy(self, instance):
        #     instrument = getattr(instance, 'instrument', None)
        #     pricing_currency = getattr(instrument, 'pricing_currency', None)
        #     return getattr(pricing_currency, 'name', None)

        # def get_instrument_accrued_pricing_ccy(self, instance):
        #     instrument = getattr(instance, 'instrument', None)
        #     accrued_currency = getattr(instrument, 'accrued_currency', None)
        #     return getattr(accrued_currency, 'name', None)


class BalanceReportSummarySerializer(serializers.Serializer):
    invested_value_system_ccy = serializers.FloatField(read_only=True)
    current_value_system_ccy = serializers.FloatField(read_only=True)
    p_l_system_ccy = serializers.FloatField(read_only=True)

    invested_value_report_ccy = serializers.FloatField(read_only=True)
    current_value_report_ccy = serializers.FloatField(read_only=True)
    p_l_report_ccy = serializers.FloatField(read_only=True)

    def create(self, validated_data):
        return BalanceReportSummary(**validated_data)

    def update(self, instance, validated_data):
        return instance


class BalanceReportSerializer(BaseReportSerializer):
    # custom_fields = BalanceReportCustomFieldField(many=True, allow_empty=True, allow_null=True, required=False)
    # show_transaction_details = serializers.BooleanField(default=False)

    items = BalanceReportItemSerializer(many=True, read_only=True)

    if settings.DEV:
        summary = BalanceReportSummarySerializer(read_only=True)
        invested_items = BalanceReportItemSerializer(many=True, read_only=True)

    def create(self, validated_data):
        return BalanceReport(**validated_data)

    def update(self, instance, validated_data):
        return instance


# ----------------------------------------------------------------------------------------------------------------------


# class PLReportTransactionSerializer(BaseTransactionSerializer):
#     principal_with_sign_system_ccy = serializers.FloatField(read_only=True)
#     carry_with_sign_system_ccy = serializers.FloatField(read_only=True)
#     overheads_with_sign_system_ccy = serializers.FloatField(read_only=True)
#
#     class Meta:
#         model = Transaction
#         fields = BaseTransactionSerializer.Meta.fields + [
#             'principal_with_sign_system_ccy', 'carry_with_sign_system_ccy', 'overheads_with_sign_system_ccy',
#         ]


class PLReportItemSerializer(BaseReportItemSerializer):
    principal_with_sign_system_ccy = serializers.FloatField(read_only=True)
    carry_with_sign_system_ccy = serializers.FloatField(read_only=True)
    overheads_with_sign_system_ccy = serializers.FloatField(read_only=True)
    total_system_ccy = serializers.FloatField(read_only=True)

    principal_with_sign_report_ccy = serializers.FloatField(read_only=True)
    carry_with_sign_report_ccy = serializers.FloatField(read_only=True)
    overheads_with_sign_report_ccy = serializers.FloatField(read_only=True)
    total_report_ccy = serializers.FloatField(read_only=True)

    def create(self, validated_data):
        return PLReportItem(**validated_data)

    def update(self, instance, validated_data):
        return instance


class PLReportSummarySerializer(serializers.Serializer):
    principal_with_sign_system_ccy = serializers.FloatField(read_only=True)
    carry_with_sign_system_ccy = serializers.FloatField(read_only=True)
    overheads_with_sign_system_ccy = serializers.FloatField(read_only=True)
    total_system_ccy = serializers.FloatField(read_only=True)

    principal_with_sign_report_ccy = serializers.FloatField(read_only=True)
    carry_with_sign_report_ccy = serializers.FloatField(read_only=True)
    overheads_with_sign_report_ccy = serializers.FloatField(read_only=True)
    total_report_ccy = serializers.FloatField(read_only=True)

    def create(self, validated_data):
        return PLReportSummary(**validated_data)

    def update(self, instance, validated_data):
        return instance


class PLReportSerializer(BaseReportSerializer):
    # custom_fields = CustomFieldField(many=True, allow_empty=True, allow_null=True, required=False)

    items = PLReportItemSerializer(many=True, read_only=True, help_text=ugettext_lazy('items'))

    if settings.DEV:
        summary = PLReportSummarySerializer(read_only=True)
        # transactions = PLReportTransactionSerializer(many=True, read_only=True)

    def create(self, validated_data):
        return PLReport(**validated_data)

    def update(self, instance, validated_data):
        return instance


# ----------------------------------------------------------------------------------------------------------------------


# class CostTransactionSerializer(BaseTransactionSerializer):
#     rolling_position = serializers.FloatField(read_only=True)
#     avco_multiplier = serializers.FloatField(read_only=True)
#     fifo_multiplier = serializers.FloatField(read_only=True)
#
#     remaining_position = serializers.FloatField(read_only=True)
#     remaining_position_cost_settlement_ccy = serializers.FloatField(read_only=True)
#     remaining_position_cost_system_ccy = serializers.FloatField(read_only=True)
#
#     class Meta:
#         model = Transaction
#         fields = BaseTransactionSerializer.Meta.fields + [
#             'rolling_position',
#             'avco_multiplier', 'fifo_multiplier',
#             'remaining_position', 'remaining_position_cost_settlement_ccy', 'remaining_position_cost_system_ccy',
#         ]
#
#     def get_transaction_class_code(self, instance):
#         return getattr(instance.transaction_class, 'code', None)
#
#     def get_transaction_currency_name(self, instance):
#         return getattr(instance.transaction_currency, 'name', None)
#
#     def get_instrument_name(self, instance):
#         return getattr(instance.instrument, 'name', None)
#
#     def get_settlement_currency_name(self, instance):
#         return getattr(instance.settlement_currency, 'name', None)


class CostReportInstrumentSerializer(BaseReportItemSerializer):
    pricing_currency_name = serializers.SerializerMethodField(read_only=True)
    pricing_currency_fx_rate = serializers.SerializerMethodField()
    price_multiplier = serializers.SerializerMethodField()
    position = serializers.FloatField(read_only=True)
    cost_system_ccy = serializers.FloatField(read_only=True)
    cost_instrument_ccy = serializers.FloatField(read_only=True)
    cost_price = serializers.FloatField(read_only=True)
    cost_price_adjusted = serializers.FloatField(read_only=True)

    def create(self, validated_data):
        return PLReportItem(**validated_data)

    def update(self, instance, validated_data):
        return instance

    def get_pricing_currency_name(self, instance):
        pricing_currency = getattr(instance.instrument, 'pricing_currency', None)
        return getattr(pricing_currency, 'name', None)

    def get_pricing_currency_fx_rate(self, instance):
        pricing_currency_fx_rate = getattr(instance.instrument, 'pricing_currency_fx_rate', None)
        return pricing_currency_fx_rate

    def get_price_multiplier(self, instance):
        return getattr(instance.instrument, 'price_multiplier', None)


class CostReportSerializer(BaseReportSerializer):
    items = CostReportInstrumentSerializer(many=True, read_only=True)

    # if settings.DEV:
    #     transactions = CostTransactionSerializer(many=True, read_only=True)

    def create(self, validated_data):
        return CostReport(**validated_data)

    def update(self, instance, validated_data):
        return instance


# ----------------------------------------------------------------------------------------------------------------------


# class YTMTransactionSerializer(BaseTransactionSerializer):
#     rolling_position = serializers.FloatField(read_only=True)
#     avco_multiplier = serializers.FloatField(read_only=True)
#     fifo_multiplier = serializers.FloatField(read_only=True)
#
#     ytm = serializers.FloatField(read_only=True)
#     time_invested = serializers.FloatField(read_only=True)
#     remaining_position = serializers.FloatField(read_only=True)
#     remaining_position_percent = serializers.FloatField(read_only=True)
#     weighted_ytm = serializers.FloatField(read_only=True)
#     weighted_time_invested = serializers.FloatField(read_only=True)
#
#     class Meta:
#         model = Transaction
#         fields = BaseTransactionSerializer.Meta.fields + [
#             'rolling_position',
#             'avco_multiplier', 'fifo_multiplier',
#             'ytm', 'time_invested',
#             'remaining_position', 'remaining_position_percent',
#             'weighted_ytm', 'weighted_time_invested',
#         ]
#
#     def get_transaction_class_code(self, instance):
#         return getattr(instance.transaction_class, 'code', None)
#
#     def get_transaction_currency_name(self, instance):
#         return getattr(instance.transaction_currency, 'name', None)
#
#     def get_instrument_name(self, instance):
#         return getattr(instance.instrument, 'name', None)
#
#     def get_settlement_currency_name(self, instance):
#         return getattr(instance.settlement_currency, 'name', None)


class YTMReportInstrumentSerializer(BaseReportItemSerializer):
    position = serializers.FloatField(read_only=True)
    ytm = serializers.FloatField(read_only=True)
    time_invested = serializers.FloatField(read_only=True)

    def create(self, validated_data):
        return PLReportItem(**validated_data)

    def update(self, instance, validated_data):
        return instance


class YTMReportSerializer(BaseReportSerializer):
    items = YTMReportInstrumentSerializer(many=True, read_only=True)

    # if settings.DEV:
    #     transactions = YTMTransactionSerializer(many=True, read_only=True)

    def create(self, validated_data):
        return CostReport(**validated_data)

    def update(self, instance, validated_data):
        return instance


# ----------------------------------------------------------------------------------------------------------------------


class SimpleMultipliersReportItemSerializer(BaseReportItemSerializer):
    instrument = serializers.PrimaryKeyRelatedField(read_only=True)
    position_size_with_sign = serializers.FloatField(read_only=True)
    avco_multiplier = serializers.FloatField(read_only=True)
    fifo_multiplier = serializers.FloatField(read_only=True)
    rolling_position = serializers.FloatField(read_only=True)

    def create(self, validated_data):
        return None

    def update(self, instance, validated_data):
        return instance

    def get_currency_name(self, instance):
        return instance.currency.name if instance.currency else None

    def get_instrument_name(self, instance):
        return instance.instrument.name if instance.instrument else None


class SimpleMultipliersReportSerializer(BaseReportSerializer):
    results = SimpleMultipliersReportItemSerializer(many=True, read_only=True,
                                                    help_text=ugettext_lazy('some help text'))

    def create(self, validated_data):
        return BalanceReport(**validated_data)

    def update(self, instance, validated_data):
        return instance


# class SimpleMultipliersReport2TransactionSerializer(BaseTransactionSerializer):
#     rolling_position = serializers.FloatField(read_only=True)
#     avco_multiplier = serializers.FloatField(read_only=True)
#     fifo_multiplier = serializers.FloatField(read_only=True)
#
#     class Meta:
#         model = Transaction
#         fields = BaseTransactionSerializer.Meta.fields + [
#             'rolling_position', 'avco_multiplier', 'fifo_multiplier',
#         ]


class SimpleMultipliersReport2Serializer(BaseReportSerializer):
    # transactions = SimpleMultipliersReport2TransactionSerializer(many=True, read_only=True)

    def create(self, validated_data):
        return BaseReport(**validated_data)

    def update(self, instance, validated_data):
        return instance
