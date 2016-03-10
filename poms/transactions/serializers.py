from __future__ import unicode_literals

from rest_framework import serializers

from poms.transactions.models import TransactionClass, Transaction


class TransactionClassSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='transactionclass-detail')

    class Meta:
        model = TransactionClass
        fields = ['url', 'id', 'code', 'name', 'description']


class TransactionSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='transaction-detail')

    class Meta:
        model = Transaction
        fields = ['url', 'id', 'portfolio', 'transaction_class',
                  'instrument', 'transaction_currency',
                  'position_size_with_sign',
                  'settlement_currency','cash_consideration',
                  'principal_with_sign', 'carry_with_sign', 'overheads_with_sign',
                  'accounting_date', 'cash_date', 'transaction_date',
                  'account_cash', 'account_position', 'account_interim',
                  'reference_fx_rate',
                  'is_locked', 'is_canceled', 'factor', 'trade_price',
                  'principal_amount', 'carry_amount', 'overheads',
                  'notes_front_office', 'notes_middle_office',
                  'responsible', 'responsible_text',
                  'counterparty', 'counterparty_text']

