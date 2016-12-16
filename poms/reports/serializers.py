from __future__ import unicode_literals

from datetime import timedelta

from django.utils.translation import ugettext_lazy
from rest_framework import serializers

from poms.accounts.fields import AccountField
from poms.accounts.serializers import AccountSerializer, AccountViewSerializer
from poms.common.fields import ExpressionField
from poms.common.utils import date_now
from poms.currencies.fields import CurrencyField, SystemCurrencyDefault
from poms.currencies.serializers import CurrencySerializer, CurrencyViewSerializer
from poms.instruments.fields import PricingPolicyField
from poms.instruments.models import CostMethod
from poms.instruments.serializers import InstrumentSerializer, PricingPolicyViewSerializer, CostMethodSerializer
from poms.portfolios.fields import PortfolioField
from poms.portfolios.serializers import PortfolioSerializer, PortfolioViewSerializer
from poms.reports.builders import Report, ReportItem
from poms.reports.cash_flow_projection import CashFlowProjectionReport
from poms.reports.fields import CustomFieldField
from poms.reports.models import CustomField
from poms.strategies.fields import Strategy1Field, Strategy2Field, Strategy3Field
from poms.strategies.serializers import Strategy1Serializer, Strategy2Serializer, Strategy3Serializer, \
    Strategy1ViewSerializer, Strategy2ViewSerializer, Strategy3ViewSerializer
from poms.transactions.models import TransactionClass
from poms.transactions.serializers import TransactionClassSerializer, TransactionSerializer, \
    ComplexTransactionSerializer
from poms.users.fields import MasterUserField, HiddenMemberField


class CustomFieldSerializer(serializers.ModelSerializer):
    master_user = MasterUserField()
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


# Report --------


class ReportInstrumentSerializer(InstrumentSerializer):
    def __init__(self, *args, **kwargs):
        super(ReportInstrumentSerializer, self).__init__(*args, **kwargs)

        self.fields.pop('manual_pricing_formulas')
        self.fields.pop('accrual_calculation_schedules')
        self.fields.pop('factor_schedules')
        self.fields.pop('event_schedules')

        self.fields.pop('user_object_permissions')
        self.fields.pop('group_object_permissions')
        self.fields.pop('object_permissions')


class ReportCurrencySerializer(CurrencySerializer):
    def __init__(self, *args, **kwargs):
        super(CurrencySerializer, self).__init__(*args, **kwargs)


class ReportPortfolioSerializer(PortfolioSerializer):
    def __init__(self, *args, **kwargs):
        super(PortfolioSerializer, self).__init__(*args, **kwargs)
        self.fields.pop('accounts', None)
        self.fields.pop('accounts_object', None)
        self.fields.pop('responsibles', None)
        self.fields.pop('responsibles_object', None)
        self.fields.pop('counterparties', None)
        self.fields.pop('counterparties_object', None)
        self.fields.pop('transaction_types', None)
        self.fields.pop('transaction_types_object', None)

        self.fields.pop('user_object_permissions', None)
        self.fields.pop('group_object_permissions', None)
        self.fields.pop('object_permissions', None)


class ReportAccountSerializer(AccountSerializer):
    def __init__(self, *args, **kwargs):
        super(AccountSerializer, self).__init__(*args, **kwargs)
        self.fields.pop('portfolios', None)
        self.fields.pop('portfolios_object', None)

        self.fields.pop('user_object_permissions', None)
        self.fields.pop('group_object_permissions', None)
        self.fields.pop('object_permissions', None)


class ReportStrategy1Serializer(Strategy1Serializer):
    def __init__(self, *args, **kwargs):
        super(Strategy1Serializer, self).__init__(*args, **kwargs)

        self.fields.pop('user_object_permissions')
        self.fields.pop('group_object_permissions')
        self.fields.pop('object_permissions')


class ReportStrategy2Serializer(Strategy2Serializer):
    def __init__(self, *args, **kwargs):
        super(Strategy2Serializer, self).__init__(*args, **kwargs)

        self.fields.pop('user_object_permissions')
        self.fields.pop('group_object_permissions')
        self.fields.pop('object_permissions')


class ReportStrategy3Serializer(Strategy3Serializer):
    def __init__(self, *args, **kwargs):
        super(Strategy3Serializer, self).__init__(*args, **kwargs)

        self.fields.pop('user_object_permissions')
        self.fields.pop('group_object_permissions')
        self.fields.pop('object_permissions')


