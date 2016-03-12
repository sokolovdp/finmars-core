from __future__ import unicode_literals

import django_filters
from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter, FilterSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from poms.api.filters import IsOwnerByMasterUserFilter
from poms.api.mixins import DbTransactionMixin
from poms.instruments.models import InstrumentClassifier, Instrument, PriceHistory
from poms.instruments.serializers import InstrumentClassifierSerializer, InstrumentSerializer, PriceHistorySerializer


class InstrumentClassifierFilter(FilterSet):
    is_root = django_filters.MethodFilter(action='is_root_filter')
    tree_id = django_filters.NumberFilter()
    level = django_filters.NumberFilter()

    class Meta:
        model = InstrumentClassifier
        fields = ['is_root', 'tree_id', 'level']

    def is_root_filter(self, qs, value):
        if value is not None and (value.lower() in ['1', 'true']):
            return qs.filter(parent__isnull=True)
            # return qs.root_nodes()
        return qs


class InstrumentClassifierViewSet(DbTransactionMixin, ModelViewSet):
    queryset = InstrumentClassifier.objects.all()
    serializer_class = InstrumentClassifierSerializer
    permission_classes = [IsAuthenticated, ]
    filter_backends = [IsOwnerByMasterUserFilter, DjangoFilterBackend, OrderingFilter, SearchFilter, ]
    filter_class = InstrumentClassifierFilter
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']


class InstrumentViewSet(DbTransactionMixin, ModelViewSet):
    queryset = Instrument.objects.all()
    serializer_class = InstrumentSerializer
    permission_classes = [IsAuthenticated, ]
    filter_backends = [IsOwnerByMasterUserFilter, DjangoFilterBackend, OrderingFilter, SearchFilter, ]
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']


class PriceHistoryFilter(FilterSet):
    instrument = django_filters.Filter(name='instrument')
    min_date = django_filters.DateFilter(name='date', lookup_type='gte')
    max_date = django_filters.DateFilter(name='date', lookup_type='lte')

    class Meta:
        model = PriceHistory
        fields = ['instrument', 'min_date', 'max_date']


class PriceHistoryViewSet(DbTransactionMixin, ModelViewSet):
    queryset = PriceHistory.objects.all()
    serializer_class = PriceHistorySerializer
    permission_classes = [IsAuthenticated, ]
    filter_backends = [DjangoFilterBackend, OrderingFilter, ]
    filter_class = PriceHistoryFilter
    ordering_fields = ['-date']
