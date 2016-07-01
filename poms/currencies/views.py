from __future__ import unicode_literals

import django_filters
from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter, FilterSet

from poms.common.filters import CharFilter, ModelMultipleChoiceFilter
from poms.common.views import AbstractModelViewSet
from poms.currencies.filters import OwnerByCurrencyFilter
from poms.currencies.models import Currency, CurrencyHistory
from poms.currencies.serializers import CurrencySerializer, CurrencyHistorySerializer
from poms.tags.filters import TagFilterBackend, TagFilter
from poms.users.filters import OwnerByMasterUserFilter
from poms.users.permissions import SuperUserOrReadOnly


class CurrencyFilterSet(FilterSet):
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    tag = TagFilter(model=Currency)

    class Meta:
        model = Currency
        fields = ['user_code', 'name', 'short_name', 'tag']


class CurrencyViewSet(AbstractModelViewSet):
    queryset = Currency.objects
    serializer_class = CurrencySerializer
    permission_classes = AbstractModelViewSet.permission_classes + [
        SuperUserOrReadOnly,
    ]
    filter_backends = [
        OwnerByMasterUserFilter,
        TagFilterBackend,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    filter_class = CurrencyFilterSet
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']


class CurrencyHistoryFilterSet(FilterSet):
    currency = ModelMultipleChoiceFilter(model=Currency)
    date = django_filters.DateFromToRangeFilter()

    class Meta:
        model = CurrencyHistory
        fields = ['currency', 'date']


class CurrencyHistoryViewSet(AbstractModelViewSet):
    queryset = CurrencyHistory.objects.prefetch_related('currency')
    serializer_class = CurrencyHistorySerializer
    permission_classes = AbstractModelViewSet.permission_classes + [
        SuperUserOrReadOnly,
    ]
    filter_backends = [
        OwnerByCurrencyFilter,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    filter_class = CurrencyHistoryFilterSet
    ordering_fields = ['date', ]
    search_fields = ['currency__user_code', 'currency__name', 'currency__short_name']