class ReportItemCustomFieldSerializer(serializers.Serializer):
    custom_field = serializers.PrimaryKeyRelatedField(read_only=True)
    value = serializers.ReadOnlyField()

    def __init__(self, *args, **kwargs):
        super(ReportItemCustomFieldSerializer, self).__init__(*args, **kwargs)

        self.fields['custom_field_object'] = CustomFieldViewSerializer(source='custom_field', read_only=True)


class ReportItemSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)

    item_type = serializers.ChoiceField(source='type', choices=ReportItem.TYPE_CHOICES, read_only=True)
    item_type_code = serializers.ReadOnlyField(source='type_code')
    item_type_name = serializers.ReadOnlyField(source='type_name')

    user_code = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField()
    short_name = serializers.ReadOnlyField()
    detail = serializers.CharField(read_only=True)

    instrument = serializers.PrimaryKeyRelatedField(source='instr', read_only=True)
    currency = serializers.PrimaryKeyRelatedField(source='ccy', read_only=True)
    transaction_currency = serializers.PrimaryKeyRelatedField(source='trn_ccy', read_only=True)
    portfolio = serializers.PrimaryKeyRelatedField(source='prtfl', read_only=True)
    account = serializers.PrimaryKeyRelatedField(source='acc', read_only=True)
    strategy1 = serializers.PrimaryKeyRelatedField(source='str1', read_only=True)
    strategy2 = serializers.PrimaryKeyRelatedField(source='str2', read_only=True)
    strategy3 = serializers.PrimaryKeyRelatedField(source='str3', read_only=True)
    custom_fields = ReportItemCustomFieldSerializer(many=True, read_only=True)

    # allocations

    allocation_balance = serializers.PrimaryKeyRelatedField(source='alloc_bl', read_only=True)
    allocation_pl = serializers.PrimaryKeyRelatedField(source='alloc_pl', read_only=True)

    # mismatches

    mismatch = serializers.FloatField(read_only=True)
    mismatch_portfolio = serializers.PrimaryKeyRelatedField(source='mismatch_prtfl', read_only=True)
    mismatch_account = serializers.PrimaryKeyRelatedField(source='mismatch_acc', read_only=True)
    # mismatch_currency = serializers.PrimaryKeyRelatedField(source='mismatch_ccy', read_only=True)

    # balance

    position_size = serializers.FloatField(source='pos_size', read_only=True)
    market_value = serializers.FloatField(source='market_value_res', read_only=True)
    cost = serializers.FloatField(source='cost_res', read_only=True)

    instr_principal = serializers.FloatField(source='instr_principal_res', read_only=True)
    instr_accrued = serializers.FloatField(source='instr_accrued_res', read_only=True)
    exposure = serializers.FloatField(source='exposure_res', read_only=True)

    # full ----------------------------------------------------
    principal = serializers.FloatField(source='principal_res', read_only=True)
    carry = serializers.FloatField(source='carry_res', read_only=True)
    overheads = serializers.FloatField(source='overheads_res', read_only=True)
    total = serializers.FloatField(source='total_res', read_only=True)

    # full / closed ----------------------------------------------------
    principal_closed = serializers.FloatField(source='principal_closed_res', read_only=True)
    carry_closed = serializers.FloatField(source='carry_closed_res', read_only=True)
    overheads_closed = serializers.FloatField(source='overheads_closed_res', read_only=True)
    total_closed = serializers.FloatField(source='total_closed_res', read_only=True)

    # full / opened ----------------------------------------------------
    principal_opened = serializers.FloatField(source='principal_opened_res', read_only=True)
    carry_opened = serializers.FloatField(source='carry_opened_res', read_only=True)
    overheads_opened = serializers.FloatField(source='overheads_opened_res', read_only=True)
    total_opened = serializers.FloatField(source='total_opened_res', read_only=True)

    # fx ----------------------------------------------------
    principal_fx = serializers.FloatField(source='principal_fx_res', read_only=True)
    carry_fx = serializers.FloatField(source='carry_fx_res', read_only=True)
    overheads_fx = serializers.FloatField(source='overheads_fx_res', read_only=True)
    total_fx = serializers.FloatField(source='total_fx_res', read_only=True)

    # fx / closed ----------------------------------------------------
    principal_fx_closed = serializers.FloatField(source='principal_fx_closed_res', read_only=True)
    carry_fx_closed = serializers.FloatField(source='carry_fx_closed_res', read_only=True)
    overheads_fx_closed = serializers.FloatField(source='overheads_fx_closed_res', read_only=True)
    total_fx_closed = serializers.FloatField(source='total_fx_closed_res', read_only=True)

    # fx / opened ----------------------------------------------------
    principal_fx_opened = serializers.FloatField(source='principal_fx_opened_res', read_only=True)
    carry_fx_opened = serializers.FloatField(source='carry_fx_opened_res', read_only=True)
    overheads_fx_opened = serializers.FloatField(source='overheads_fx_opened_res', read_only=True)
    total_fx_opened = serializers.FloatField(source='total_fx_opened_res', read_only=True)

    # fixed ----------------------------------------------------
    principal_fixed = serializers.FloatField(source='principal_fixed_res', read_only=True)
    carry_fixed = serializers.FloatField(source='carry_fixed_res', read_only=True)
    overheads_fixed = serializers.FloatField(source='overheads_fixed_res', read_only=True)
    total_fixed = serializers.FloatField(source='total_fixed_res', read_only=True)

    # fixed / closed ----------------------------------------------------
    principal_fixed_closed = serializers.FloatField(source='principal_fixed_closed_res', read_only=True)
    carry_fixed_closed = serializers.FloatField(source='carry_fixed_closed_res', read_only=True)
    overheads_fixed_closed = serializers.FloatField(source='overheads_fixed_closed_res', read_only=True)
    total_fixed_closed = serializers.FloatField(source='total_fixed_closed_res', read_only=True)

    # fixed / opened ----------------------------------------------------
    principal_fixed_opened = serializers.FloatField(source='principal_fixed_opened_res', read_only=True)
    carry_fixed_opened = serializers.FloatField(source='carry_fixed_opened_res', read_only=True)
    overheads_fixed_opened = serializers.FloatField(source='overheads_fixed_opened_res', read_only=True)
    total_fixed_opened = serializers.FloatField(source='total_fixed_opened_res', read_only=True)

    def __init__(self, *args, **kwargs):
        super(ReportItemSerializer, self).__init__(*args, **kwargs)

        # from poms.currencies.serializers import CurrencySerializer
        # from poms.instruments.serializers import InstrumentSerializer
        # from poms.portfolios.serializers import PortfolioViewSerializer
        # from poms.accounts.serializers import AccountViewSerializer
        # from poms.strategies.serializers import Strategy1ViewSerializer, Strategy2ViewSerializer, \
        #     Strategy3ViewSerializer

        self.fields['portfolio_object'] = ReportPortfolioSerializer(source='prtfl', read_only=True)
        self.fields['account_object'] = ReportAccountSerializer(source='acc', read_only=True)
        self.fields['strategy1_object'] = ReportStrategy1Serializer(source='str1', read_only=True)
        self.fields['strategy2_object'] = ReportStrategy2Serializer(source='str2', read_only=True)
        self.fields['strategy3_object'] = ReportStrategy3Serializer(source='str3', read_only=True)
        self.fields['instrument_object'] = ReportInstrumentSerializer(source='instr', read_only=True)
        self.fields['currency_object'] = ReportCurrencySerializer(source='ccy', read_only=True)
        self.fields['transaction_currency_object'] = ReportCurrencySerializer(source='trn_ccy', read_only=True)

        self.fields['allocation_balance_object'] = ReportInstrumentSerializer(source='alloc_bl', read_only=True)
        self.fields['allocation_pl_object'] = ReportInstrumentSerializer(source='alloc_pl', read_only=True)

        self.fields['mismatch_portfolio_object'] = ReportPortfolioSerializer(source='mismatch_prtfl', read_only=True)
        self.fields['mismatch_account_object'] = ReportAccountSerializer(source='mismatch_acc', read_only=True)
        # self.fields['mismatch_currency_object'] = ReportCurrencySerializer(source='mismatch_ccy', read_only=True)


