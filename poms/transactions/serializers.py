from __future__ import unicode_literals

import six
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from poms.accounts.fields import AccountField
from poms.accounts.models import Account
from poms.common.serializers import PomsClassSerializer, ModelWithUserCodeSerializer
from poms.counterparties.fields import ResponsibleField, CounterpartyField
from poms.counterparties.models import Counterparty, Responsible
from poms.currencies.fields import CurrencyField
from poms.currencies.models import Currency
from poms.instruments.fields import InstrumentField, InstrumentTypeField
from poms.instruments.models import Instrument, InstrumentType, DailyPricingModel, PaymentSizeDetail
from poms.obj_attrs.models import AbstractAttributeType
from poms.obj_attrs.serializers import AbstractAttributeTypeSerializer, AbstractAttributeSerializer, \
    ModelWithAttributesSerializer
from poms.obj_perms.serializers import ModelWithObjectPermissionSerializer
from poms.portfolios.fields import PortfolioField
from poms.portfolios.models import Portfolio
from poms.strategies.fields import Strategy1Field, Strategy2Field, Strategy3Field
from poms.strategies.models import Strategy1, Strategy2, Strategy3
from poms.tags.fields import TagField
from poms.transactions.fields import TransactionAttributeTypeField, TransactionTypeInputContentTypeField, \
    ExpressionField, TransactionTypeGroupField
from poms.transactions.models import TransactionClass, Transaction, TransactionType, TransactionAttributeType, \
    TransactionAttribute, TransactionTypeAction, TransactionTypeActionTransaction, TransactionTypeActionInstrument, \
    TransactionTypeInput, TransactionTypeGroup
from poms.users.fields import MasterUserField


class TransactionClassSerializer(PomsClassSerializer):
    class Meta(PomsClassSerializer.Meta):
        model = TransactionClass


class TransactionTypeGroupSerializer(ModelWithObjectPermissionSerializer, ModelWithUserCodeSerializer):
    master_user = MasterUserField()

    class Meta:
        model = TransactionTypeGroup
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'public_name', 'notes']


class TransactionInputField(serializers.CharField):
    def __init__(self, **kwargs):
        super(TransactionInputField, self).__init__(**kwargs)

    def to_representation(self, value):
        return value.name if value else None


class TransactionTypeActionInstrumentPhantomField(serializers.IntegerField):
    def to_representation(self, value):
        return value.order if value else None


class TransactionTypeInputSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=255, allow_null=False, allow_blank=False,
                                 validators=[
                                     # serializers.RegexValidator(regex='[a-zA-Z0-9_]+'),
                                     serializers.RegexValidator(regex='[a-zA-Z_][a-zA-Z0-9_]*'),
                                 ])
    content_type = TransactionTypeInputContentTypeField(allow_null=True, allow_empty=True)

    class Meta:
        model = TransactionTypeInput
        fields = ['id', 'name', 'verbose_name', 'value_type', 'content_type', 'order']
        read_only_fields = ['order']

    def validate(self, data):
        value_type = data['value_type']
        if value_type == TransactionTypeInput.RELATION:
            content_type = data.get('content_type', None)
            if content_type is None:
                self.content_type.fail('required')
        return data


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
    user_text_1 = ExpressionField(allow_blank=True)
    user_text_2 = ExpressionField(allow_blank=True)
    user_text_3 = ExpressionField(allow_blank=True)

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
            'default_price', 'default_accrued',
            'user_text_1', 'user_text_2', 'user_text_3',
        ]


class TransactionTypeActionTransactionSerializer(serializers.ModelSerializer):
    portfolio = PortfolioField(allow_null=True)
    portfolio_input = TransactionInputField(allow_null=True)
    instrument = InstrumentField(allow_null=True)
    instrument_input = TransactionInputField(allow_null=True)
    instrument_phantom = TransactionTypeActionInstrumentPhantomField(allow_null=True)
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
    strategy1_cash = Strategy1Field(allow_null=True)
    strategy1_cash_input = TransactionInputField(allow_null=True)
    strategy2_position = Strategy1Field(allow_null=True)
    strategy2_position_input = TransactionInputField(allow_null=True)
    strategy2_cash = Strategy1Field(allow_null=True)
    strategy2_cash_input = TransactionInputField(allow_null=True)
    strategy3_position = Strategy1Field(allow_null=True)
    strategy3_position_input = TransactionInputField(allow_null=True)
    strategy3_cash = Strategy1Field(allow_null=True)
    strategy3_cash_input = TransactionInputField(allow_null=True)
    responsible = ResponsibleField(allow_null=True)
    responsible_input = TransactionInputField(allow_null=True)
    factor = ExpressionField(default="0.0")
    trade_price = ExpressionField(default="0.0")
    principal_amount = ExpressionField(default="0.0")
    carry_amount = ExpressionField(default="0.0")
    overheads = ExpressionField(default="0.0")
    counterparty = CounterpartyField(allow_null=True)
    counterparty_input = TransactionInputField(allow_null=True)

    class Meta:
        model = TransactionTypeActionTransaction
        fields = [
            'transaction_class',
            'portfolio', 'portfolio_input',
            'instrument', 'instrument_input', 'instrument_phantom',
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
            'factor',
            'trade_price',
            'principal_amount',
            'carry_amount',
            'overheads',
            'responsible', 'responsible_input',
            'counterparty', 'counterparty_input',
        ]


