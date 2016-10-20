from __future__ import unicode_literals, print_function

import django_filters
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Prefetch
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.filters import FilterSet
from rest_framework.response import Response

from poms.common.filters import CharFilter, ModelExtWithPermissionMultipleChoiceFilter, NoOpFilter, \
    ModelExtMultipleChoiceFilter
from poms.common.views import AbstractViewSet, AbstractModelViewSet, AbstractReadOnlyModelViewSet, \
    AbstractClassModelViewSet
from poms.currencies.models import Currency
from poms.instruments.models import InstrumentType, AccrualCalculationModel, Periodicity
from poms.integrations.filters import TaskFilter, InstrumentAttributeValueMappingObjectPermissionFilter, \
    InstrumentTypeMappingObjectPermissionFilter
from poms.integrations.models import ImportConfig, Task, InstrumentDownloadScheme, ProviderClass, \
    FactorScheduleDownloadMethod, AccrualScheduleDownloadMethod, PriceDownloadScheme, CurrencyMapping, \
    InstrumentTypeMapping, InstrumentAttributeValueMapping, AccrualCalculationModelMapping, PeriodicityMapping, \
    PricingAutomatedSchedule, InstrumentDownloadSchemeAttribute
from poms.integrations.serializers import ImportConfigSerializer, TaskSerializer, \
    ImportFileInstrumentSerializer, ImportInstrumentSerializer, ImportPricingSerializer, \
    InstrumentDownloadSchemeSerializer, ProviderClassSerializer, FactorScheduleDownloadMethodSerializer, \
    AccrualScheduleDownloadMethodSerializer, PriceDownloadSchemeSerializer, CurrencyMappingSerializer, \
    InstrumentTypeMappingSerializer, InstrumentAttributeValueMappingSerializer, \
    AccrualCalculationModelMappingSerializer, \
    PeriodicityMappingSerializer, PricingAutomatedScheduleSerializer
from poms.obj_attrs.models import GenericAttributeType
from poms.obj_perms.utils import get_permissions_prefetch_lookups
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


class ImportConfigFilterSet(FilterSet):
    provider = django_filters.ModelMultipleChoiceFilter(queryset=ProviderClass.objects)

    class Meta:
        model = ImportConfig
        fields = []


class ImportConfigViewSet(AbstractModelViewSet):
    queryset = ImportConfig.objects
    serializer_class = ImportConfigSerializer
    permission_classes = AbstractModelViewSet.permission_classes + [
        SuperUserOnly,
    ]
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]
    filter_class = ImportConfigFilterSet


class InstrumentDownloadSchemeFilterSet(FilterSet):
    id = NoOpFilter()
    provider = django_filters.ModelMultipleChoiceFilter(queryset=ProviderClass.objects)
    scheme_name = CharFilter()

    class Meta:
        model = InstrumentDownloadScheme
        fields = []


class InstrumentDownloadSchemeViewSet(AbstractModelViewSet):
    queryset = InstrumentDownloadScheme.objects.select_related(
        'provider', 'payment_size_detail', 'daily_pricing_model', 'price_download_scheme', 'factor_schedule_method',
        'accrual_calculation_schedule_method',
    ).prefetch_related(
        'inputs',
        Prefetch(
            'attributes',
            queryset=InstrumentDownloadSchemeAttribute.objects.select_related('attribute_type')
        ),
        *get_permissions_prefetch_lookups(
            ('attributes__attribute_type', GenericAttributeType),
        )
    )
    serializer_class = InstrumentDownloadSchemeSerializer
    # permission_classes = AbstractModelViewSet.permission_classes + [
    #     SuperUserOrReadOnly,
    # ]
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]
    filter_class = InstrumentDownloadSchemeFilterSet
    ordering_fields = [
        'scheme_name',
        'provider', 'provider__name',
    ]


class PriceDownloadSchemeFilterSet(FilterSet):
    id = NoOpFilter()
    provider = django_filters.ModelMultipleChoiceFilter(queryset=ProviderClass.objects)
    scheme_name = CharFilter()

    class Meta:
        model = PriceDownloadScheme
        fields = []


class PriceDownloadSchemeViewSet(AbstractModelViewSet):
    queryset = PriceDownloadScheme.objects.select_related('provider')
    serializer_class = PriceDownloadSchemeSerializer
    # permission_classes = AbstractModelViewSet.permission_classes + [
    #     SuperUserOrReadOnly,
    # ]
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]
    filter_class = PriceDownloadSchemeFilterSet
    ordering_fields = [
        'scheme_name',
        'provider', 'provider__name',
    ]


class CurrencyMappingFilterSet(FilterSet):
    id = NoOpFilter()
    provider = django_filters.ModelMultipleChoiceFilter(queryset=ProviderClass.objects)
    value = CharFilter()
    currency = ModelExtMultipleChoiceFilter(model=Currency)

    class Meta:
        model = CurrencyMapping
        fields = []


class CurrencyMappingViewSet(AbstractModelViewSet):
    queryset = CurrencyMapping.objects.select_related('master_user', 'provider', 'currency')
    serializer_class = CurrencyMappingSerializer
    permission_classes = AbstractModelViewSet.permission_classes + [
        SuperUserOrReadOnly,
    ]
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]
    filter_class = CurrencyMappingFilterSet
    ordering_fields = [
        'provider', 'provider__name',
        'value',
        'currency', 'currency__user_code', 'currency__name', 'currency__short_name', 'currency__public_name',
    ]


