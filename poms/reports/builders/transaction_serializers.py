from __future__ import unicode_literals

from rest_framework import serializers

from poms.reports.builders.base_serializers import ReportItemCustomFieldSerializer, ReportPortfolioSerializer, \
    ReportAccountSerializer, ReportStrategy1Serializer, ReportStrategy2Serializer, ReportStrategy3Serializer, \
    ReportInstrumentSerializer, ReportCurrencySerializer, CustomFieldViewSerializer, ReportGenericAttributeSerializer, \
    ReportComplexTransactionSerializer, ReportResponsibleSerializer, ReportCounterpartySerializer, \
    ReportGenericAttributeTypeSerializer
from poms.reports.builders.transaction_item import TransactionReport
from poms.reports.fields import CustomFieldField
from poms.transactions.serializers import TransactionTypeViewSerializer
from poms.users.fields import MasterUserField, HiddenMemberField


class TransactionReportItemSerializer(serializers.Serializer):
    id = serializers.ReadOnlyField()
    # complex_transaction = ReportComplexTransactionSerializer(read_only=True)
    complex_transaction = serializers.PrimaryKeyRelatedField(read_only=True)
    transaction_code = serializers.ReadOnlyField()
    transaction_class = serializers.PrimaryKeyRelatedField(read_only=True)
    instrument = serializers.PrimaryKeyRelatedField(read_only=True)
    transaction_currency = serializers.PrimaryKeyRelatedField(read_only=True)
    position_size_with_sign = serializers.ReadOnlyField()
    settlement_currency = serializers.PrimaryKeyRelatedField(read_only=True)
    cash_consideration = serializers.ReadOnlyField()
    principal_with_sign = serializers.ReadOnlyField()
    carry_with_sign = serializers.ReadOnlyField()
    overheads_with_sign = serializers.ReadOnlyField()
    accounting_date = serializers.DateField(read_only=True)
    cash_date = serializers.DateField(read_only=True)
    transaction_date = serializers.DateField(read_only=True)
    portfolio = serializers.PrimaryKeyRelatedField(read_only=True)
    account_cash = serializers.PrimaryKeyRelatedField(read_only=True)
    account_position = serializers.PrimaryKeyRelatedField(read_only=True)
    account_interim = serializers.PrimaryKeyRelatedField(read_only=True)
    strategy1_position = serializers.PrimaryKeyRelatedField(read_only=True)
    strategy1_cash = serializers.PrimaryKeyRelatedField(read_only=True)
    strategy2_position = serializers.PrimaryKeyRelatedField(read_only=True)
    strategy2_cash = serializers.PrimaryKeyRelatedField(read_only=True)
    strategy3_position = serializers.PrimaryKeyRelatedField(read_only=True)
    strategy3_cash = serializers.PrimaryKeyRelatedField(read_only=True)
    responsible = serializers.PrimaryKeyRelatedField(read_only=True)
    counterparty = serializers.PrimaryKeyRelatedField(read_only=True)
    linked_instrument = serializers.PrimaryKeyRelatedField(read_only=True)
    allocation_balance = serializers.PrimaryKeyRelatedField(read_only=True)
    allocation_pl = serializers.PrimaryKeyRelatedField(read_only=True)
    reference_fx_rate = serializers.ReadOnlyField()
    factor = serializers.ReadOnlyField()
    trade_price = serializers.ReadOnlyField()
    position_amount = serializers.ReadOnlyField()
    principal_amount = serializers.ReadOnlyField()
    carry_amount = serializers.ReadOnlyField()
    overheads = serializers.ReadOnlyField()
    notes = serializers.ReadOnlyField()
    attributes = ReportGenericAttributeSerializer(many=True, read_only=True)

    custom_fields = ReportItemCustomFieldSerializer(many=True, read_only=True)

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('read_only', True)

        super(TransactionReportItemSerializer, self).__init__(*args, **kwargs)


