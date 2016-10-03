import json
import logging

from django.utils.translation import ugettext_lazy

from poms.common import formula
from poms.transactions.serializers import TransactionSerializer

_l = logging.getLogger('poms.transactions.renderer')


class ComplexTransactionRenderer(object):
    def __init__(self, ):
        pass

    def render(self, complex_transaction, context):
        transaction_serializer = TransactionSerializer(instance=complex_transaction.transactions.all(), many=True,
                                                       context=context)
        transactions = transaction_serializer.data

        # update foreign object value from *_object item
        for transaction in transactions:
            for key, value in transaction.items():
                if key.endswith('_object'):
                    tkey = key[:-7]
                    transaction[tkey] = value

        transaction_type = complex_transaction.transaction_type
        display_expr = transaction_type.display_expr
        if display_expr:
            try:
                ret = formula.safe_eval(display_expr, names={
                    'transactions': transactions
                })
                return str(ret)
            except formula.InvalidExpression:
                _l.debug('Invalid display expression: transaction_type=%s, display_expr="%s"',
                         transaction_type.id, transaction_type.display_expr,
                         exc_info=True)
                return ugettext_lazy('Invalid transaction type display expression.')
        return ugettext_lazy('Empty transaction type display expression.')
