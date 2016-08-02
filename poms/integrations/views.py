from __future__ import unicode_literals, print_function

import django_filters
from rest_framework.filters import FilterSet
from rest_framework.response import Response

from poms.common.filters import CharFilter, ModelWithPermissionMultipleChoiceFilter
from poms.common.views import AbstractViewSet, AbstractModelViewSet, AbstractReadOnlyModelViewSet
from poms.integrations.filters import BloombergTaskFilter
from poms.integrations.models import InstrumentMapping, BloombergConfig, BloombergTask
from poms.integrations.permissions import BloombergConfigured
from poms.integrations.serializers import FileInstrumentImportSerializer, InstrumentMappingSerializer, \
    BloombergConfigSerializer, BloombergTaskSerializer, BloombergInstrumentImportSerializer, \
    BloombergPriceHistoryImportSerializer, BloombergCurrencyHistoryImportSerializer
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


class BloombergConfigViewSet(AbstractModelViewSet):
    queryset = BloombergConfig.objects
    serializer_class = BloombergConfigSerializer
    permission_classes = AbstractModelViewSet.permission_classes + [
        SuperUserOnly,
    ]
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]


class BloombergTaskFilterSet(FilterSet):
    member = ModelWithPermissionMultipleChoiceFilter(model=Member, field_name='username')
    action = CharFilter()
    created = django_filters.DateFromToRangeFilter()
    modified = django_filters.DateFromToRangeFilter()

    class Meta:
        model = BloombergTask
        fields = ['member', 'action', 'created', 'modified']


class BloombergTaskViewSet(AbstractReadOnlyModelViewSet):
    queryset = BloombergTask.objects
    serializer_class = BloombergTaskSerializer
    filter_backends = AbstractReadOnlyModelViewSet.filter_backends + [
        BloombergTaskFilter,
    ]
    filter_class = BloombergTaskFilterSet
    ordering_fields = ['action', 'created', 'modified']
    search_fields = ['action']


class FileInstrumentImportViewSet(AbstractViewSet):
    serializer_class = FileInstrumentImportSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class BloombergInstrumentImportViewSet(AbstractViewSet):
    serializer_class = BloombergInstrumentImportSerializer
    permission_classes = AbstractViewSet.permission_classes + [
        BloombergConfigured,
    ]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class BloombergPriceHistoryImportViewSet(AbstractViewSet):
    serializer_class = BloombergPriceHistoryImportSerializer
    permission_classes = AbstractViewSet.permission_classes + [
        BloombergConfigured,
    ]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class BloombergCurrencyHistoryImportViewSet(AbstractViewSet):
    serializer_class = BloombergCurrencyHistoryImportSerializer
    permission_classes = AbstractViewSet.permission_classes + [
        BloombergConfigured,
    ]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
