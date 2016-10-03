from __future__ import unicode_literals

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from poms.accounts.fields import AccountField, AccountDefault
from poms.accounts.models import Account
from poms.common import formula
from poms.common.fields import ExpressionField
from poms.common.serializers import PomsClassSerializer, ModelWithUserCodeSerializer, AbstractClassifierSerializer, \
    AbstractClassifierNodeSerializer, ReadonlyNamedModelSerializer, ReadonlyModelWithNameSerializer
from poms.counterparties.fields import ResponsibleField, CounterpartyField, ResponsibleDefault, CounterpartyDefault
from poms.counterparties.models import Counterparty, Responsible
from poms.currencies.fields import CurrencyField, CurrencyDefault
from poms.currencies.models import Currency
from poms.instruments.fields import InstrumentField, InstrumentTypeField
from poms.instruments.models import Instrument, InstrumentType, DailyPricingModel, PaymentSizeDetail
from poms.instruments.serializers import InstrumentSerializer
from poms.integrations.fields import PriceDownloadSchemeField
from poms.integrations.models import PriceDownloadScheme
from poms.obj_attrs.serializers import AbstractAttributeTypeSerializer, AbstractAttributeSerializer, \
    ModelWithAttributesSerializer
from poms.obj_perms.serializers import ModelWithObjectPermissionSerializer, \
    ReadonlyNamedModelWithObjectPermissionSerializer
from poms.portfolios.fields import PortfolioField, PortfolioDefault
from poms.portfolios.models import Portfolio
from poms.strategies.fields import Strategy1Field, Strategy2Field, Strategy3Field, Strategy1Default, Strategy2Default, \
    Strategy3Default
from poms.strategies.models import Strategy1, Strategy2, Strategy3
from poms.tags.fields import TagField
from poms.transactions.fields import TransactionAttributeTypeField, TransactionTypeInputContentTypeField, \
    TransactionTypeGroupField, TransactionClassifierField
from poms.transactions.models import TransactionClass, Transaction, TransactionType, TransactionAttributeType, \
    TransactionAttribute, TransactionTypeAction, TransactionTypeActionTransaction, TransactionTypeActionInstrument, \
    TransactionTypeInput, TransactionTypeGroup, ComplexTransaction, TransactionClassifier, EventClass, NotificationClass
from poms.transactions.processor import TransactionTypeProcessor
from poms.users.fields import MasterUserField


class EventClassSerializer(PomsClassSerializer):
    class Meta(PomsClassSerializer.Meta):
        model = EventClass


class NotificationClassSerializer(PomsClassSerializer):
    class Meta(PomsClassSerializer.Meta):
        model = NotificationClass


class TransactionClassSerializer(PomsClassSerializer):
    class Meta(PomsClassSerializer.Meta):
        model = TransactionClass


class TransactionTypeGroupSerializer(ModelWithObjectPermissionSerializer, ModelWithUserCodeSerializer):
    master_user = MasterUserField()
    tags = TagField(many=True, required=False, allow_null=True)
    tags_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='tags', many=True)

    class Meta:
        model = TransactionTypeGroup
        fields = [
            'url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'public_name', 'notes', 'is_deleted',
            'tags', 'tags_object',
        ]


# class TransactionTypeGroupBulkObjectPermissionSerializer(AbstractBulkObjectPermissionSerializer):
#     content_objects = TransactionTypeGroupField(many=True, allow_null=False, allow_empty=False)
#
#     class Meta:
#         model = TransactionTypeGroup


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
    content_type = TransactionTypeInputContentTypeField(required=False, allow_null=True, allow_empty=True)

    account = AccountField(required=False, allow_null=True)
    account_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='account')
    instrument_type = InstrumentTypeField(required=False, allow_null=True)
    instrument_type_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='instrument_type')
    instrument = InstrumentField(required=False, allow_null=True)
    instrument_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='instrument')
    currency = CurrencyField(required=False, allow_null=True)
    currency_object = ReadonlyNamedModelSerializer(source='currency')
    counterparty = CounterpartyField(required=False, allow_null=True)
    counterparty_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='counterparty')
    responsible = ResponsibleField(required=False, allow_null=True)
    responsible_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='responsible')
    portfolio = PortfolioField(required=False, allow_null=True)
    portfolio_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='portfolio')
    strategy1 = Strategy1Field(required=False, allow_null=True)
    strategy1_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='strategy1')
    strategy2 = Strategy2Field(required=False, allow_null=True)
    strategy2_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='strategy2')
    strategy3 = Strategy3Field(required=False, allow_null=True)
    strategy3_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='strategy3')
    daily_pricing_model_object = ReadonlyModelWithNameSerializer(source='daily_pricing_model')
    payment_size_detail_object = ReadonlyModelWithNameSerializer(source='daily_pricing_model')
    price_download_scheme = PriceDownloadSchemeField(required=False, allow_null=True)
    price_download_scheme_object = ReadonlyModelWithNameSerializer(source='price_download_scheme',
                                                                   fields=['scheme_name'])

    class Meta:
        model = TransactionTypeInput
        fields = [
            'id', 'name', 'verbose_name', 'value_type', 'content_type', 'order', 'is_fill_from_context', 'value',
            'account', 'account_object', 'instrument_type', 'instrument_type_object', 'instrument', 'instrument_object',
            'currency', 'currency_object', 'counterparty', 'counterparty_object', 'responsible', 'responsible_object',
            'portfolio', 'portfolio_object', 'strategy1', 'strategy1_object', 'strategy2', 'strategy2_object',
            'strategy3', 'strategy3_object', 'daily_pricing_model', 'daily_pricing_model_object',
            'payment_size_detail', 'payment_size_detail_object', 'price_download_scheme',
            'price_download_scheme_object',
        ]
        read_only_fields = ['order']

    def validate(self, data):
        value_type = data['value_type']
        if value_type == TransactionTypeInput.RELATION:
            content_type = data.get('content_type', None)
            if content_type is None:
                self.content_type.fail('required')
        return data


