import json
import logging
from collections import OrderedDict

from django.utils.translation import ugettext_lazy

from poms.accounts.serializers import AccountSerializer, AccountTypeSerializer
from poms.common import formula
from poms.counterparties.serializers import ResponsibleSerializer, CounterpartySerializer
from poms.currencies.serializers import CurrencySerializer
from poms.instruments.serializers import InstrumentSerializer, InstrumentTypeSerializer
from poms.portfolios.serializers import PortfolioSerializer
from poms.strategies.serializers import Strategy1GroupSerializer, Strategy1SubgroupSerializer, Strategy1Serializer, \
    Strategy2GroupSerializer, Strategy2SubgroupSerializer, Strategy2Serializer, Strategy3GroupSerializer, \
    Strategy3SubgroupSerializer, Strategy3Serializer
from poms.transactions.serializers import TransactionSerializer

_l = logging.getLogger('poms.transactions.renderer')


class RenderingAccountTypeSerializer(AccountTypeSerializer):
    pass


class RenderingAccountSerializer(AccountSerializer):
    type_object = RenderingAccountTypeSerializer(source='type')
    pass


class RenderingCurrencySerializer(CurrencySerializer):
    pass


class RenderingInstrumentTypeSerializer(InstrumentTypeSerializer):
    pass


class RenderingInstrumentSerializer(InstrumentSerializer):
    instrument_type_object = RenderingInstrumentTypeSerializer(source='instrument_type')
    pricing_currency_object = RenderingCurrencySerializer(source='pricing_currency')
    accrued_currency_object = RenderingCurrencySerializer(source='accrued_currency')

    # attributes = InstrumentAttributeSerializer(many=True, required=False, allow_null=True)
    # tags = TagField(many=True, required=False, allow_null=True)
    # tags_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='tags', many=True)

    def __init__(self, **kwargs):
        super(RenderingInstrumentSerializer, self).__init__(**kwargs)


class RenderingPortfolioSerializer(PortfolioSerializer):
    pass


class RenderingStrategy1GroupSerializer(Strategy1GroupSerializer):
    pass


class RenderingStrategy1SubgroupSerializer(Strategy1SubgroupSerializer):
    group_object = RenderingStrategy1GroupSerializer(source='group')
    pass


class RenderingStrategy1Serializer(Strategy1Serializer):
    subgroup_object = RenderingStrategy1SubgroupSerializer(source='subgroup')
    pass


class RenderingStrategy2GroupSerializer(Strategy2GroupSerializer):
    pass


class RenderingStrategy2SubgroupSerializer(Strategy2SubgroupSerializer):
    group_object = RenderingStrategy2GroupSerializer(source='group')
    pass


class RenderingStrategy2Serializer(Strategy2Serializer):
    subgroup_object = RenderingStrategy2SubgroupSerializer(source='subgroup')
    pass


class RenderingStrategy3GroupSerializer(Strategy3GroupSerializer):
    pass


class RenderingStrategy3SubgroupSerializer(Strategy3SubgroupSerializer):
    group_object = RenderingStrategy3GroupSerializer(source='group')
    pass


class RenderingStrategy3Serializer(Strategy3Serializer):
    subgroup_object = RenderingStrategy3SubgroupSerializer(source='subgroup')
    pass


class RenderingResponsibleSerializer(ResponsibleSerializer):
    pass


class RenderingCounterpartySerializer(CounterpartySerializer):
    pass


class RenderingTransactionSerializer(TransactionSerializer):
    portfolio_object = RenderingPortfolioSerializer(source='portfolio')
    instrument_object = RenderingInstrumentSerializer(source='instrument')
    transaction_currency_object = RenderingCurrencySerializer(source='transaction_currency')
    settlement_currency_object = RenderingCurrencySerializer(source='settlement_currency')
    account_cash_object = RenderingAccountSerializer(source='account_cash')
    account_position_object = RenderingAccountSerializer(source='account_position')
    account_interim_object = RenderingAccountSerializer(source='account_interim')
    strategy1_position_object = RenderingStrategy1Serializer(source='strategy1_position')
    strategy1_cash_object = RenderingStrategy1Serializer(source='strategy1_cash')
    strategy2_position_object = RenderingStrategy2Serializer(source='strategy2_position')
    strategy2_cash_object = RenderingStrategy2Serializer(source='strategy2_cash')
    strategy3_position_object = RenderingStrategy3Serializer(source='strategy3_position')
    strategy3_cash_object = RenderingStrategy3Serializer(source='strategy3_cash')
    responsible_object = RenderingResponsibleSerializer(source='responsible')
    counterparty_object = RenderingCounterpartySerializer(source='counterparty')

    def __init__(self, **kwargs):
        super(RenderingTransactionSerializer, self).__init__(**kwargs)


class ComplexTransactionRenderer(object):
    def __init__(self, ):
        pass

    def render(self, complex_transaction, context):
        transactions = list(complex_transaction.transactions.all())

        transaction_serializer = RenderingTransactionSerializer(instance=transactions, many=True, context=context)
        transactions_data = transaction_serializer.data

        transactions_data = self._process_object(transactions_data)

        # instruments_data = {}
        # for transaction in complex_transaction.transactions.all():
        #     instrument = transaction.instrument
        #     if instrument.id not in instruments_data:
        #         instrument_serializer = RenderingInstrumentSerializer(instance=instrument, context=context)
        #         instruments_data[instrument.id] = instrument_serializer.data
        #
        # for transaction_data in transactions_data:
        #     for key, value in transaction_data.items():
        #         if key == 'instrument':
        #             transaction_data['instrument'] = instruments_data[value]
        #             transaction_data['instrument_object'] = instruments_data[value]
        #         if key == 'instrument_object':
        #             pass
        #         elif key.endswith('_object'):
        #             tkey = key[:-7]
        #             transaction_data[tkey] = value

        # _l.info(json.dumps(transactions_data, indent=4))

        transaction_type = complex_transaction.transaction_type
        display_expr = transaction_type.display_expr
        if display_expr:
            try:
                ret = formula.safe_eval(display_expr, names={
                    'code': complex_transaction.code,
                    'transactions': transactions_data,
                })
                return str(ret)
            except formula.InvalidExpression:
                _l.debug('Invalid display expression: transaction_type=%s, display_expr="%s"',
                         transaction_type.id, transaction_type.display_expr,
                         exc_info=True)
                return ugettext_lazy('Invalid transaction type display expression.')
        return ugettext_lazy('Empty transaction type display expression.')

    def _process_object(self, data):
        if isinstance(data, (list, tuple)):
            ret = []
            for value in data:
                ret.append(self._process_object(value))
            return ret
        elif isinstance(data, (dict, OrderedDict)):
            ret = OrderedDict()
            skip = set()
            for key, value in data.items():
                if key.endswith('_object'):
                    tkey = key[:-7]
                    skip.add(tkey)
                    value = self._process_object(value)
                    ret[tkey] = value
                    # ret[key] = value
                    ret.pop(key, None)
                elif key not in skip:
                    ret[key] = self._process_object(value)
            return ret
        else:
            return data