class TransactionTypeActionSerializer(serializers.ModelSerializer):
    transaction = TransactionTypeActionTransactionSerializer(source='transactiontypeactiontransaction', allow_null=True)
    instrument = TransactionTypeActionInstrumentSerializer(source='transactiontypeactioninstrument', allow_null=True)

    class Meta:
        model = TransactionTypeAction
        fields = ['id', 'order', 'transaction', 'instrument']
        read_only_fields = ['order']

    def validate(self, attrs):
        # TODO: transaction or instrument prsent
        return attrs


class TransactionTypeSerializer(ModelWithObjectPermissionSerializer, ModelWithUserCodeSerializer):
    master_user = MasterUserField()
    group = TransactionTypeGroupField(allow_null=False)
    display_expr = ExpressionField(allow_blank=False, allow_null=False)
    instrument_types = InstrumentTypeField(many=True, required=False, allow_null=True)
    portfolios = PortfolioField(many=True, required=False, allow_null=True)
    tags = TagField(many=True, required=False, allow_null=True)
    inputs = TransactionTypeInputSerializer(many=True)
    actions = TransactionTypeActionSerializer(many=True, read_only=False)

    class Meta:
        model = TransactionType
        fields = ['url', 'id', 'master_user', 'group', 'user_code', 'name', 'short_name', 'public_name', 'notes',
                  'display_expr', 'instrument_types', 'portfolios', 'tags', 'inputs', 'actions']

    def validate(self, attrs):
        # TODO: validate *_input...
        return attrs

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

    def save_inputs(self, instance, inputs_data, created):
        cur_inputs = {i.name: i for i in instance.inputs.all()}
        new_inputs = {}
        for order, input_data in enumerate(inputs_data):
            name = input_data['name']
            input = cur_inputs.pop(name, None)
            if input is None:
                input = TransactionTypeInput(transaction_type=instance)
            input.order = order
            for attr, value in six.iteritems(input_data):
                setattr(input, attr, value)
            input.save()
            new_inputs[input.name] = input
        return new_inputs

    def save_actions(self, instance, actions_data, created):
        inputs = {i.name: i for i in instance.inputs.all()}
        cur_actions = {i.order: i for i in instance.actions.select_related('transactiontypeactioninstrument',
                                                                           'transactiontypeactiontransaction').all()}
        actions = []
        for order, action_data in enumerate(actions_data):
            instrument_data = action_data.get('instrument', action_data.get('transactiontypeactioninstrument'))
            transaction_data = action_data.get('transaction', action_data.get('transactiontypeactiontransaction'))
            data = instrument_data or transaction_data

            # replace input name to input object
            for attr, value in six.iteritems(data):
                if attr.endswith('_input') and value:
                    # print('name=%s, value=%s' % (name, value,))
                    data[attr] = inputs[value]
                if transaction_data and attr == 'instrument_phantom' and value is not None:
                    data[attr] = actions[value]

            action = cur_actions.pop(order, None)
            if created:
                if instrument_data:
                    action = TransactionTypeActionInstrument(transaction_type=instance)
                elif transaction_data:
                    action = TransactionTypeActionTransaction(transaction_type=instance)
                else:
                    raise RuntimeError('some unknown error')
            else:
                try:
                    action = action.transactiontypeactioninstrument
                except ObjectDoesNotExist:
                    try:
                        action = action.transactiontypeactiontransaction
                    except ObjectDoesNotExist:
                        pass
                if action is None:
                    raise RuntimeError('unknown action')
            action.order = order
            for attr, value in six.iteritems(data):
                setattr(action, attr, value)
            action.save()
            actions.append(action)