class TransactionTypeActionInstrumentSerializer(serializers.ModelSerializer):
    user_code = ExpressionField(required=False, allow_blank=True, default='""')
    name = ExpressionField(required=False, allow_blank=True, default='""')
    public_name = ExpressionField(required=False, allow_blank=True, default='""')
    short_name = ExpressionField(required=False, allow_blank=True, default='""')
    notes = ExpressionField(required=False, allow_blank=True, default='""')

    instrument_type = InstrumentTypeField(required=False, allow_null=True)
    instrument_type_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='instrument_type')
    instrument_type_input = TransactionInputField(required=False, allow_null=True)
    pricing_currency = CurrencyField(required=False, allow_null=True)
    pricing_currency_object = ReadonlyNamedModelSerializer(source='pricing_currency')
    pricing_currency_input = TransactionInputField(required=False, allow_null=True)
    price_multiplier = ExpressionField(required=False, default="1.0")
    accrued_currency = CurrencyField(required=False, allow_null=True)
    accrued_currency_object = ReadonlyNamedModelSerializer(source='accrued_currency')
    accrued_currency_input = TransactionInputField(required=False, allow_null=True)
    accrued_multiplier = ExpressionField(required=False, default="1.0")
    payment_size_detail_input = TransactionInputField(required=False, allow_null=True)
    default_price = ExpressionField(required=False, default="0.0")
    default_accrued = ExpressionField(required=False, default="0.0")
    user_text_1 = ExpressionField(required=False, allow_blank=True, default='""')
    user_text_2 = ExpressionField(required=False, allow_blank=True, default='""')
    user_text_3 = ExpressionField(required=False, allow_blank=True, default='""')

    reference_for_pricing = ExpressionField(required=False, allow_blank=True, default='""')
    daily_pricing_model_object = ReadonlyModelWithNameSerializer(source='daily_pricing_model')
    daily_pricing_model_input = TransactionInputField(required=False, allow_null=True)
    payment_size_detail_object = ReadonlyModelWithNameSerializer(source='daily_pricing_model')
    price_download_scheme = PriceDownloadSchemeField(required=False, allow_null=True)
    price_download_scheme_object = ReadonlyModelWithNameSerializer(source='price_download_scheme',
                                                                   fields=['scheme_name'])

    price_download_scheme_input = TransactionInputField(required=False, allow_null=True)
    maturity_date = ExpressionField(required=False, allow_blank=True)

    class Meta:
        model = TransactionTypeActionInstrument
        fields = [
            'user_code', 'name', 'public_name', 'short_name', 'notes',
            'instrument_type', 'instrument_type_object', 'instrument_type_input',
            'pricing_currency', 'pricing_currency_object', 'pricing_currency_input', 'price_multiplier',
            'accrued_currency', 'accrued_currency_object', 'accrued_currency_input', 'accrued_multiplier',
            'payment_size_detail', 'payment_size_detail_object', 'payment_size_detail_input',
            'default_price', 'default_accrued', 'user_text_1', 'user_text_2', 'user_text_3', 'reference_for_pricing',
            'price_download_scheme', 'price_download_scheme_object', 'price_download_scheme_input',
            'daily_pricing_model', 'daily_pricing_model_object', 'daily_pricing_model_input',
            'maturity_date',
        ]


