from functools import partial

import django_filters
from django.contrib.contenttypes.models import ContentType
from rest_framework.filters import BaseFilterBackend

from poms.accounts.models import Account
from poms.accounts.models import AccountType
from poms.chats.models import ThreadGroup, Thread
from poms.common.middleware import get_request
from poms.counterparties.models import Counterparty
from poms.counterparties.models import Responsible
from poms.currencies.models import Currency
from poms.instruments.models import Instrument
from poms.instruments.models import InstrumentType
from poms.obj_perms.utils import obj_perms_filter_objects_for_view
from poms.portfolios.models import Portfolio
from poms.strategies.models import Strategy1Group, Strategy1Subgroup, Strategy1, Strategy2Group, Strategy2Subgroup, \
    Strategy2, Strategy3Group, Strategy3Subgroup, Strategy3
from poms.tags.models import Tag
from poms.transactions.models import TransactionType


class TagFakeFilter(django_filters.Filter):
    def __init__(self, *args, **kwargs):
        super(TagFakeFilter, self).__init__(*args, **kwargs)

    def filter(self, qs, value):
        return qs


class TagContentTypeFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        models = [AccountType, Account, Currency, InstrumentType, Instrument, Counterparty, Responsible,
                  Strategy1Group, Strategy1Subgroup, Strategy1,
                  Strategy2Group, Strategy2Subgroup, Strategy2,
                  Strategy3Group, Strategy3Subgroup, Strategy3,
                  Portfolio, TransactionType, ThreadGroup, Thread]
        ctypes = [ContentType.objects.get_for_model(model).pk for model in models]
        return queryset.filter(pk__in=ctypes)


class TagFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        queryset = queryset.prefetch_related(
            'tags',
            'tags__user_object_permissions', 'tags__user_object_permissions__permission',
            'tags__group_object_permissions', 'tags__group_object_permissions__permission',
        )
        return queryset


def tags_choices(model=None):
    master_user = get_request().user.master_user
    member = get_request().user.member
    content_type = ContentType.objects.get_for_model(model)
    qs = Tag.objects.filter(master_user=master_user, content_types__in=[content_type.id]).order_by('name')
    for t in obj_perms_filter_objects_for_view(member, qs, prefetch=False):
        yield t.id, t.name


class TagFilter(django_filters.MultipleChoiceFilter):
    def __init__(self, *args, **kwargs):
        model = kwargs.pop('model')
        kwargs['name'] = 'tags'
        kwargs['choices'] = partial(tags_choices, model=model)
        super(TagFilter, self).__init__(*args, **kwargs)
