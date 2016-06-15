from django.contrib.contenttypes.models import ContentType
from rest_framework.filters import BaseFilterBackend


class LayoutContentTypeFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        from poms.accounts.models import AccountType
        from poms.accounts.models import Account
        from poms.currencies.models import Currency, CurrencyHistory
        from poms.instruments.models import InstrumentType, Instrument, PriceHistory, PricingPolicy
        from poms.counterparties.models import Counterparty
        from poms.counterparties.models import Responsible
        from poms.strategies.models import Strategy1, Strategy2, Strategy3
        from poms.portfolios.models import Portfolio
        from poms.transactions.models import TransactionType, Transaction

        models = [AccountType, Account, Currency, CurrencyHistory, InstrumentType, Instrument, PriceHistory,
                  PricingPolicy, Counterparty, Responsible, Portfolio, TransactionType, Transaction,
                  Strategy1, Strategy2, Strategy3, ]
        ctypes = [ContentType.objects.get_for_model(model).pk for model in models]
        return queryset.filter(pk__in=ctypes).order_by('model')


class MyLayoutFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(mamber=request.user.member)