class TransactionTypeProcessSerializer(serializers.Serializer):
    def __init__(self, transaction_type=None, **kwargs):
        context = kwargs.get('context', None) or {}
        self.transaction_type = transaction_type or context.get('transaction_type', None)

        super(TransactionTypeProcessSerializer, self).__init__(**kwargs)

        from poms.instruments.serializers import InstrumentSerializer
        self.fields['instruments'] = InstrumentSerializer(many=True, read_only=True, context=context)
        self.fields['transactions'] = TransactionSerializer(many=True, read_only=True, context=context)

        if self.transaction_type:
            for i in self.transaction_type.inputs.order_by('value_type', 'name').all():
                name = '%s' % i.name
                field = None
                if i.value_type == TransactionTypeInput.STRING:
                    field = serializers.CharField(required=True, label=i.name, help_text=i.verbose_name)
                elif i.value_type == TransactionTypeInput.NUMBER:
                    field = serializers.FloatField(required=True, label=i.name, help_text=i.verbose_name)
                elif i.value_type == TransactionTypeInput.DATE:
                    field = serializers.DateField(required=True, label=i.name, help_text=i.verbose_name)
                elif i.value_type == TransactionTypeInput.RELATION:
                    content_type = i.content_type
                    model_class = content_type.model_class()
                    if issubclass(model_class, Account):
                        field = AccountField(required=True, label=i.name, help_text=i.verbose_name)
                    elif issubclass(model_class, Currency):
                        field = CurrencyField(required=True, label=i.name, help_text=i.verbose_name)
                    elif issubclass(model_class, Instrument):
                        field = InstrumentField(required=True, label=i.name, help_text=i.verbose_name)
                    elif issubclass(model_class, InstrumentType):
                        field = InstrumentTypeField(required=True, label=i.name, help_text=i.verbose_name)
                    elif issubclass(model_class, Counterparty):
                        field = CounterpartyField(required=True, label=i.name, help_text=i.verbose_name)
                    elif issubclass(model_class, Responsible):
                        field = ResponsibleField(required=True, label=i.name, help_text=i.verbose_name)
                    elif issubclass(model_class, Strategy1):
                        field = Strategy1Field(required=True, label=i.name, help_text=i.verbose_name)
                    elif issubclass(model_class, Strategy2):
                        field = Strategy2Field(required=True, label=i.name, help_text=i.verbose_name)
                    elif issubclass(model_class, Strategy3):
                        field = Strategy3Field(required=True, label=i.name, help_text=i.verbose_name)
                    elif issubclass(model_class, DailyPricingModel):
                        field = serializers.PrimaryKeyRelatedField(queryset=DailyPricingModel.objects, required=True,
                                                                   label=i.name, help_text=i.verbose_name)
                    elif issubclass(model_class, PaymentSizeDetail):
                        field = serializers.PrimaryKeyRelatedField(queryset=PaymentSizeDetail.objects, required=True,
                                                                   label=i.name, help_text=i.verbose_name)
                    elif issubclass(model_class, Portfolio):
                        field = PortfolioField(required=True, label=i.name, help_text=i.verbose_name)
                if field:
                    self.fields[name] = field
                else:
                    raise RuntimeError('Unknown value type %s' % i.value_type)


class TransactionAttributeTypeSerializer(AbstractAttributeTypeSerializer):
    class Meta(AbstractAttributeTypeSerializer.Meta):
        model = TransactionAttributeType

    def validate_value_type(self, value_type):
        if value_type == AbstractAttributeType.CLASSIFIER:
            raise ValidationError({'value_type': _('Value type classifier is unsupported')})
        return value_type


class TransactionAttributeSerializer(AbstractAttributeSerializer):
    attribute_type = TransactionAttributeTypeField()

    # strategy_position = StrategyRootField(required=False, allow_null=True)
    # strategy_cash = StrategyRootField(required=False, allow_null=True)

    class Meta(AbstractAttributeSerializer.Meta):
        model = TransactionAttribute
        fields = AbstractAttributeSerializer.Meta.fields + ['attribute_type']


class TransactionSerializer(ModelWithAttributesSerializer):
    master_user = MasterUserField()
    complex_transaction = serializers.PrimaryKeyRelatedField(read_only=True)
    complex_transaction_order = serializers.IntegerField(read_only=True)
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
                  'transaction_code',
                  'complex_transaction', 'complex_transaction_order',
                  'transaction_class',
                  'portfolio',
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