class TransactionTypeActionTransactionSerializer(serializers.ModelSerializer):
    transaction_class_object = ReadonlyModelWithNameSerializer(source='transaction_class')
    portfolio = PortfolioField(required=False, allow_null=True)
    portfolio_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='portfolio')
    portfolio_input = TransactionInputField(required=False, allow_null=True)
    instrument = InstrumentField(required=False, allow_null=True)
    instrument_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='instrument')
    instrument_input = TransactionInputField(required=False, allow_null=True)
    instrument_phantom = TransactionTypeActionInstrumentPhantomField(required=False, allow_null=True)
    transaction_currency = CurrencyField(required=False, allow_null=True)
    transaction_currency_object = ReadonlyNamedModelSerializer(source='transaction_currency')
    transaction_currency_input = TransactionInputField(required=False, allow_null=True)
    position_size_with_sign = ExpressionField(required=False, default="0.0")
    settlement_currency = CurrencyField(required=False, allow_null=True)
    settlement_currency_object = ReadonlyNamedModelSerializer(source='settlement_currency')
    settlement_currency_input = TransactionInputField(required=False, allow_null=True)
    cash_consideration = ExpressionField(required=False, default="0.0")
    principal_with_sign = ExpressionField(required=False, default="0.0")
    carry_with_sign = ExpressionField(required=False, default="0.0")
    overheads_with_sign = ExpressionField(required=False, default="0.0")
    account_position = AccountField(required=False, allow_null=True)
    account_position_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='account_position')
    account_position_input = TransactionInputField(required=False, allow_null=True)
    account_cash = AccountField(required=False, allow_null=True)
    account_cash_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='account_cash')
    account_cash_input = TransactionInputField(required=False, allow_null=True)
    account_interim = AccountField(required=False, allow_null=True)
    account_interim_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='account_interim')
    account_interim_input = TransactionInputField(required=False, allow_null=True)
    accounting_date = ExpressionField(required=False, default="now()")
    cash_date = ExpressionField(required=False, default="now()")
    strategy1_position = Strategy1Field(required=False, allow_null=True)
    strategy1_position_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='strategy1_position')
    strategy1_position_input = TransactionInputField(required=False, allow_null=True)
    strategy1_cash = Strategy1Field(required=False, allow_null=True)
    strategy1_cash_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='strategy1_cash')
    strategy1_cash_input = TransactionInputField(required=False, allow_null=True)
    strategy2_position = Strategy2Field(required=False, allow_null=True)
    strategy2_position_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='strategy2_position')
    strategy2_position_input = TransactionInputField(required=False, allow_null=True)
    strategy2_cash = Strategy2Field(required=False, allow_null=True)
    strategy2_cash_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='strategy2_cash')
    strategy2_cash_input = TransactionInputField(required=False, allow_null=True)
    strategy3_position = Strategy3Field(required=False, allow_null=True)
    strategy3_position_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='strategy3_position')
    strategy3_position_input = TransactionInputField(required=False, allow_null=True)
    strategy3_cash = Strategy3Field(required=False, allow_null=True)
    strategy3_cash_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='strategy3_cash')
    strategy3_cash_input = TransactionInputField(required=False, allow_null=True)
    responsible = ResponsibleField(required=False, allow_null=True)
    responsible_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='responsible')
    responsible_input = TransactionInputField(required=False, allow_null=True)
    counterparty = CounterpartyField(required=False, allow_null=True)
    counterparty_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='counterparty')
    counterparty_input = TransactionInputField(required=False, allow_null=True)
    factor = ExpressionField(required=False, default="0.0")
    trade_price = ExpressionField(required=False, default="0.0")
    principal_amount = ExpressionField(required=False, default="0.0")
    carry_amount = ExpressionField(required=False, default="0.0")
    overheads = ExpressionField(required=False, default="0.0")

    class Meta:
        model = TransactionTypeActionTransaction
        fields = [
            'transaction_class', 'transaction_class_object',
            'portfolio', 'portfolio_object', 'portfolio_input',
            'instrument', 'instrument_object', 'instrument_input', 'instrument_phantom',
            'transaction_currency', 'transaction_currency_object', 'transaction_currency_input',
            'position_size_with_sign',
            'settlement_currency', 'settlement_currency_object', 'settlement_currency_input',
            'cash_consideration',
            'principal_with_sign',
            'carry_with_sign',
            'overheads_with_sign',
            'account_position', 'account_position_object', 'account_position_input',
            'account_cash', 'account_cash_object', 'account_cash_input',
            'account_interim', 'account_interim_object', 'account_interim_input',
            'accounting_date',
            'cash_date',
            'strategy1_position', 'strategy1_position_object', 'strategy1_position_input',
            'strategy1_cash', 'strategy1_cash_object', 'strategy1_cash_input',
            'strategy2_position', 'strategy2_position_object', 'strategy2_position_input',
            'strategy2_cash', 'strategy2_cash_object', 'strategy2_cash_input',
            'strategy3_position', 'strategy3_position_object', 'strategy3_position_input',
            'strategy3_cash', 'strategy3_cash_object', 'strategy3_cash_input',
            'factor',
            'trade_price',
            'principal_amount',
            'carry_amount',
            'overheads',
            'responsible', 'responsible_object', 'responsible_input',
            'counterparty', 'counterparty_object', 'counterparty_input',
        ]


class TransactionTypeActionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    transaction = TransactionTypeActionTransactionSerializer(source='transactiontypeactiontransaction', required=False,
                                                             allow_null=True)
    instrument = TransactionTypeActionInstrumentSerializer(source='transactiontypeactioninstrument', required=False,
                                                           allow_null=True)

    class Meta:
        model = TransactionTypeAction
        fields = ['id', 'order', 'action_notes', 'transaction', 'instrument']

    def validate(self, attrs):
        # TODO: transaction or instrument present
        return attrs


