from __future__ import unicode_literals

import django_filters
from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter, FilterSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from poms.api.filters import IsOwnerByMasterUserOrSystemFilter
from poms.api.permissions import IsOwnerOrReadonly
from poms.currencies.models import Currency, CurrencyHistory
from poms.currencies.serializers import CurrencySerializer, CurrencyHistorySerializer


class CurrencyFilter(FilterSet):
    is_global = django_filters.MethodFilter(action='is_global_filter')

    class Meta:
        model = Currency
        fields = ['is_global']

    def is_global_filter(self, qs, value):
        if value is not None and (value.lower() in ['1', 'true']):
            return qs.filter(master_user__isnull=True)
        elif value is not None and (value.lower() in ['0', 'false']):
            return qs.filter(master_user__isnull=False)
        return qs


class CurrencyViewSet(ModelViewSet):
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadonly]
    filter_backends = [IsOwnerByMasterUserOrSystemFilter, DjangoFilterBackend, OrderingFilter, SearchFilter, ]
    # permission_classes = (IsAuthenticated, DjangoObjectPermissions,)
    # filter_backends = (DjangoFilterBackend, OrderingFilter, DjangoObjectPermissionsFilter)
    filter_class = CurrencyFilter
    ordering_fields = ['name']
    search_fields = ['name']


class CurrencyHistoryFilter(FilterSet):
    currency = django_filters.Filter(name='currency')
    min_date = django_filters.DateFilter(name='date', lookup_type='gte')
    max_date = django_filters.DateFilter(name='date', lookup_type='lte')

    class Meta:
        model = CurrencyHistory
        fields = ['currency', 'min_date', 'max_date']


class CurrencyHistoryViewSet(ModelViewSet):
    queryset = CurrencyHistory.objects.all()
    serializer_class = CurrencyHistorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter, ]
    filter_class = CurrencyHistoryFilter
    ordering_fields = ['-date']