class ReportSerializer(serializers.Serializer):
    task_id = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    task_status = serializers.ReadOnlyField()

    master_user = MasterUserField()
    member = HiddenMemberField()
    pricing_policy = PricingPolicyField()
    report_date = serializers.DateField(required=False, allow_null=True, default=date_now)
    report_currency = CurrencyField(required=False, allow_null=True, default=SystemCurrencyDefault())
    cost_method = serializers.PrimaryKeyRelatedField(queryset=CostMethod.objects, allow_null=True, allow_empty=True)

    portfolio_mode = serializers.ChoiceField(default=Report.MODE_INDEPENDENT, initial=Report.MODE_INDEPENDENT,
                                             choices=Report.MODE_CHOICES)
    account_mode = serializers.ChoiceField(default=Report.MODE_INDEPENDENT, initial=Report.MODE_INDEPENDENT,
                                           choices=Report.MODE_CHOICES)
    strategy1_mode = serializers.ChoiceField(default=Report.MODE_INDEPENDENT, initial=Report.MODE_INDEPENDENT,
                                             choices=Report.MODE_CHOICES)
    strategy2_mode = serializers.ChoiceField(default=Report.MODE_INDEPENDENT, initial=Report.MODE_INDEPENDENT,
                                             choices=Report.MODE_CHOICES)
    strategy3_mode = serializers.ChoiceField(default=Report.MODE_INDEPENDENT, initial=Report.MODE_INDEPENDENT,
                                             choices=Report.MODE_CHOICES)
    show_transaction_details = serializers.BooleanField(default=False)
    approach_multiplier = serializers.FloatField(default=0.5, initial=0.5, min_value=0.0, max_value=1.0)

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
                                             ('transaction_date', ugettext_lazy('Transaction date')),
                                             ('accounting_date', ugettext_lazy('Accounting date')),
                                             ('cash_date', ugettext_lazy('Cash date')),
                                         ))

    items = ReportItemSerializer(many=True, read_only=True)

    # transactions = ReportTransactionSerializer(many=True, read_only=True)

    def __init__(self, *args, **kwargs):
        super(ReportSerializer, self).__init__(*args, **kwargs)

        self.fields['pricing_policy_object'] = PricingPolicyViewSerializer(source='pricing_policy', read_only=True)
        self.fields['report_currency_object'] = CurrencyViewSerializer(source='report_currency', read_only=True)
        self.fields['cost_method_object'] = CostMethodSerializer(source='cost_method', read_only=True)
        self.fields['portfolios_object'] = PortfolioViewSerializer(source='portfolios', read_only=True, many=True)
        self.fields['accounts_object'] = AccountViewSerializer(source='accounts', read_only=True, many=True)
        self.fields['strategies1_object'] = Strategy1ViewSerializer(source='strategies1', read_only=True, many=True)
        self.fields['strategies2_object'] = Strategy2ViewSerializer(source='strategies2', read_only=True, many=True)
        self.fields['strategies3_object'] = Strategy3ViewSerializer(source='strategies3', read_only=True, many=True)
        self.fields['custom_fields_object'] = CustomFieldViewSerializer(source='custom_fields', read_only=True,
                                                                        many=True)
        self.fields['transaction_classes_object'] = TransactionClassSerializer(source='transaction_classes',
                                                                               read_only=True, many=True)

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


