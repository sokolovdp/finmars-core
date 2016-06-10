from __future__ import unicode_literals

import django_filters
from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter, FilterSet
from rest_framework.permissions import IsAuthenticated

from poms.common.views import PomsViewSetBase
from poms.currencies.filters import OwnerByCurrencyFilter
from poms.currencies.models import Currency, CurrencyHistory
from poms.currencies.serializers import CurrencySerializer, CurrencyHistorySerializer
from poms.obj_perms.filters import AllFakeFilter
from poms.tags.filters import TagPrefetchFilter, ByTagNameFilter, TagFakeFilter
from poms.users.filters import OwnerByMasterUserFilter


class CurrencyFilterSet(FilterSet):
    all = AllFakeFilter()
    tags = TagFakeFilter()

    class Meta:
        model = Currency
        fields = ['user_code', 'name', 'short_name', 'all', 'tags']


class CurrencyViewSet(PomsViewSetBase):
    queryset = Currency.objects
    serializer_class = CurrencySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [
        OwnerByMasterUserFilter,
        TagPrefetchFilter,
        ByTagNameFilter,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    filter_class = CurrencyFilterSet
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']


class CurrencyHistoryFilterSet(FilterSet):
    currency = django_filters.Filter(name='currency')
    min_date = django_filters.DateFilter(name='date', lookup_type='gte')
    max_date = django_filters.DateFilter(name='date', lookup_type='lte')

    class Meta:
        model = CurrencyHistory
        fields = ['currency', 'min_date', 'max_date']


class CurrencyHistoryViewSet(PomsViewSetBase):
    queryset = CurrencyHistory.objects
    serializer_class = CurrencyHistorySerializer
    permission_classes = [IsAuthenticated, ]
    filter_backends = [
        OwnerByCurrencyFilter,
        DjangoFilterBackend,
        OrderingFilter,
    ]
    filter_class = CurrencyHistoryFilterSet
    ordering_fields = ['date', ]
