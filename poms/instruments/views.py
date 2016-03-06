from __future__ import unicode_literals

import django_filters
from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter, FilterSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from poms.api.filters import IsOwnerByMasterUserFilter
from poms.instruments.models import InstrumentClassifier
from poms.instruments.serializers import InstrumentClassifierSerializer


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


class InstrumentClassifierViewSet(ModelViewSet):
    queryset = InstrumentClassifier.objects.all()
    serializer_class = InstrumentClassifierSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (IsOwnerByMasterUserFilter, DjangoFilterBackend, OrderingFilter, SearchFilter,)
    filter_class = InstrumentClassifierFilter
    ordering_fields = ['name']
    search_fields = ['name']
