from __future__ import unicode_literals

from rest_framework import serializers

from poms.accounts.fields import AccountTypeField, AccountField
from poms.counterparties.fields import CounterpartyField, ResponsibleField
from poms.currencies.fields import CurrencyField
from poms.instruments.fields import InstrumentTypeField, InstrumentField
from poms.portfolios.fields import PortfolioField
from poms.strategies.fields import StrategyField
from poms.tags.fields import TagContentTypeField
from poms.tags.models import Tag
from poms.transactions.fields import TransactionTypeField
from poms.users.fields import MasterUserField


class TagSerializer(serializers.ModelSerializer):
    master_user = MasterUserField()
    content_types = TagContentTypeField(many=True)
    account_types = AccountTypeField(many=True)
    accounts = AccountField(many=True)
    currencies = CurrencyField(many=True)
    instrument_types = InstrumentTypeField(many=True)
    instruments = InstrumentField(many=True)
    counterparties = CounterpartyField(many=True)
    responsibles = ResponsibleField(many=True)
    strategies = StrategyField(many=True)
    portfolios = PortfolioField(many=True)
    transaction_types = TransactionTypeField(many=True)

    class Meta:
        model = Tag
        fields = ['url', 'id', 'master_user', 'user_code', 'name', 'short_name', 'notes',
                  'content_types', 'account_types', 'accounts', 'currencies', 'instrument_types', 'instruments',
                  'counterparties', 'responsibles', 'strategies', 'portfolios', 'transaction_types']
