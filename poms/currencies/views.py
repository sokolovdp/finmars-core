from __future__ import unicode_literals

import django_filters
from rest_framework.filters import FilterSet

from poms.common.filters import CharFilter, ModelMultipleChoiceFilter, NoOpFilter
from poms.common.views import AbstractModelViewSet
from poms.currencies.filters import OwnerByCurrencyFilter
from poms.currencies.models import Currency, CurrencyHistory
from poms.currencies.serializers import CurrencySerializer, CurrencyHistorySerializer
from poms.tags.filters import TagFilterBackend, TagFilter
from poms.users.filters import OwnerByMasterUserFilter
from poms.users.permissions import SuperUserOrReadOnly


class CurrencyFilterSet(FilterSet):
    id = NoOpFilter()
    is_deleted = django_filters.BooleanFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    reference_for_pricing = CharFilter()
    tag = TagFilter(model=Currency)

    class Meta:
        model = Currency
        fields = []


class CurrencyViewSet(AbstractModelViewSet):
    queryset = Currency.objects.prefetch_related('master_user')
    serializer_class = CurrencySerializer
    permission_classes = AbstractModelViewSet.permission_classes + [
        SuperUserOrReadOnly,
    ]
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        TagFilterBackend,
    ]
    filter_class = CurrencyFilterSet
    ordering_fields = [
        'user_code', 'name', 'short_name', 'reference_for_pricing',
    ]
    search_fields = [
        'user_code', 'name', 'short_name', 'reference_for_pricing'
    ]
    has_feature_is_deleted = True


class CurrencyHistoryFilterSet(FilterSet):
    id = NoOpFilter()
    date = django_filters.DateFromToRangeFilter()
    currency = ModelMultipleChoiceFilter(model=Currency)

    class Meta:
        model = CurrencyHistory
        fields = []


class CurrencyHistoryViewSet(AbstractModelViewSet):
    queryset = CurrencyHistory.objects.prefetch_related('currency')
    serializer_class = CurrencyHistorySerializer
    permission_classes = AbstractModelViewSet.permission_classes + [
        SuperUserOrReadOnly,
    ]
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByCurrencyFilter,
    ]
    filter_class = CurrencyHistoryFilterSet
    ordering_fields = [
        'date', 'currency__user_code', 'currency__name', 'currency__short_name',
    ]
    search_fields = []
