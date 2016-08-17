from __future__ import unicode_literals, print_function

import django_filters
from rest_framework.filters import FilterSet
from rest_framework.response import Response

from poms.common.filters import CharFilter, ModelWithPermissionMultipleChoiceFilter
from poms.common.views import AbstractViewSet, AbstractModelViewSet, AbstractReadOnlyModelViewSet, \
    AbstractClassModelViewSet
from poms.currencies.models import Currency
from poms.instruments.models import InstrumentType, InstrumentAttributeType
from poms.integrations.filters import TaskFilter
from poms.integrations.models import ImportConfig, Task, InstrumentDownloadScheme, ProviderClass, \
    FactorScheduleDownloadMethod, AccrualScheduleDownloadMethod, PriceDownloadScheme, CurrencyMapping, \
    InstrumentTypeMapping, InstrumentAttributeValueMapping, AccrualCalculationModelMapping, PeriodicityMapping
from poms.integrations.serializers import ImportConfigSerializer, TaskSerializer, \
    ImportFileInstrumentSerializer, ImportInstrumentSerializer, ImportHistorySerializer, \
    InstrumentDownloadSchemeSerializer, ProviderClassSerializer, FactorScheduleDownloadMethodSerializer, \
    AccrualScheduleDownloadMethodSerializer, PriceDownloadSchemeSerializer, CurrencyMappingSerializer, \
    InstrumentTypeMappingSerializer, InstrumentAttributeValueMappingSerializer, \
    AccrualCalculationModelMappingSerializer, \
    PeriodicityMappingSerializer
from poms.users.filters import OwnerByMasterUserFilter
from poms.users.models import Member
from poms.users.permissions import SuperUserOrReadOnly, SuperUserOnly


class ProviderClassViewSet(AbstractClassModelViewSet):
    queryset = ProviderClass.objects
    serializer_class = ProviderClassSerializer


class FactorScheduleDownloadMethodViewSet(AbstractClassModelViewSet):
    queryset = FactorScheduleDownloadMethod.objects
    serializer_class = FactorScheduleDownloadMethodSerializer


class AccrualScheduleDownloadMethodViewSet(AbstractClassModelViewSet):
    queryset = AccrualScheduleDownloadMethod.objects
    serializer_class = AccrualScheduleDownloadMethodSerializer


class ImportConfigViewSet(AbstractModelViewSet):
    queryset = ImportConfig.objects
    serializer_class = ImportConfigSerializer
    permission_classes = AbstractModelViewSet.permission_classes + [
        SuperUserOnly,
    ]
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]


class InstrumentDownloadSchemeFilterSet(FilterSet):
    scheme_name = CharFilter()

    class Meta:
        model = InstrumentDownloadScheme
        fields = ['scheme_name', 'provider', ]


class InstrumentDownloadSchemeViewSet(AbstractModelViewSet):
    queryset = InstrumentDownloadScheme.objects.prefetch_related('inputs', 'attributes', 'attributes__attribute_type')
    serializer_class = InstrumentDownloadSchemeSerializer
    permission_classes = AbstractModelViewSet.permission_classes + [
        SuperUserOrReadOnly,
    ]
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]
    filter_class = InstrumentDownloadSchemeFilterSet
    ordering_fields = ['scheme_name']
    search_fields = ['scheme_name']


class PriceDownloadSchemeFilterSet(FilterSet):
    scheme_name = CharFilter()

    class Meta:
        model = PriceDownloadScheme
        fields = ['provider', 'scheme_name', ]


class PriceDownloadSchemeViewSet(AbstractModelViewSet):
    queryset = PriceDownloadScheme.objects.prefetch_related()
    serializer_class = PriceDownloadSchemeSerializer
    permission_classes = AbstractModelViewSet.permission_classes + [
        SuperUserOrReadOnly,
    ]
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]
    filter_class = PriceDownloadSchemeFilterSet
    ordering_fields = ['scheme_name']
    search_fields = ['scheme_name']


class CurrencyMappingFilterSet(FilterSet):
    value = CharFilter()
    currency = ModelWithPermissionMultipleChoiceFilter(model=Currency)

    class Meta:
        model = CurrencyMapping
        fields = ['provider', 'value', 'currency', ]


class CurrencyMappingViewSet(AbstractModelViewSet):
    queryset = CurrencyMapping.objects.select_related('master_user', 'currency')
    serializer_class = CurrencyMappingSerializer
    permission_classes = AbstractModelViewSet.permission_classes + [
        SuperUserOrReadOnly,
    ]
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]
    filter_class = CurrencyMappingFilterSet


class InstrumentTypeMappingFilterSet(FilterSet):
    value = CharFilter()
    instrument_type = ModelWithPermissionMultipleChoiceFilter(model=InstrumentType)

    class Meta:
        model = InstrumentTypeMapping
        fields = ['provider', 'value', 'instrument_type', ]


class InstrumentTypeMappingViewSet(AbstractModelViewSet):
    queryset = InstrumentTypeMapping.objects.select_related('master_user', 'instrument_type')
    serializer_class = InstrumentTypeMappingSerializer
    permission_classes = AbstractModelViewSet.permission_classes + [
        SuperUserOrReadOnly,
    ]
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]
    filter_class = InstrumentTypeMappingFilterSet


class InstrumentAttributeValueMappingFilterSet(FilterSet):
    value = CharFilter()
    attribute_type = ModelWithPermissionMultipleChoiceFilter(model=InstrumentAttributeType)

    class Meta:
        model = InstrumentAttributeValueMapping
        fields = ['provider', 'value', 'attribute_type', ]


class InstrumentAttributeValueMappingViewSet(AbstractModelViewSet):
    queryset = InstrumentAttributeValueMapping.objects.select_related('master_user', 'attribute_type', 'classifier')
    serializer_class = InstrumentAttributeValueMappingSerializer
    permission_classes = AbstractModelViewSet.permission_classes + [
        SuperUserOrReadOnly,
    ]
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]
    filter_class = InstrumentAttributeValueMappingFilterSet


class AccrualCalculationModelMappingFilterSet(FilterSet):
    value = CharFilter()

    class Meta:
        model = AccrualCalculationModelMapping
        fields = ['provider', 'value', 'accrual_calculation_model', ]


class AccrualCalculationModelMappingViewSet(AbstractModelViewSet):
    queryset = AccrualCalculationModelMapping.objects.select_related('master_user', 'accrual_calculation_model')
    serializer_class = AccrualCalculationModelMappingSerializer
    permission_classes = AbstractModelViewSet.permission_classes + [
        SuperUserOrReadOnly,
    ]
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]
    filter_class = AccrualCalculationModelMappingFilterSet


class PeriodicityMappingFilterSet(FilterSet):
    value = CharFilter()

    class Meta:
        model = PeriodicityMapping
        fields = ['provider', 'value', 'periodicity', ]


class PeriodicityMappingViewSet(AbstractModelViewSet):
    queryset = PeriodicityMapping.objects.select_related('master_user', 'periodicity')
    serializer_class = PeriodicityMappingSerializer
    permission_classes = AbstractModelViewSet.permission_classes + [
        SuperUserOrReadOnly,
    ]
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]
    filter_class = PeriodicityMappingFilterSet


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


class ImportHistoryViewSet(AbstractViewSet):
    serializer_class = ImportHistorySerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
