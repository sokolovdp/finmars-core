from __future__ import unicode_literals

import django_filters
from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter, FilterSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from poms.api.filters import IsOwnerByMasterUserOrSystemFilter
from poms.api.permissions import IsOwnerOrReadonly
from poms.currencies.models import Currency
from poms.currencies.serializers import CurrencySerializer


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
    permission_classes = (IsAuthenticated, IsOwnerOrReadonly)
    filter_backends = (IsOwnerByMasterUserOrSystemFilter, DjangoFilterBackend, OrderingFilter, SearchFilter,)
    # permission_classes = (IsAuthenticated, DjangoObjectPermissions,)
    # filter_backends = (DjangoFilterBackend, OrderingFilter, DjangoObjectPermissionsFilter)
    filter_class = CurrencyFilter
    ordering_fields = ['name']
    search_fields = ['name']
