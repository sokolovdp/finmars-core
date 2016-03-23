from __future__ import unicode_literals

import django_filters
from rest_framework.decorators import detail_route, list_route
from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter, FilterSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from poms.api.filters import IsOwnerByMasterUserOrSystemFilter
from poms.api.mixins import DbTransactionMixin
from poms.api.permissions import IsOwnerOrReadonly
from poms.audit.serializers import VersionSerializer
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


class CurrencyViewSet(DbTransactionMixin, ModelViewSet):
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadonly]
    filter_backends = [IsOwnerByMasterUserOrSystemFilter, DjangoFilterBackend, OrderingFilter, SearchFilter, ]
    filter_class = CurrencyFilter
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']

    @list_route()
    def deleted(self, request, pk=None):
        from reversion import revisions as reversion

        profile = getattr(request.user, 'profile', None)
        master_user = getattr(profile, 'master_user', None)

        deleted_list = reversion.get_deleted(Currency).filter(revision__info__master_user=master_user)
        return self.make_historical_reponse(deleted_list)

    @detail_route()
    def history(self, request, pk=None):
        from reversion import revisions as reversion
        instance = self.get_object()
        version_list = list(reversion.get_for_object(instance))
        return self.make_historical_reponse(version_list)

    def make_historical_reponse(self, versions):
        versions = list(versions)
        for v in versions:
            instance = v.object_version.object
            serializer = self.get_serializer(instance=instance)
            v.object_json = serializer.data
        serializer = VersionSerializer(data=versions, many=True)
        serializer.is_valid()
        return Response(serializer.data)


class CurrencyHistoryFilter(FilterSet):
    currency = django_filters.Filter(name='currency')
    min_date = django_filters.DateFilter(name='date', lookup_type='gte')
    max_date = django_filters.DateFilter(name='date', lookup_type='lte')

    class Meta:
        model = CurrencyHistory
        fields = ['currency', 'min_date', 'max_date']


class CurrencyHistoryViewSet(DbTransactionMixin, ModelViewSet):
    queryset = CurrencyHistory.objects.all()
    serializer_class = CurrencyHistorySerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadonly]
    filter_backends = [IsOwnerByMasterUserOrSystemFilter, DjangoFilterBackend, OrderingFilter, ]
    filter_class = CurrencyHistoryFilter
    ordering_fields = ['-date']