class TransactionTypeSerializer(ModelWithObjectPermissionSerializer, ModelWithUserCodeSerializer):
    master_user = MasterUserField()
    group = TransactionTypeGroupField(required=False, allow_null=False)
    group_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='group')
    display_expr = ExpressionField(required=False, allow_blank=False, allow_null=False, default='')
    instrument_types = InstrumentTypeField(required=False, allow_null=True, many=True)
    instrument_types_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='instrument_types', many=True)
    portfolios = PortfolioField(required=False, allow_null=True, many=True)
    portfolios_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='portfolios', many=True)
    tags = TagField(required=False, many=True, allow_null=True)
    tags_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='tags', many=True)
    inputs = TransactionTypeInputSerializer(required=False, many=True)
    actions = TransactionTypeActionSerializer(required=False, many=True, read_only=False)
    book_transaction_layout = serializers.JSONField(required=False, allow_null=True)

    class Meta:
        model = TransactionType
        fields = [
            'url', 'id', 'master_user', 'group', 'group_object',
            'user_code', 'name', 'short_name', 'public_name', 'notes',
            'display_expr', 'is_valid_for_all_portfolios', 'is_valid_for_all_instruments', 'is_deleted',
            'book_transaction_layout',
            'instrument_types', 'instrument_types_object', 'portfolios', 'portfolios_object', 'tags', 'tags_object',
            'inputs', 'actions'
        ]

    def validate(self, attrs):
        # TODO: validate *_input...
        return attrs

    def create(self, validated_data):
        inputs = validated_data.pop('inputs', None)
        actions = validated_data.pop('actions', None)
        instance = super(TransactionTypeSerializer, self).create(validated_data)
        inputs = self.save_inputs(instance, inputs)
        self.save_actions(instance, actions, inputs)
        return instance

    def update(self, instance, validated_data):
        inputs = validated_data.pop('inputs', None)
        actions = validated_data.pop('actions', None)
        instance = super(TransactionTypeSerializer, self).update(instance, validated_data)
        inputs = self.save_inputs(instance, inputs)
        actions = self.save_actions(instance, actions, inputs)
        if inputs:
            instance.inputs.exclude(id__in=[i.id for i in inputs.values()]).delete()
        if actions:
            instance.actions.exclude(id__in=[a.id for a in actions]).delete()
        return instance

    def save_inputs(self, instance, inputs_data):
        cur_inputs = {i.name: i for i in instance.inputs.all()}
        new_inputs = {}
        for order, input_data in enumerate(inputs_data):
            name = input_data['name']
            input = cur_inputs.pop(name, None)
            if input is None:
                input = TransactionTypeInput(transaction_type=instance)
            input.order = order
            for attr, value in input_data.items():
                setattr(input, attr, value)
            input.save()
            new_inputs[input.name] = input
        return new_inputs

    # def save_actions(self, instance, actions_data, created):
    #     inputs = {i.name: i for i in instance.inputs.all()}
    #
    #     actions_qs = instance.actions.select_related(
    #         'transactiontypeactioninstrument', 'transactiontypeactiontransaction').order_by('order', 'id')
    #     existed_actions = {a.id: a for a in actions_qs}
    #
    #     actions = []
    #     for order, action_data in enumerate(actions_data):
    #         pk = action_data.pop('id', None)
    #         instrument_data = action_data.get('instrument', action_data.get('transactiontypeactioninstrument'))
    #         transaction_data = action_data.get('transaction', action_data.get('transactiontypeactiontransaction'))
    #
    #         data = instrument_data or transaction_data
    #         # replace input name to input object
    #         for attr, value in data.items():
    #             if attr.endswith('_input') and value:
    #                 # print('name=%s, value=%s' % (name, value,))
    #                 data[attr] = inputs[value]
    #             if transaction_data and attr == 'instrument_phantom' and value is not None:
    #                 data[attr] = actions[value]
    #
    #         action = existed_actions.get(pk, None)
    #         if action:
    #             try:
    #                 action = action.transactiontypeactioninstrument
    #             except ObjectDoesNotExist:
    #                 try:
    #                     action = action.transactiontypeactiontransaction
    #                 except ObjectDoesNotExist:
    #                     pass
    #         if not action:
    #             if instrument_data:
    #                 action = TransactionTypeActionInstrument(transaction_type=instance)
    #             elif transaction_data:
    #                 action = TransactionTypeActionTransaction(transaction_type=instance)
    #         if action is None:
    #             raise RuntimeError('unknown action')
    #
    #         action.order = order
    #         for attr, value in data.items():
    #             setattr(action, attr, value)
    #
    #         action.save()
    #         actions.append(action)
    #     return actions

    def save_actions(self, instance, actions_data, inputs):
        actions_qs = instance.actions.select_related(
            'transactiontypeactioninstrument', 'transactiontypeactiontransaction').order_by('order', 'id')
        existed_actions = {a.id: a for a in actions_qs}

        actions = [None for a in actions_data]
        for order, action_data in enumerate(actions_data):
            pk = action_data.pop('id', None)
            action = existed_actions.get(pk, None)

            action_instrument_data = action_data.get('instrument', action_data.get('transactiontypeactioninstrument'))
            if action_instrument_data:
                for attr, value in action_instrument_data.items():
                    if attr.endswith('_input') and value:
                        try:
                            action_instrument_data[attr] = inputs[value]
                        except KeyError:
                            raise ValidationError('Invalid input "%s"' % value)

                action_instrument = None
                if action:
                    try:
                        action_instrument = action.transactiontypeactioninstrument
                    except ObjectDoesNotExist:
                        pass
                if action_instrument is None:
                    action_instrument = TransactionTypeActionInstrument(transaction_type=instance)

                action_instrument.order = order
                action_instrument.action_notes = action_data.get('action_notes', action_instrument.action_notes)
                for attr, value in action_instrument_data.items():
                    setattr(action_instrument, attr, value)

                action_instrument.save()
                actions[order] = action_instrument

        for order, action_data in enumerate(actions_data):
            pk = action_data.pop('id', None)
            action = existed_actions.get(pk, None)
            action_transaction_data = action_data.get('transaction',
                                                      action_data.get('transactiontypeactiontransaction'))
            if action_transaction_data:
                for attr, value in action_transaction_data.items():
                    if attr.endswith('_input') and value:
                        try:
                            action_transaction_data[attr] = inputs[value]
                        except KeyError:
                            raise ValidationError('Invalid input "%s"' % value)
                    if attr == 'instrument_phantom' and value is not None:
                        try:
                            action_transaction_data[attr] = actions[value]
                        except IndexError:
                            raise ValidationError('Invalid action order "%s"' % value)

                action_transaction = None
                if action:
                    try:
                        action_transaction = action.transactiontypeactiontransaction
                    except ObjectDoesNotExist:
                        pass
                if action_transaction is None:
                    action_transaction = TransactionTypeActionTransaction(transaction_type=instance)

                action_transaction.order = order
                action_transaction.action_notes = action_data.get('action_notes', action_transaction.action_notes)
                for attr, value in action_transaction_data.items():
                    setattr(action_transaction, attr, value)

                action_transaction.save()
                actions[order] = action_transaction

        return actions


