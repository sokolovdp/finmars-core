import json
import logging

from django.utils.translation import ugettext_lazy

from poms.common import formula
from poms.instruments.serializers import InstrumentSerializer
from poms.transactions.serializers import TransactionSerializer

_l = logging.getLogger('poms.transactions.renderer')


class RenderingInstrumentSerializer(InstrumentSerializer):
    def __init__(self, **kwargs):
        super(RenderingInstrumentSerializer, self).__init__(**kwargs)
        self.fields.pop('manual_pricing_formulas')
        self.fields.pop('accrual_calculation_schedules')
        self.fields.pop('factor_schedules')
        self.fields.pop('event_schedules')
        self.fields.pop('granted_permissions')
        self.fields.pop('user_object_permissions')
        self.fields.pop('group_object_permissions')


class RenderingTransactionSerializer(TransactionSerializer):
    def __init__(self, **kwargs):
        super(RenderingTransactionSerializer, self).__init__(**kwargs)


class ComplexTransactionRenderer(object):
    def __init__(self, ):
        pass

    def render(self, complex_transaction, context):
        transactions = list(complex_transaction.transactions.all())

        transaction_serializer = RenderingTransactionSerializer(instance=transactions, many=True, context=context)
        transactions_data = transaction_serializer.data

        instruments_data = {}
        for transaction in complex_transaction.transactions.all():
            instrument = transaction.instrument
            if instrument.id not in instruments_data:
                instrument_serializer = RenderingInstrumentSerializer(instance=instrument, context=context)
                instruments_data[instrument.id] = instrument_serializer.data

        for transaction_data in transactions_data:
            for key, value in transaction_data.items():
                if key == 'instrument':
                    transaction_data['instrument'] = instruments_data[value]
                    transaction_data['instrument_object'] = instruments_data[value]
                if key == 'instrument_object':
                    pass
                elif key.endswith('_object'):
                    tkey = key[:-7]
                    transaction_data[tkey] = value

        _l.info(json.dumps(transactions_data, indent=4))

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
