from __future__ import unicode_literals

import django_filters
from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter, FilterSet

from poms.common.views import PomsViewSetBase
from poms.currencies.filters import OwnerByCurrencyFilter
from poms.currencies.models import Currency, CurrencyHistory
from poms.currencies.serializers import CurrencySerializer, CurrencyHistorySerializer
from poms.tags.filters import TagFakeFilter, TagFilterBackend
from poms.users.filters import OwnerByMasterUserFilter
from poms.users.permissions import SuperUserOrReadOnly


class CurrencyFilterSet(FilterSet):
    user_code = django_filters.CharFilter(lookup_expr='icontains')
    name = django_filters.CharFilter(lookup_expr='icontains')
    short_name = django_filters.CharFilter(lookup_expr='icontains')
    tags = TagFakeFilter()

    class Meta:
        model = Currency
        fields = ['user_code', 'name', 'short_name', 'tags']


class CurrencyViewSet(PomsViewSetBase):
    queryset = Currency.objects
    serializer_class = CurrencySerializer
    permission_classes = PomsViewSetBase.permission_classes + [
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
    currency = django_filters.Filter(name='currency')
    date = django_filters.DateFromToRangeFilter()

    class Meta:
        model = CurrencyHistory
        fields = ['currency', 'date']


class CurrencyHistoryViewSet(PomsViewSetBase):
    queryset = CurrencyHistory.objects.prefetch_related('currency')
    serializer_class = CurrencyHistorySerializer
    permission_classes = PomsViewSetBase.permission_classes + [
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
