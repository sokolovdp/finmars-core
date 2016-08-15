from __future__ import unicode_literals, print_function

import django_filters
from rest_framework.filters import FilterSet
from rest_framework.response import Response

from poms.common.filters import CharFilter, ModelWithPermissionMultipleChoiceFilter
from poms.common.views import AbstractViewSet, AbstractModelViewSet, AbstractReadOnlyModelViewSet
from poms.integrations.filters import TaskFilter
from poms.integrations.models import InstrumentMapping, ImportConfig, Task
from poms.integrations.serializers import InstrumentMappingSerializer, ImportConfigSerializer, TaskSerializer, \
    ImportFileInstrumentSerializer, ImportInstrumentSerializer, ImportPriceHistorySerializer, \
    ImportCurrencyHistorySerializer
from poms.users.filters import OwnerByMasterUserFilter
from poms.users.models import Member
from poms.users.permissions import SuperUserOrReadOnly, SuperUserOnly


class InstrumentMappingFilterSet(FilterSet):
    mapping_name = CharFilter()

    class Meta:
        model = InstrumentMapping
        fields = ['mapping_name', ]


class InstrumentMappingViewSet(AbstractModelViewSet):
    queryset = InstrumentMapping.objects.prefetch_related('attributes', 'attributes__attribute_type')
    serializer_class = InstrumentMappingSerializer
    permission_classes = AbstractModelViewSet.permission_classes + [
        SuperUserOrReadOnly,
    ]
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]
    filter_class = InstrumentMappingFilterSet
    ordering_fields = ['mapping_name']
    search_fields = ['mapping_name']


class ImportConfigViewSet(AbstractModelViewSet):
    queryset = ImportConfig.objects
    serializer_class = ImportConfigSerializer
    permission_classes = AbstractModelViewSet.permission_classes + [
        SuperUserOnly,
    ]
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]


class TaskFilterSet(FilterSet):
    member = ModelWithPermissionMultipleChoiceFilter(model=Member, field_name='username')
    action = CharFilter()
    created = django_filters.DateFromToRangeFilter()
    modified = django_filters.DateFromToRangeFilter()

    class Meta:
        model = Task
        fields = ['member', 'provider', 'action', 'created', 'modified']


class TaskViewSet(AbstractReadOnlyModelViewSet):
    queryset = Task.objects.prefetch_related('instruments', 'currencies')
    serializer_class = TaskSerializer
    filter_backends = AbstractReadOnlyModelViewSet.filter_backends + [
        TaskFilter,
    ]
    filter_class = TaskFilterSet
    ordering_fields = ['action', 'created', 'modified']
    search_fields = ['action']


class ImportFileInstrumentViewSet(AbstractViewSet):
    serializer_class = ImportFileInstrumentSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ImportInstrumentViewSet(AbstractViewSet):
    serializer_class = ImportInstrumentSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ImportPriceHistoryViewSet(AbstractViewSet):
    serializer_class = ImportPriceHistorySerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ImportCurrencyHistoryViewSet(AbstractViewSet):
    serializer_class = ImportCurrencyHistorySerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