# class TransactionTypeBulkObjectPermissionSerializer(AbstractBulkObjectPermissionSerializer):
#     content_objects = TransactionTypeField(many=True, allow_null=False, allow_empty=False)
#
#     class Meta:
#         model = TransactionType



class TransactionClassifierSerializer(AbstractClassifierSerializer):
    class Meta(AbstractClassifierSerializer.Meta):
        model = TransactionClassifier


class TransactionClassifierNodeSerializer(AbstractClassifierNodeSerializer):
    class Meta(AbstractClassifierNodeSerializer.Meta):
        model = TransactionClassifier


class TransactionAttributeTypeSerializer(AbstractAttributeTypeSerializer):
    classifiers = TransactionClassifierSerializer(required=False, allow_null=True, many=True)

    class Meta(AbstractAttributeTypeSerializer.Meta):
        model = TransactionAttributeType
        fields = AbstractAttributeTypeSerializer.Meta.fields + ['classifiers']


# class TransactionAttributeTypeBulkObjectPermissionSerializer(AbstractBulkObjectPermissionSerializer):
#     content_objects = TransactionAttributeTypeField(many=True, allow_null=False, allow_empty=False)
#
#     class Meta:
#         model = TransactionAttributeType


class TransactionAttributeSerializer(AbstractAttributeSerializer):
    attribute_type = TransactionAttributeTypeField()
    classifier = TransactionClassifierField(required=False, allow_null=True)

    class Meta(AbstractAttributeSerializer.Meta):
        model = TransactionAttribute
        fields = AbstractAttributeSerializer.Meta.fields + ['attribute_type', 'classifier']


