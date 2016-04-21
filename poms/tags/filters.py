from django.contrib.contenttypes.models import ContentType
from rest_framework.filters import BaseFilterBackend


class TagContentTypeFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        from poms.accounts.models import AccountType
        from poms.accounts.models import Account
        from poms.currencies.models import Currency
        from poms.instruments.models import InstrumentType
        from poms.instruments.models import Instrument
        from poms.counterparties.models import Counterparty
        from poms.counterparties.models import Responsible
        from poms.strategies.models import Strategy
        from poms.portfolios.models import Portfolio
        from poms.transactions.models import TransactionType

        models = [AccountType, Account, Currency, InstrumentType, Instrument, Counterparty, Responsible, Strategy,
                  Portfolio, TransactionType]
        ctypes = [ContentType.objects.get_for_model(model).pk for model in models]
        return queryset.filter(pk__in=ctypes)
