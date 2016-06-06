from __future__ import unicode_literals

import pprint

from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from poms.accounts.fields import AccountField
from poms.common.serializers import PomsClassSerializer
from poms.counterparties.fields import ResponsibleField, CounterpartyField
from poms.currencies.fields import CurrencyField
from poms.instruments.fields import InstrumentField, InstrumentTypeField
from poms.obj_attrs.models import AttributeTypeBase
from poms.obj_attrs.serializers import AttributeTypeSerializerBase, AttributeSerializerBase, \
    ModelWithAttributesSerializer
from poms.obj_perms.serializers import ModelWithObjectPermissionSerializer
from poms.portfolios.fields import PortfolioField
from poms.strategies.fields import Strategy1Field, Strategy2Field, Strategy3Field
from poms.tags.fields import TagField
from poms.transactions.fields import TransactionAttributeTypeField
from poms.transactions.models import TransactionClass, Transaction, TransactionType, TransactionAttributeType, \
    TransactionAttribute, TransactionTypeAction, TransactionTypeActionTransaction, TransactionTypeActionInstrument, \
    TransactionTypeInput
from poms.users.fields import MasterUserField


class TransactionClassSerializer(PomsClassSerializer):
    class Meta(PomsClassSerializer.Meta):
        model = TransactionClass


class TransactionTypeInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionTypeInput
        fields = ['id', 'value_type', 'name', 'order']


class TransactionTypeActionTransactionSerializer(serializers.ModelSerializer):
    instrument = InstrumentField()
    transaction_currency = CurrencyField()
    # transaction_currency_input = ?
    settlement_currency = CurrencyField()
    # settlement_currency_input = ?
    account_position = AccountField()
    # account_position_input = ?
    account_cash = AccountField()
    # account_cash_input = ?
    account_interim = AccountField()
    # aaccount_interim_input = ?
    strategy1_position = Strategy1Field()
    # strategy1_position_input = ?
    strategy2_position = Strategy1Field()
    # strategy2_position_input = ?
    strategy3_position = Strategy1Field()

    # strategy3_position_input = ?
    class Meta:
        model = TransactionTypeActionTransaction
        fields = [
            'transaction_class',
            'instrument', 'instrument_input',
            'transaction_currency', 'transaction_currency_input',
            'position_size_with_sign',
            'settlement_currency', 'settlement_currency_input',
            'cash_consideration',
            'principal_with_sign',
            'carry_with_sign',
            'overheads_with_sign',
            'account_position', 'account_position_input',
            'account_cash', 'account_cash_input',
            'account_interim', 'account_interim_input',
            'accounting_date',
            'cash_date',
            'strategy1_position', 'strategy1_position_input',
            'strategy1_cash', 'strategy1_cash_input',
            'strategy2_position', 'strategy2_position_input',
            'strategy2_cash', 'strategy2_cash_input',
            'strategy3_position', 'strategy3_position_input',
            'strategy3_cash', 'strategy3_cash_input',
        ]


class TransactionTypeActionInstrumentSerializer(serializers.ModelSerializer):
    instrument_type = InstrumentTypeField()
    # instrument_type_input = ?
    pricing_currency = CurrencyField()
    # pricing_currency_input = ?
    accrued_currency = CurrencyField()

    # accrued_currency_input = ?
    # daily_pricing_model_input = ?
    # payment_size_detail_input = ?
    class Meta:
        model = TransactionTypeActionInstrument
        fields = [
            'instrument_type', 'instrument_type_input',
            'pricing_currency', 'pricing_currency_input',
            'price_multiplier',
            'accrued_currency', 'accrued_currency_input',
            'accrued_multiplier',
            'daily_pricing_model', 'daily_pricing_model_input',
            'payment_size_detail', 'payment_size_detail_input',
            'default_price',
            'default_accrued',
        ]


class TransactionTypeActionSerializer(serializers.ModelSerializer):
    transaction = TransactionTypeActionTransactionSerializer(source='transactiontypeactiontransaction')
    instrument = TransactionTypeActionInstrumentSerializer(source='transactiontypeactioninstrument')

    class Meta:
        model = TransactionTypeAction
        fields = ['id', 'order', 'transaction', 'instrument']

        # def to_representation(self, obj):
        #     # print('----')
        #     # print(obj.id, obj.order)
        #     try:
        #         # print(obj.transactiontypeactiontransaction, obj.transactiontypeactiontransaction.order)
        #         ret = TransactionTypeActionTransactionSerializer(instance=obj.transactiontypeactiontransaction,
        #                                                          context=self.context).to_representation(
        #             obj.transactiontypeactiontransaction)
        #         ret['action_type'] = 'transaction'
        #         return ret
        #     except ObjectDoesNotExist:
        #         pass
        #     try:
        #         # print(obj.transactiontypeactioninstrument, obj.transactiontypeactioninstrument.order)
        #         ret = TransactionTypeActionInstrumentSerializer(instance=obj.transactiontypeactioninstrument,
        #                                                         context=self.context).to_representation(
        #             obj.transactiontypeactioninstrument)
        #         ret['action_type'] = 'instrument'
        #         return ret
        #     except ObjectDoesNotExist:
        #         pass
        #         # TransactionTypeActionTransactionSerializer(obj.transactiontypeactiontransaction, context=self.context).to_representation(obj)
        #         # TransactionTypeActionInstrumentSerializer(obj.transactiontypeactioninstrument, context=self.context).to_representation(obj)
        #         # if hasattr(obj, 'transactiontypeactiontransaction'):
        #         #     return TransactionTypeActionTransactionSerializer(obj.transactiontypeactiontransaction, context=self.context).to_representation(obj)
        #         # elif hasattr(obj, 'transactiontypeactioninstrument'):
        #         #     return TransactionTypeActionInstrumentSerializer(obj.transactiontypeactioninstrument, context=self.context).to_representation(obj)
        #     return super(TransactionTypeActionSerializer, self).to_representation(obj)
        #
        # def to_internal_value(self, data):
        #     # print(data)
        #     action_type = data['action_type']
        #     if action_type == 'transaction':
        #         return TransactionTypeActionTransactionSerializer(context=self.context).to_internal_value(data)
        #     elif action_type == 'instrument':
        #         return TransactionTypeActionInstrumentSerializer(context=self.context).to_internal_value(data)
        #     return super(TransactionTypeActionSerializer, self).to_internal_value(data)


class TransactionTypeSerializer(ModelWithObjectPermissionSerializer):
    master_user = MasterUserField()
    tags = TagField(many=True, required=False, allow_null=True)
    instrument_types = InstrumentTypeField(many=True)
    inputs = TransactionTypeInputSerializer(many=True)
    actions = TransactionTypeActionSerializer(many=True, read_only=False)

    class Meta:
        model = TransactionType
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes', 'tags',
                  'instrument_types', 'inputs', 'actions']

    def update(self, instance, validated_data):
        pprint.pprint(validated_data)
        return instance


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
    attributes = TransactionAttributeSerializer(many=True, required=False, allow_null=True)

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