class TransactionSerializer(ModelWithAttributesSerializer):
    master_user = MasterUserField()
    transaction_class_object = ReadonlyNamedModelSerializer(source='transaction_class')
    complex_transaction = serializers.PrimaryKeyRelatedField(read_only=True)
    complex_transaction_order = serializers.IntegerField(read_only=True)
    portfolio = PortfolioField(default=PortfolioDefault())
    portfolio_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='portfolio')
    transaction_currency = CurrencyField(default=CurrencyDefault(), required=False, allow_null=True)
    transaction_currency_object = ReadonlyNamedModelSerializer(source='transaction_currency')
    instrument = InstrumentField(required=False, allow_null=True)
    instrument_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='instrument')
    settlement_currency = CurrencyField(default=CurrencyDefault())
    settlement_currency_object = ReadonlyNamedModelSerializer(source='settlement_currency')
    account_cash = AccountField(default=AccountDefault())
    account_cash_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='account_cash')
    account_position = AccountField(default=AccountDefault())
    account_position_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='account_position')
    account_interim = AccountField(default=AccountDefault())
    account_interim_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='account_interim')
    strategy1_position = Strategy1Field(default=Strategy1Default())
    strategy1_position_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='strategy1_position')
    strategy1_cash = Strategy1Field(default=Strategy1Default())
    strategy1_cash_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='strategy1_cash')
    strategy2_position = Strategy2Field(default=Strategy2Default())
    strategy2_position_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='strategy2_position')
    strategy2_cash = Strategy2Field(default=Strategy2Default())
    strategy2_cash_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='strategy2_cash')
    strategy3_position = Strategy3Field(default=Strategy3Default())
    strategy3_position_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='strategy3_position')
    strategy3_cash = Strategy3Field(default=Strategy3Default())
    strategy3_cash_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='strategy3_cash')
    responsible = ResponsibleField(default=ResponsibleDefault())
    responsible_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='responsible')
    counterparty = CounterpartyField(default=CounterpartyDefault())
    counterparty_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='counterparty')
    attributes = TransactionAttributeSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = Transaction
        fields = [
            'url', 'id', 'master_user',
            'transaction_code',
            'complex_transaction', 'complex_transaction_order',
            'transaction_class', 'transaction_class_object',
            'portfolio', 'portfolio_object',
            'transaction_currency', 'transaction_currency_object', 'instrument', 'instrument_object',
            'position_size_with_sign',
            'settlement_currency', 'settlement_currency_object',
            'cash_consideration', 'principal_with_sign', 'carry_with_sign', 'overheads_with_sign',
            'accounting_date', 'cash_date', 'transaction_date',
            'account_cash', 'account_cash_object', 'account_position', 'account_position_object',
            'account_interim', 'account_interim_object',
            'strategy1_position', 'strategy1_position_object', 'strategy1_cash', 'strategy1_cash_object',
            'strategy2_position', 'strategy2_position_object', 'strategy2_cash', 'strategy2_cash_object',
            'strategy3_position', 'strategy3_position_object', 'strategy3_cash', 'strategy3_cash_object',
            'reference_fx_rate',
            'is_locked', 'is_canceled',
            'factor', 'trade_price',
            'principal_amount', 'carry_amount', 'overheads',
            'responsible', 'responsible_object', 'counterparty', 'counterparty_object',
            'attributes'
        ]


class ComplexTransactionSerializer(serializers.ModelSerializer):
    transaction_type = serializers.PrimaryKeyRelatedField(read_only=True)
    transaction_type__object = ReadonlyNamedModelWithObjectPermissionSerializer(source='transaction_type')
    transactions = serializers.PrimaryKeyRelatedField(read_only=True, many=True)
    text = serializers.SerializerMethodField()

    class Meta:
        model = ComplexTransaction
        fields = [
            'url', 'id', 'code', 'transaction_type', 'transaction_type__object', 'transactions', 'text',
        ]

    def get_text(self, obj):
        from poms.transactions.renderer import ComplexTransactionRenderer
        renderer = ComplexTransactionRenderer()
        return renderer.render(complex_transaction=obj, context=self.context)


# TransactionType processing


class TransactionTypeProcessValues(object):
    def __init__(self, parent=None, **kwargs):
        self._parent = parent
        # for key, value in kwargs.items():
        #     # TODO: validate attr_name
        #     setattr(self, key, value)
        self._parent.set_default_values(self)


class TransactionTypeProcess(object):
    def __init__(self, transaction_type=None, calculate=True, store=False, values=None, has_errors=False,
                 instruments=None, instruments_errors=None, transactions=None, transactions_errors=None):
        self.transaction_type = transaction_type
        self.transaction_type_inputs = list(self.transaction_type.inputs.order_by('value_type', 'name').all())

        self.calculate = calculate or False
        self.store = store or False
        self.values = values or TransactionTypeProcessValues(self)
        self.has_errors = has_errors
        self.instruments = instruments or []
        self.instruments_errors = instruments_errors or []
        self.transactions = transactions or []
        self.transactions_errors = transactions_errors or []

    def get_attr_name(self, input0):
        return '%s_%s' % (input0.id, input0.name)

    def get_input_name(self, attr_name):
        try:
            id, name = attr_name.split('_', maxsplit=2)
            return name
        except ValueError:
            return None

    def set_default_values(self, target):
        for i in self.transaction_type_inputs:
            name = self.get_attr_name(i)
            if i.value_type == TransactionTypeInput.RELATION:
                model_class = i.content_type.model_class()
                if issubclass(model_class, Account):
                    value = i.account
                elif issubclass(model_class, Currency):
                    value = i.currency
                elif issubclass(model_class, Instrument):
                    value = i.instrument
                elif issubclass(model_class, InstrumentType):
                    value = i.instrument_type
                elif issubclass(model_class, Counterparty):
                    value = i.counterparty
                elif issubclass(model_class, Responsible):
                    value = i.responsible
                elif issubclass(model_class, Strategy1):
                    value = i.strategy1
                elif issubclass(model_class, Strategy2):
                    value = i.strategy2
                elif issubclass(model_class, Strategy3):
                    value = i.strategy3
                elif issubclass(model_class, DailyPricingModel):
                    value = i.daily_pricing_model
                elif issubclass(model_class, PaymentSizeDetail):
                    value = i.payment_size_detail
                elif issubclass(model_class, Portfolio):
                    value = i.portfolio
                elif issubclass(model_class, PriceDownloadScheme):
                    value = i.price_download_scheme
                else:
                    value = None
                setattr(target, name, value)
            else:
                value = i.value
                if value:
                    try:
                        value = formula.safe_eval(value)
                    except formula.InvalidExpression:
                        value = None
                else:
                    value = None
                setattr(target, name, value)


