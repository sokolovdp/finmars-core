from __future__ import unicode_literals

import six
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty

from poms.accounts.fields import AccountField
from poms.common import formula
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


class TransactionInputField(serializers.CharField):
    def __init__(self, **kwargs):
        super(TransactionInputField, self).__init__(**kwargs)

    def to_representation(self, value):
        return value.name if value else None


class ExpressionField(serializers.CharField):
    def __init__(self, **kwargs):
        kwargs['allow_null'] = kwargs.get('allow_null', False)
        kwargs['allow_blank'] = kwargs.get('allow_blank', False)
        super(ExpressionField, self).__init__(**kwargs)

    def run_validation(self, data=empty):
        value = super(ExpressionField, self).run_validation(data)
        if data:
            _, err = formula.parse(data)
            if err:
                raise ValidationError('Invalid expression: %s' % err)
        return value


class TransactionTypeActionInstrumentSerializer(serializers.ModelSerializer):
    user_code = ExpressionField(allow_blank=True)
    name = ExpressionField(allow_blank=False)
    public_name = ExpressionField(allow_blank=True)
    short_name = ExpressionField(allow_blank=True)
    notes = ExpressionField(allow_blank=True)
    instrument_type = InstrumentTypeField(allow_null=True)
    instrument_type_input = TransactionInputField(allow_null=True)
    pricing_currency = CurrencyField(allow_null=True)
    pricing_currency_input = TransactionInputField(allow_null=True)
    price_multiplier = ExpressionField(default="1.0")
    accrued_currency = CurrencyField(allow_null=True)
    accrued_currency_input = TransactionInputField(allow_null=True)
    accrued_multiplier = ExpressionField(default="1.0")
    daily_pricing_model_input = TransactionInputField(allow_null=True)
    payment_size_detail_input = TransactionInputField(allow_null=True)
    default_price = ExpressionField(default="0.0")
    default_accrued = ExpressionField(default="0.0")

    class Meta:
        model = TransactionTypeActionInstrument
        fields = [
            'user_code',
            'name',
            'public_name',
            'short_name',
            'notes',
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


class TransactionTypeActionTransactionSerializer(serializers.ModelSerializer):
    instrument = InstrumentField(allow_null=True)
    instrument_input = TransactionInputField(allow_null=True)
    transaction_currency = CurrencyField(allow_null=True)
    transaction_currency_input = TransactionInputField(allow_null=True)
    position_size_with_sign = ExpressionField(default="0.0")
    settlement_currency = CurrencyField(allow_null=True)
    settlement_currency_input = TransactionInputField(allow_null=True)
    cash_consideration = ExpressionField(default="0.0")
    principal_with_sign = ExpressionField(default="0.0")
    carry_with_sign = ExpressionField(default="0.0")
    overheads_with_sign = ExpressionField(default="0.0")
    account_position = AccountField(allow_null=True)
    account_position_input = TransactionInputField(allow_null=True)
    account_cash = AccountField(allow_null=True)
    account_cash_input = TransactionInputField(allow_null=True)
    account_interim = AccountField(allow_null=True)
    account_interim_input = TransactionInputField(allow_null=True)
    accounting_date = ExpressionField(default="now()")
    cash_date = ExpressionField(default="now()")
    strategy1_position = Strategy1Field(allow_null=True)
    strategy1_position_input = TransactionInputField(allow_null=True)
    strategy2_position = Strategy1Field(allow_null=True)
    strategy2_position_input = TransactionInputField(allow_null=True)
    strategy3_position = Strategy1Field(allow_null=True)
    strategy3_position_input = TransactionInputField(allow_null=True)

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


class TransactionTypeActionSerializer(serializers.ModelSerializer):
    transaction = TransactionTypeActionTransactionSerializer(source='transactiontypeactiontransaction', allow_null=True)
    instrument = TransactionTypeActionInstrumentSerializer(source='transactiontypeactioninstrument', allow_null=True)

    class Meta:
        model = TransactionTypeAction
        fields = ['id', 'order', 'transaction', 'instrument']


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

    def create(self, validated_data):
        inputs = validated_data.pop('inputs', None)
        actions = validated_data.pop('actions', None)
        instance = super(TransactionTypeSerializer, self).create(validated_data)
        self.save_inputs(instance, inputs, True)
        self.save_actions(instance, actions, True)
        return instance

    def update(self, instance, validated_data):
        inputs = validated_data.pop('inputs', None)
        actions = validated_data.pop('actions', None)
        instance = super(TransactionTypeSerializer, self).update(instance, validated_data)
        inputs = self.save_inputs(instance, inputs, False)
        self.save_actions(instance, actions, False)
        if inputs:
            instance.inputs.exclude(id__in=[i.id for i in six.itervalues(inputs)]).delete()
        return instance

    def save_inputs(self, instance, inputs, created):
        cur_inputs = {i.name: i for i in instance.inputs.all()}
        new_inputs = {i['name']: i for i in inputs}
        for name, input_data in six.iteritems(new_inputs):
            input = cur_inputs.pop(name, None)
            if input is None:
                input = TransactionTypeInput(transaction_type=instance)
            for attr, value in six.iteritems(input_data):
                setattr(input, attr, value)
            input.save()
            new_inputs[input.name] = input
        return new_inputs

    def save_actions(self, instance, actions, created):
        inputs = {i.name: i for i in instance.inputs.all()}
        cur_actions = {i.order: i for i in instance.actions.select_related('transactiontypeactioninstrument',
                                                                           'transactiontypeactiontransaction').all()}
        for action_data in actions:
            instrument_data = action_data.get('instrument', action_data.get('transactiontypeactioninstrument'))
            transaction_data = action_data.get('transaction', action_data.get('transactiontypeactiontransaction'))
            data = instrument_data or transaction_data

            # replace input name to input object
            for name, value in six.iteritems(data):
                if name.endswith('_input') and value:
                    # print('name=%s, value=%s' % (name, value,))
                    data[name] = inputs[value]

            action = cur_actions.pop(action_data['order'], None)
            if created:
                if instrument_data:
                    action = TransactionTypeActionInstrument(transaction_type=instance)
                elif transaction_data:
                    action = TransactionTypeActionTransaction(transaction_type=instance)
                else:
                    raise RuntimeError('unknown action')
                action.order = action_data['order']
                for attr, value in six.iteritems(instrument_data):
                    setattr(action, attr, value)
                action.save()
            else:
                try:
                    instrument = action.transactiontypeactioninstrument
                except ObjectDoesNotExist:
                    instrument = None
                try:
                    transaction = action.transactiontypeactiontransaction
                except ObjectDoesNotExist:
                    transaction = None
                action = instrument or transaction
                if action is None:
                    raise RuntimeError('unknown action')
                for attr, value in six.iteritems(data):
                    setattr(action, attr, value)
                action.save()


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
