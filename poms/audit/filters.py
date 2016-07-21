import django_filters
from django.contrib.contenttypes.models import ContentType
from rest_framework.filters import BaseFilterBackend

from poms.accounts.models import Account, AccountType, AccountAttributeType
from poms.chats.models import ThreadGroup, Thread, Message, DirectMessage
from poms.counterparties.models import Counterparty, CounterpartyAttributeType, Responsible, ResponsibleAttributeType
from poms.currencies.models import Currency, CurrencyHistory
from poms.instruments.models import Instrument, InstrumentType, InstrumentAttributeType, PriceHistory
from poms.portfolios.models import Portfolio, PortfolioAttributeType
from poms.strategies.models import Strategy1, Strategy2, Strategy3
from poms.transactions.models import TransactionType, Transaction, TransactionAttributeType
from poms.users.models import MasterUser, Member


class HistoryFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        master_user = request.user.master_user
        return queryset.filter(info__master_user=master_user)


class ObjectHistoryContentTypeFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        models = [
            AccountType, Account, AccountAttributeType,
            ThreadGroup, Thread, Message, DirectMessage,
            Counterparty, CounterpartyAttributeType, Responsible, ResponsibleAttributeType,
            Currency, CurrencyHistory,
            InstrumentType, Instrument, InstrumentAttributeType, PriceHistory,
            Portfolio, PortfolioAttributeType,
            Strategy1, Strategy2, Strategy3,
            TransactionType, Transaction, TransactionAttributeType,
            MasterUser, Member
        ]
        ctypes = [ContentType.objects.get_for_model(model).pk for model in models]
        return queryset.filter(pk__in=ctypes)


class ObjectHistoryContentTypeMultipleChoiceFilter(django_filters.MultipleChoiceFilter):
    def __init__(self, *args, **kwargs):
        queryset = ContentType.objects.all().order_by('app_label', 'model')
        queryset = ObjectHistoryContentTypeFilter().filter_queryset(None, queryset, None)
        kwargs['choices'] = [
            ('%s.%s' % (c.app_label, c.model), c.model_class()._meta.verbose_name)
            for c in queryset
            ]
        super(ObjectHistoryContentTypeMultipleChoiceFilter, self).__init__(*args, **kwargs)

    def filter(self, qs, value):
        value = value or tuple()
        cvalue = []
        for v in value:
            ctype = v.split('.')
            ctype = ContentType.objects.get_by_natural_key(*ctype)
            cvalue.append(ctype.id)
        return super(ObjectHistoryContentTypeMultipleChoiceFilter, self).filter(qs, cvalue)