class TransactionTypeProcessValuesSerializer(serializers.Serializer):
    def __init__(self, **kwargs):
        super(TransactionTypeProcessValuesSerializer, self).__init__(**kwargs)

        ttp = self.instance._parent
        transaction_type_inputs = ttp.transaction_type_inputs
        for i in transaction_type_inputs:
            # name = '%s_%s' % (i.id, i.name)
            name = ttp.get_attr_name(i)
            name_object = '%s_object' % name
            field = None
            field_object = None
            if i.value_type == TransactionTypeInput.STRING:
                field = serializers.CharField(required=True, label=i.name, help_text=i.verbose_name)
            elif i.value_type == TransactionTypeInput.NUMBER:
                field = serializers.FloatField(required=True, label=i.name, help_text=i.verbose_name)
            elif i.value_type == TransactionTypeInput.DATE:
                field = serializers.DateField(required=True, label=i.name, help_text=i.verbose_name)
            elif i.value_type == TransactionTypeInput.RELATION:
                model_class = i.content_type.model_class()
                if issubclass(model_class, Account):
                    field = AccountField(required=True, label=i.name, help_text=i.verbose_name)
                    field_object = ReadonlyNamedModelWithObjectPermissionSerializer(source=name)
                elif issubclass(model_class, Currency):
                    field = CurrencyField(required=True, label=i.name, help_text=i.verbose_name)
                    field_object = ReadonlyNamedModelSerializer(source=name)
                elif issubclass(model_class, Instrument):
                    field = InstrumentField(required=True, label=i.name, help_text=i.verbose_name)
                    field_object = ReadonlyNamedModelWithObjectPermissionSerializer(source=name)
                elif issubclass(model_class, InstrumentType):
                    field = InstrumentTypeField(required=True, label=i.name, help_text=i.verbose_name)
                    field_object = ReadonlyNamedModelWithObjectPermissionSerializer(source=name)
                elif issubclass(model_class, Counterparty):
                    field = CounterpartyField(required=True, label=i.name, help_text=i.verbose_name)
                    field_object = ReadonlyNamedModelWithObjectPermissionSerializer(source=name)
                elif issubclass(model_class, Responsible):
                    field = ResponsibleField(required=True, label=i.name, help_text=i.verbose_name)
                    field_object = ReadonlyNamedModelWithObjectPermissionSerializer(source=name)
                elif issubclass(model_class, Strategy1):
                    field = Strategy1Field(required=True, label=i.name, help_text=i.verbose_name)
                    field_object = ReadonlyNamedModelWithObjectPermissionSerializer(source=name)
                elif issubclass(model_class, Strategy2):
                    field = Strategy2Field(required=True, label=i.name, help_text=i.verbose_name)
                    field_object = ReadonlyNamedModelWithObjectPermissionSerializer(source=name)
                elif issubclass(model_class, Strategy3):
                    field = Strategy3Field(required=True, label=i.name, help_text=i.verbose_name)
                    field_object = ReadonlyNamedModelWithObjectPermissionSerializer(source=name)
                elif issubclass(model_class, DailyPricingModel):
                    field = serializers.PrimaryKeyRelatedField(queryset=DailyPricingModel.objects, required=True,
                                                               label=i.name, help_text=i.verbose_name)
                    field_object = ReadonlyModelWithNameSerializer(source=name)
                elif issubclass(model_class, PaymentSizeDetail):
                    field = serializers.PrimaryKeyRelatedField(queryset=PaymentSizeDetail.objects, required=True,
                                                               label=i.name, help_text=i.verbose_name)
                    field_object = ReadonlyModelWithNameSerializer(source=name)
                elif issubclass(model_class, Portfolio):
                    field = PortfolioField(required=True, label=i.name, help_text=i.verbose_name)
                    field_object = ReadonlyNamedModelWithObjectPermissionSerializer(source=name)
                elif issubclass(model_class, PriceDownloadScheme):
                    field = PriceDownloadSchemeField(required=True, label=i.name, help_text=i.verbose_name)
                    field_object = ReadonlyNamedModelWithObjectPermissionSerializer(source=name)
            if field:
                self.fields[name] = field
                if field_object:
                    self.fields[name_object] = field_object
            else:
                raise RuntimeError('Unknown value type %s' % i.value_type)