class TransactionReportSerializer(serializers.Serializer):
    task_id = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    task_status = serializers.ReadOnlyField()

    master_user = MasterUserField()
    member = HiddenMemberField()

    begin_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)

    custom_fields = CustomFieldField(many=True, allow_empty=True, allow_null=True, required=False)

    items = TransactionReportItemSerializer(many=True, read_only=True)

    item_complex_transactions = ReportComplexTransactionSerializer(source='complex_transactions', many=True, read_only=True)
    item_transaction_types = TransactionTypeViewSerializer(source='transaction_types', many=True, read_only=True)
    item_instruments = ReportInstrumentSerializer(source='instruments', many=True, read_only=True)
    item_currencies = ReportCurrencySerializer(source='currencies', many=True, read_only=True)
    item_portfolios = ReportPortfolioSerializer(source='portfolios', many=True, read_only=True)
    item_accounts = ReportAccountSerializer(source='accounts', many=True, read_only=True)
    item_strategies1 = ReportStrategy1Serializer(source='strategies1', many=True, read_only=True)
    item_strategies2 = ReportStrategy2Serializer(source='strategies2', many=True, read_only=True)
    item_strategies3 = ReportStrategy3Serializer(source='strategies3', many=True, read_only=True)
    item_responsibles = ReportResponsibleSerializer(source='responsibles', many=True, read_only=True)
    item_counterparties = ReportCounterpartySerializer(source='counterparties', many=True, read_only=True)
    # item_complex_transaction_attribute_types = ReportGenericAttributeTypeSerializer(source='complex_transaction_attribute_types', many=True, read_only=True, show_classifiers=True)
    # item_transaction_attribute_types = ReportGenericAttributeTypeSerializer(source='transaction_attribute_types', many=True, read_only=True, show_classifiers=True)
    # item_instrument_attribute_types = ReportGenericAttributeTypeSerializer(source='instrument_attribute_types', many=True, read_only=True, show_classifiers=True)
    # item_currency_attribute_types = ReportGenericAttributeTypeSerializer(source='currency_attribute_types', many=True, read_only=True, show_classifiers=True)
    # item_portfolio_attribute_types = ReportGenericAttributeTypeSerializer(source='portfolio_attribute_types', many=True, read_only=True, show_classifiers=True)
    # item_account_attribute_types = ReportGenericAttributeTypeSerializer(source='account_attribute_types', many=True, read_only=True, show_classifiers=True)
    # item_responsible_attribute_types = ReportGenericAttributeTypeSerializer(source='responsible_attribute_types', many=True, read_only=True, show_classifiers=True)
    # item_counterparty_attribute_types = ReportGenericAttributeTypeSerializer(source='counterparty_attribute_types', many=True, read_only=True, show_classifiers=True)

    # TODO: deprecated names
    # complex_transactions = ReportComplexTransactionSerializer(many=True, read_only=True)
    # transaction_types = TransactionTypeViewSerializer(many=True, read_only=True)
    # instruments = ReportInstrumentSerializer(many=True, read_only=True)
    # currencies = ReportCurrencySerializer(many=True, read_only=True)
    # portfolios = ReportPortfolioSerializer(many=True, read_only=True)
    # accounts = ReportAccountSerializer(many=True, read_only=True)
    # strategies1 = ReportStrategy1Serializer(many=True, read_only=True)
    # strategies2 = ReportStrategy2Serializer(many=True, read_only=True)
    # strategies3 = ReportStrategy3Serializer(many=True, read_only=True)
    # responsibles = ReportResponsibleSerializer(many=True, read_only=True)
    # counterparties = ReportCounterpartySerializer(many=True, read_only=True)
    # complex_transaction_attribute_types = ReportGenericAttributeTypeSerializer(many=True, read_only=True,  show_classifiers=True)
    # transaction_attribute_types = ReportGenericAttributeTypeSerializer(many=True, read_only=True, show_classifiers=True)
    # instrument_attribute_types = ReportGenericAttributeTypeSerializer(many=True, read_only=True, show_classifiers=True)
    # currency_attribute_types = ReportGenericAttributeTypeSerializer(many=True, read_only=True, show_classifiers=True)
    # portfolio_attribute_types = ReportGenericAttributeTypeSerializer(many=True, read_only=True, show_classifiers=True)
    # account_attribute_types = ReportGenericAttributeTypeSerializer(many=True, read_only=True, show_classifiers=True)
    # responsible_attribute_types = ReportGenericAttributeTypeSerializer(many=True, read_only=True, show_classifiers=True)
    # counterparty_attribute_types = ReportGenericAttributeTypeSerializer(many=True, read_only=True, show_classifiers=True)

    def __init__(self, *args, **kwargs):
        super(TransactionReportSerializer, self).__init__(*args, **kwargs)

        self.fields['custom_fields_object'] = CustomFieldViewSerializer(source='custom_fields', read_only=True,
                                                                        many=True)

    def create(self, validated_data):
        return TransactionReport(**validated_data)
