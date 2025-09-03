import django_filters
from django.contrib.contenttypes.models import ContentType

from poms.accounts.models import Account, AccountType
from poms.counterparties.models import Counterparty, CounterpartyGroup, Responsible, ResponsibleGroup
from poms.currencies.models import Currency, CurrencyHistory
from poms.instruments.models import Instrument, InstrumentType, PriceHistory
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
from poms.transactions.models import TransactionType, TransactionTypeGroup


def get_scheme_content_types():
    models = [
        AccountType,
        Account,
        Currency,
        InstrumentType,
        Instrument,
        Portfolio,
        CounterpartyGroup,
        Counterparty,
        ResponsibleGroup,
        Responsible,
        Strategy1Group,
        Strategy1Subgroup,
        Strategy1,
        Strategy2Group,
        Strategy2Subgroup,
        Strategy2,
        Strategy3Group,
        Strategy3Subgroup,
        Strategy3,
        PriceHistory,
        CurrencyHistory,
        TransactionTypeGroup,
        TransactionType,
    ]
    return [ContentType.objects.get_for_model(model).pk for model in models]


def scheme_content_type_choices():
    queryset = ContentType.objects.all().order_by("app_label", "model").filter(pk__in=get_scheme_content_types())
    for c in queryset:
        yield f"{c.app_label}.{c.model}", c.model_class()._meta.verbose_name


class SchemeContentTypeFilter(django_filters.MultipleChoiceFilter):
    def __init__(self, *args, **kwargs):
        kwargs["choices"] = scheme_content_type_choices
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        value = value or tuple()
        cvalue = []
        for v in value:
            ctype = v.split(".")
            ctype = ContentType.objects.get_by_natural_key(*ctype)
            cvalue.append(ctype.id)
        return super().filter(qs, cvalue)
