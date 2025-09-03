from django.contrib.contenttypes.models import ContentType
from rest_framework.filters import BaseFilterBackend

from poms.portfolios.models import (
    PortfolioHistory,
    PortfolioReconcileGroup,
    PortfolioReconcileHistory,
    PortfolioRegister,
    PortfolioRegisterRecord,
    PortfolioType,
)
from poms.pricing.models import CurrencyHistoryError, PriceHistoryError
from poms.reports.models import (
    BalanceReport,
    CashFlowReport,
    PerformanceReport,
    PLReport,
    TransactionReport,
)


class LayoutContentTypeFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        from poms.accounts.models import Account, AccountType
        from poms.counterparties.models import (
            Counterparty,
            CounterpartyGroup,
            Responsible,
            ResponsibleGroup,
        )
        from poms.csv_import.models import CsvImportScheme
        from poms.currencies.models import Currency, CurrencyHistory
        from poms.instruments.models import (
            GeneratedEvent,
            Instrument,
            InstrumentType,
            PriceHistory,
            PricingPolicy,
        )
        from poms.integrations.models import ComplexTransactionImportScheme
        from poms.portfolios.models import Portfolio
        from poms.strategies.models import (
            Strategy1,
            Strategy1Group,
            Strategy1Subgroup,
            Strategy2,
            Strategy2Group,
            Strategy2Subgroup,
            Strategy3,
            Strategy3Group,
            Strategy3Subgroup,
        )
        from poms.transactions.models import (
            ComplexTransaction,
            Transaction,
            TransactionType,
            TransactionTypeGroup,
        )
        from poms.ui.models import Dashboard

        models = [
            AccountType,
            Account,
            Currency,
            InstrumentType,
            Instrument,
            PriceHistory,
            CurrencyHistory,
            PriceHistoryError,
            CurrencyHistoryError,
            PricingPolicy,
            CounterpartyGroup,
            Counterparty,
            Responsible,
            ResponsibleGroup,
            PortfolioType,
            PortfolioReconcileHistory,
            PortfolioReconcileGroup,
            Portfolio,
            PortfolioRegister,
            PortfolioRegisterRecord,
            PortfolioHistory,
            TransactionTypeGroup,
            TransactionType,
            Transaction,
            ComplexTransaction,
            Strategy1Group,
            Strategy1Subgroup,
            Strategy1,
            Strategy2Group,
            Strategy2Subgroup,
            Strategy2,
            Strategy3Group,
            Strategy3Subgroup,
            Strategy3,
            BalanceReport,
            PLReport,
            PerformanceReport,
            CashFlowReport,
            TransactionReport,
            Dashboard,
            GeneratedEvent,
            ComplexTransactionImportScheme,
            CsvImportScheme,
        ]
        ctypes = [ContentType.objects.get_for_model(model).pk for model in models]
        return queryset.filter(pk__in=ctypes).order_by("model")


class MyLayoutFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(mamber=request.user.member)
