from __future__ import unicode_literals

from rest_framework import serializers

from poms.accounts.fields import AccountField
from poms.common.serializers import PomsClassSerializer
from poms.counterparties.fields import ResponsibleField, CounterpartyField
from poms.currencies.fields import CurrencyField
from poms.instruments.fields import InstrumentField
from poms.obj_attrs.serializers import AttributeTypeSerializerBase, AttributeSerializerBase, \
    ModelWithAttributesSerializer
from poms.portfolios.fields import PortfolioField
from poms.strategies.fields import StrategyRootField
from poms.transactions.fields import TransactionAttributeTypeField
from poms.transactions.models import TransactionClass, Transaction, TransactionType, TransactionAttributeType, \
    TransactionAttribute
from poms.users.fields import MasterUserField


class TransactionClassSerializer(PomsClassSerializer):
    class Meta(PomsClassSerializer.Meta):
        model = TransactionClass


class TransactionTypeSerializer(serializers.ModelSerializer):
    master_user = MasterUserField()

    class Meta:
        model = TransactionType
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes']


class TransactionAttributeTypeSerializer(AttributeTypeSerializerBase):
    strategy_position_root = StrategyRootField(required=False, allow_null=True)
    strategy_cash_root = StrategyRootField(required=False, allow_null=True)

    class Meta(AttributeTypeSerializerBase.Meta):
        model = TransactionAttributeType
        fields = AttributeTypeSerializerBase.Meta.fields + ['strategy_position_root', 'strategy_cash_root']
        update_read_only_fields = AttributeTypeSerializerBase.Meta.update_read_only_fields + \
                                  ['strategy_position_root', 'strategy_cash_root']


class TransactionAttributeSerializer(AttributeSerializerBase):
    attribute_type = TransactionAttributeTypeField()
    strategy_position = StrategyRootField(required=False, allow_null=True)
    strategy_cash = StrategyRootField(required=False, allow_null=True)

    class Meta(AttributeSerializerBase.Meta):
        model = TransactionAttribute
        fields = AttributeSerializerBase.Meta.fields + ['attribute_type', 'strategy_position', 'strategy_cash']


class TransactionSerializer(ModelWithAttributesSerializer):
    master_user = MasterUserField()
    portfolio = PortfolioField(required=False, allow_null=True)
    transaction_currency = CurrencyField(required=False, allow_null=True)
    instrument = InstrumentField(required=False, allow_null=True)
    settlement_currency = CurrencyField(required=False, allow_null=True)
    account_cash = AccountField(required=False, allow_null=True)
    account_position = AccountField(required=False, allow_null=True)
    account_interim = AccountField(required=False, allow_null=True)
    responsible = ResponsibleField(required=False, allow_null=True)
    counterparty = CounterpartyField(required=False, allow_null=True)
    attributes = TransactionAttributeSerializer(many=True)

    class Meta:
        model = Transaction
        fields = ['url', 'id', 'master_user',
                  'portfolio', 'transaction_class',
                  'transaction_currency', 'instrument',
                  'position_size_with_sign',
                  'settlement_currency', 'cash_consideration',
                  'principal_with_sign', 'carry_with_sign', 'overheads_with_sign',
                  'accounting_date', 'cash_date', 'transaction_date',
                  'account_cash', 'account_position', 'account_interim',
                  'reference_fx_rate',
                  'is_locked', 'is_canceled',
                  'factor', 'trade_price',
                  'principal_amount', 'carry_amount', 'overheads',
                  'responsible', 'counterparty',
                  'attributes']
