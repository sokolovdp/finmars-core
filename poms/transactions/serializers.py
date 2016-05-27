from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from poms.accounts.fields import AccountField
from poms.common.serializers import PomsClassSerializer
from poms.counterparties.fields import ResponsibleField, CounterpartyField
from poms.currencies.fields import CurrencyField
from poms.instruments.fields import InstrumentField
from poms.obj_attrs.models import AttributeTypeBase
from poms.obj_attrs.serializers import AttributeTypeSerializerBase, AttributeSerializerBase, \
    ModelWithAttributesSerializer
from poms.obj_perms.serializers import ModelWithObjectPermissionSerializer
from poms.portfolios.fields import PortfolioField
from poms.strategies.fields import Strategy1Field, Strategy2Field, Strategy3Field
from poms.tags.fields import TagField
from poms.transactions.fields import TransactionAttributeTypeField
from poms.transactions.models import TransactionClass, Transaction, TransactionType, TransactionAttributeType, \
    TransactionAttribute
from poms.users.fields import MasterUserField


class TransactionClassSerializer(PomsClassSerializer):
    class Meta(PomsClassSerializer.Meta):
        model = TransactionClass


class TransactionTypeSerializer(serializers.ModelSerializer):
    master_user = MasterUserField()
    tags = TagField(many=True)

    class Meta:
        model = TransactionType
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes', 'tags']


class TransactionAttributeTypeSerializer(AttributeTypeSerializerBase, ModelWithObjectPermissionSerializer):
    # strategy_position_root = StrategyRootField(required=False, allow_null=True)
    # strategy_cash_root = StrategyRootField(required=False, allow_null=True)

    class Meta(AttributeTypeSerializerBase.Meta):
        model = TransactionAttributeType
        # fields = AttributeTypeSerializerBase.Meta.fields + ['strategy_position_root', 'strategy_cash_root']
        # update_read_only_fields = AttributeTypeSerializerBase.Meta.update_read_only_fields + \
        #                           ['strategy_position_root', 'strategy_cash_root']

    def validate_value_type(self, value_type):
        if value_type == AttributeTypeBase.CLASSIFIER:
            raise ValidationError({'value_type': _('Value type classifier is unsupported')})
        return value_type


class TransactionAttributeSerializer(AttributeSerializerBase):
    attribute_type = TransactionAttributeTypeField()

    # strategy_position = StrategyRootField(required=False, allow_null=True)
    # strategy_cash = StrategyRootField(required=False, allow_null=True)

    class Meta(AttributeSerializerBase.Meta):
        model = TransactionAttribute
        fields = AttributeSerializerBase.Meta.fields + ['attribute_type']


class TransactionSerializer(ModelWithAttributesSerializer):
    master_user = MasterUserField()
    portfolio = PortfolioField(required=False, allow_null=True)
    transaction_currency = CurrencyField(required=False, allow_null=True)
    instrument = InstrumentField(required=False, allow_null=True)
    settlement_currency = CurrencyField(required=False, allow_null=True)
    account_cash = AccountField(required=False, allow_null=True)
    account_position = AccountField(required=False, allow_null=True)
    account_interim = AccountField(required=False, allow_null=True)
    strategy1_position = Strategy1Field(required=False, allow_null=True)
    strategy1_cash = Strategy1Field(required=False, allow_null=True)
    strategy2_position = Strategy2Field(required=False, allow_null=True)
    strategy2_cash = Strategy2Field(required=False, allow_null=True)
    strategy3_position = Strategy3Field(required=False, allow_null=True)
    strategy3_cash = Strategy3Field(required=False, allow_null=True)

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
                  'strategy1_position', 'strategy1_cash',
                  'strategy2_position', 'strategy2_cash',
                  'strategy3_position', 'strategy3_cash',
                  'reference_fx_rate',
                  'is_locked', 'is_canceled',
                  'factor', 'trade_price',
                  'principal_amount', 'carry_amount', 'overheads',
                  'responsible', 'counterparty',
                  'attributes']