class PhantomInstrumentSerializer(InstrumentSerializer):
    def __init__(self, **kwargs):
        super(PhantomInstrumentSerializer, self).__init__(**kwargs)
        self.fields['id'] = serializers.IntegerField(required=True)
        self.fields.pop('manual_pricing_formulas')
        self.fields.pop('accrual_calculation_schedules')
        self.fields.pop('factor_schedules')
        self.fields.pop('event_schedules')
        self.fields.pop('attributes')
        self.fields.pop('tags')
        self.fields.pop('user_object_permissions')
        self.fields.pop('group_object_permissions')


class PhantomInstrumentField(InstrumentField):
    def to_internal_value(self, data):
        pk = data
        if self.pk_field is not None:
            pk = self.pk_field.to_internal_value(data)
        if pk and pk < 0:
            return Instrument(id=pk)
        return super(PhantomInstrumentField, self).to_internal_value(data)


class PhantomTransactionSerializer(TransactionSerializer):
    def __init__(self, **kwargs):
        super(PhantomTransactionSerializer, self).__init__(**kwargs)
        self.fields['instrument'] = PhantomInstrumentField(required=False)
        self.fields.pop('attributes')


class TransactionTypeProcessSerializer(serializers.Serializer):
    def __init__(self, **kwargs):
        kwargs['context'] = context = kwargs.get('context', {}) or {}
        super(TransactionTypeProcessSerializer, self).__init__(**kwargs)
        context['instance'] = self.instance

        self.fields['transaction_type'] = serializers.PrimaryKeyRelatedField(read_only=True)
        self.fields['calculate'] = serializers.BooleanField(default=False, required=False)
        self.fields['store'] = serializers.BooleanField(default=False, required=False)
        self.fields['values'] = TransactionTypeProcessValuesSerializer(instance=self.instance.values)
        self.fields['has_errors'] = serializers.BooleanField(read_only=True)
        self.fields['instruments_errors'] = serializers.ReadOnlyField()
        self.fields['transactions_errors'] = serializers.ReadOnlyField()
        self.fields['instruments'] = PhantomInstrumentSerializer(many=True, read_only=False)
        self.fields['transactions'] = PhantomTransactionSerializer(many=True, read_only=False)

    def create(self, validated_data):
        return validated_data

    def update(self, instance, validated_data):
        values_data = validated_data.pop('values')

        for key, value in validated_data.items():
            setattr(instance, key, value)

        input_values = {}
        values = instance.values
        for key, value in values_data.items():
            setattr(values, key, value)

            name = instance.get_input_name(key)
            if name:
                input_values[name] = value

        if instance.calculate:
            processor = TransactionTypeProcessor(instance.transaction_type, input_values)
            processor.run(False)

            instance.has_errors = processor.has_errors
            instance.instruments_errors = processor.instruments_errors
            instance.instruments = processor.instruments
            instance.transactions_errors = processor.transactions_errors
            instance.transactions = processor.transactions

            if instance.store and not instance.has_errors:
                instruments_map = {}
                for instrument in instance.instruments:
                    fake_id = instrument.id
                    instrument.id = None
                    instrument.save()
                    if fake_id:
                        instruments_map[fake_id] = instrument
                if instance.transactions:
                    instance.complex_transaction.id = None
                    instance.complex_transaction.save()
                    # complex_transaction = ComplexTransaction.objects.create(transaction_type=instance.transaction_type)
                    for transaction in instance.transactions:
                        transaction.id = None
                        # transaction.complex_transaction = complex_transaction
                        if transaction.instrument_id in instruments_map:
                            transaction.instrument = instruments_map[transaction.instrument_id]
                        transaction.save()
        else:
            if instance.store:
                instruments_map = {}
                instruments_data = validated_data['instruments']
                if instruments_data:
                    instruments = []
                    for instrument_data in instruments_data:
                        fake_id = instrument_data.pop('id', None)
                        instrument = Instrument(master_user=instance.transaction_type.master_user)
                        for attr, value in instrument_data.items():
                            if attr in ['id']:
                                continue
                            setattr(instrument, attr, value)
                        instrument.save()
                        instruments.append(instrument)
                        if fake_id:
                            instruments_map[fake_id] = instrument
                    instance.instruments = instruments

                transactions_data = validated_data['transactions']
                if transactions_data:
                    transactions = []
                    complex_transaction = ComplexTransaction.objects.create(transaction_type=instance.transaction_type)
                    for transaction_data in transactions_data:
                        transaction = Transaction(master_user=instance.transaction_type.master_user)
                        for attr, value in transaction_data.items():
                            if attr in ['id']:
                                continue
                            if attr == 'instrument':
                                value = value.id
                                if value in instruments_map:
                                    value = instruments_map[value]
                            setattr(transaction, attr, value)
                        transaction.complex_transaction = complex_transaction
                        transaction.save()
                        transactions.append(transaction)
                    instance.transactions = transactions

        return instance