# Transaction Report --------


class ComplexTransactionReportSerializer(ComplexTransactionSerializer):
    def __init__(self, *args, **kwargs):
        super(ComplexTransactionReportSerializer, self).__init__(*args, **kwargs)

        # self.fields.pop('transactions')
        self.fields.pop('transactions_object')
        # self.fields.pop('text')


class TransactionReportTransactionSerializer(TransactionSerializer):
    def __init__(self, *args, **kwargs):
        super(TransactionReportTransactionSerializer, self).__init__(*args, **kwargs)

        # self.fields.pop('complex_transaction_object')

        self.fields['complex_transaction_object'] = ComplexTransactionReportSerializer(source='complex_transaction',
                                                                                       read_only=True)


class TransactionReport:
    def __init__(self, id=None, task_id=None, task_status=None, master_user=None, member=None, transactions=None):
        self.id = id
        self.task_id = task_id
        self.task_status = task_status
        self.master_user = master_user
        self.member = member
        self.transactions = transactions


class TransactionReportSerializer(serializers.Serializer):
    task_id = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    task_status = serializers.ReadOnlyField()

    master_user = MasterUserField()
    member = HiddenMemberField()

    transactions = TransactionReportTransactionSerializer(many=True, read_only=True)

    def create(self, validated_data):
        return TransactionReport(**validated_data)


# Cash flow projection Report --------


class CashFlowProjectionReportSerializer(serializers.Serializer):
    task_id = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    task_status = serializers.ReadOnlyField()

    master_user = MasterUserField()
    member = HiddenMemberField()

    def create(self, validated_data):
        return CashFlowProjectionReport(**validated_data)