class InstrumentTypeMappingFilterSet(FilterSet):
    id = NoOpFilter()
    provider = django_filters.ModelMultipleChoiceFilter(queryset=ProviderClass.objects)
    value = CharFilter()
    instrument_type = ModelExtWithPermissionMultipleChoiceFilter(model=InstrumentType)

    class Meta:
        model = InstrumentTypeMapping
        fields = []


class InstrumentTypeMappingViewSet(AbstractModelViewSet):
    queryset = InstrumentTypeMapping.objects.select_related('master_user', 'provider', 'instrument_type')
    serializer_class = InstrumentTypeMappingSerializer
    # permission_classes = AbstractModelViewSet.permission_classes + [
    #     SuperUserOrReadOnly,
    # ]
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        InstrumentTypeMappingObjectPermissionFilter,
    ]
    filter_class = InstrumentTypeMappingFilterSet
    ordering_fields = [
        'value',
        'instrument_type', 'instrument_type__user_code', 'instrument_type__name', 'instrument_type__short_name',
        'instrument_type__public_name',
    ]


class InstrumentAttributeValueMappingFilterSet(FilterSet):
    id = NoOpFilter()
    provider = django_filters.ModelMultipleChoiceFilter(queryset=ProviderClass.objects)
    value = CharFilter()
    attribute_type = ModelExtWithPermissionMultipleChoiceFilter(model=GenericAttributeType)

    class Meta:
        model = InstrumentAttributeValueMapping
        fields = []


class InstrumentAttributeValueMappingViewSet(AbstractModelViewSet):
    queryset = InstrumentAttributeValueMapping.objects.select_related(
        'master_user', 'provider', 'attribute_type', 'classifier'
    )
    serializer_class = InstrumentAttributeValueMappingSerializer
    # permission_classes = AbstractModelViewSet.permission_classes + [
    #     SuperUserOrReadOnly,
    # ]
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        InstrumentAttributeValueMappingObjectPermissionFilter,
    ]
    filter_class = InstrumentAttributeValueMappingFilterSet
    ordering_fields = [
        'provider', 'provider__name',
        'value',
        'attribute_type', 'attribute_type__user_code', 'attribute_type__name', 'attribute_type__short_name',
        'attribute_type__public_name',
    ]


class AccrualCalculationModelMappingFilterSet(FilterSet):
    id = NoOpFilter()
    provider = django_filters.ModelMultipleChoiceFilter(queryset=ProviderClass.objects)
    value = CharFilter()
    accrual_calculation_model = django_filters.ModelMultipleChoiceFilter(queryset=AccrualCalculationModel.objects)

    class Meta:
        model = AccrualCalculationModelMapping
        fields = []


class AccrualCalculationModelMappingViewSet(AbstractModelViewSet):
    queryset = AccrualCalculationModelMapping.objects.select_related(
        'master_user', 'provider', 'accrual_calculation_model'
    )
    serializer_class = AccrualCalculationModelMappingSerializer
    # permission_classes = AbstractModelViewSet.permission_classes + [
    #     SuperUserOrReadOnly,
    # ]
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]
    filter_class = AccrualCalculationModelMappingFilterSet
    ordering_fields = [
        'provider', 'provider__name',
        'value',
        'accrual_calculation_model', 'accrual_calculation_model__name'
    ]


class PeriodicityMappingFilterSet(FilterSet):
    id = NoOpFilter()
    provider = django_filters.ModelMultipleChoiceFilter(queryset=ProviderClass.objects)
    value = CharFilter()
    periodicity = django_filters.ModelMultipleChoiceFilter(queryset=Periodicity.objects)

    class Meta:
        model = PeriodicityMapping
        fields = []


class PeriodicityMappingViewSet(AbstractModelViewSet):
    queryset = PeriodicityMapping.objects.select_related('master_user', 'provider', 'periodicity')
    serializer_class = PeriodicityMappingSerializer
    # permission_classes = AbstractModelViewSet.permission_classes + [
    #     SuperUserOrReadOnly,
    # ]
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]
    filter_class = PeriodicityMappingFilterSet
    ordering_fields = [
        'provider', 'provider__name',
        'value',
        'periodicity', 'periodicity__name',
    ]


class TaskFilterSet(FilterSet):
    id = NoOpFilter()
    provider = django_filters.ModelMultipleChoiceFilter(queryset=ProviderClass.objects)
    member = ModelExtMultipleChoiceFilter(model=Member, field_name='username')
    action = CharFilter()
    created = django_filters.DateFromToRangeFilter()
    modified = django_filters.DateFromToRangeFilter()

    class Meta:
        model = Task
        fields = []


class TaskViewSet(AbstractReadOnlyModelViewSet):
    queryset = Task.objects.select_related('provider').prefetch_related('children')
    serializer_class = TaskSerializer
    filter_backends = AbstractReadOnlyModelViewSet.filter_backends + [
        TaskFilter,
    ]
    filter_class = TaskFilterSet
    ordering_fields = [
        'action', 'created', 'modified'
    ]


class PricingAutomatedScheduleViewSet(AbstractModelViewSet):
    queryset = PricingAutomatedSchedule.objects
    serializer_class = PricingAutomatedScheduleSerializer
    permission_classes = AbstractModelViewSet.permission_classes + [
        SuperUserOrReadOnly,
    ]
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]

    def get_object(self):
        try:
            return self.request.user.master_user.pricing_automated_schedule
        except ObjectDoesNotExist:
            obj = PricingAutomatedSchedule.objects.create(master_user=self.request.user.master_user)
            return obj

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed(method=request.method)


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


class ImportPricingViewSet(AbstractViewSet):
    serializer_class = ImportPricingSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
