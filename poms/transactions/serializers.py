from __future__ import unicode_literals

from rest_framework import serializers

from poms.accounts.serializers import AccountField
from poms.counterparties.serializers import CounterpartyField, ResponsibleField
from poms.currencies.serializers import CurrencyField
from poms.instruments.serializers import InstrumentField
from poms.portfolios.serializers import PortfolioField
from poms.transactions.models import TransactionClass, Transaction


class TransactionClassSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='transactionclass-detail')

    class Meta:
        model = TransactionClass
        fields = ['url', 'id', 'code', 'name', 'description']


class TransactionSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='transaction-detail')
    portfolio = PortfolioField(required=False, allow_null=True)
    transaction_currency = CurrencyField(required=False, allow_null=True)
    instrument = InstrumentField(required=False, allow_null=True)
    settlement_currency = CurrencyField(required=False, allow_null=True)
    account_cash = AccountField(required=False, allow_null=True)
    account_position = AccountField(required=False, allow_null=True)
    account_interim = AccountField(required=False, allow_null=True)
    responsible = ResponsibleField(required=False, allow_null=True)
    counterparty = CounterpartyField(required=False, allow_null=True)

    class Meta:
        model = Transaction
        fields = ['url', 'id', 'portfolio', 'transaction_class',
                  'transaction_currency', 'instrument',
                  'position_size_with_sign',
                  'settlement_currency', 'cash_consideration',
                  'principal_with_sign', 'carry_with_sign', 'overheads_with_sign',
                  'accounting_date', 'cash_date', 'transaction_date',
                  'account_cash', 'account_position', 'account_interim',
                  'reference_fx_rate',
                  'is_locked', 'is_canceled', 'factor', 'trade_price',
                  'principal_amount', 'carry_amount', 'overheads',
                  'notes_front_office', 'notes_middle_office',
                  'responsible', 'responsible_text',
                  'counterparty', 'counterparty_text']
