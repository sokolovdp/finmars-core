from __future__ import unicode_literals

import django_filters
from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter, FilterSet

from poms.common.filters import OrderingWithAttributesFilter
from poms.common.views import PomsClassViewSetBase, PomsViewSetBase
from poms.instruments.filters import OwnerByInstrumentFilter
from poms.instruments.models import Instrument, PriceHistory, InstrumentClass, DailyPricingModel, \
    AccrualCalculationModel, PaymentSizeDetail, PeriodicityPeriod, CostMethod, InstrumentType, InstrumentAttributeType, \
    PricingPolicy
from poms.instruments.serializers import InstrumentSerializer, PriceHistorySerializer, \
    InstrumentClassSerializer, DailyPricingModelSerializer, AccrualCalculationModelSerializer, \
    PaymentSizeDetailSerializer, PeriodicityPeriodSerializer, CostMethodSerializer, InstrumentTypeSerializer, \
    InstrumentAttributeTypeSerializer, PricingPolicySerializer
from poms.obj_attrs.filters import AttributePrefetchFilter
from poms.obj_attrs.views import AttributeTypeViewSetBase
from poms.obj_perms.filters import AllFakeFilter, ObjectPermissionBackend
from poms.obj_perms.permissions import ObjectPermissionBase
from poms.tags.filters import TagFakeFilter, TagFilterBackend
from poms.users.filters import OwnerByMasterUserFilter
from poms.users.permissions import SuperUserOrReadOnly


class InstrumentClassViewSet(PomsClassViewSetBase):
    queryset = InstrumentClass.objects
    serializer_class = InstrumentClassSerializer


class DailyPricingModelViewSet(PomsClassViewSetBase):
    queryset = DailyPricingModel.objects
    serializer_class = DailyPricingModelSerializer


class AccrualCalculationModelClassViewSet(PomsClassViewSetBase):
    queryset = AccrualCalculationModel.objects
    serializer_class = AccrualCalculationModelSerializer


class PaymentSizeDetailViewSet(PomsClassViewSetBase):
    queryset = PaymentSizeDetail.objects
    serializer_class = PaymentSizeDetailSerializer


class PeriodicityPeriodViewSet(PomsClassViewSetBase):
    queryset = PeriodicityPeriod.objects
    serializer_class = PeriodicityPeriodSerializer


class CostMethodViewSet(PomsClassViewSetBase):
    queryset = CostMethod.objects
    serializer_class = CostMethodSerializer


class PricingPolicyViewSet(PomsViewSetBase):
    queryset = PricingPolicy.objects
    serializer_class = PricingPolicySerializer
    filter_backends = [
        OwnerByMasterUserFilter,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter
    ]
    permission_classes = PomsViewSetBase.permission_classes + [
        SuperUserOrReadOnly,
    ]
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']


class InstrumentTypeFilterSet(FilterSet):
    all = AllFakeFilter()
    tags = TagFakeFilter()

    class Meta:
        model = InstrumentType
        fields = ['user_code', 'name', 'short_name', 'all', 'tags']


class InstrumentTypeViewSet(PomsViewSetBase):
    queryset = InstrumentType.objects
    serializer_class = InstrumentTypeSerializer
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionBackend,
        TagFilterBackend,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    filter_class = InstrumentTypeFilterSet
    permission_classes = PomsViewSetBase.permission_classes + [
        ObjectPermissionBase,
    ]
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']


# class InstrumentClassifierFilterSet(ClassifierFilterSetBase):
#     class Meta(ClassifierFilterSetBase.Meta):
#         model = InstrumentClassifier
#
#
# class InstrumentClassifierViewSet(ClassifierViewSetBase):
#     queryset = InstrumentClassifier.objects
#     serializer_class = InstrumentClassifierSerializer
#     filter_class = InstrumentClassifierFilterSet
#
#
# class InstrumentClassifierNodeViewSet(ClassifierNodeViewSetBase):
#     queryset = InstrumentClassifier.objects
#     serializer_class = InstrumentClassifierNodeSerializer
#     filter_class = InstrumentClassifierFilterSet


class InstrumentAttributeTypeFilterSet(FilterSet):
    class Meta:
        model = InstrumentAttributeType
        fields = ['user_code', 'name', 'short_name']


class InstrumentAttributeTypeViewSet(AttributeTypeViewSetBase):
    queryset = InstrumentAttributeType.objects.prefetch_related('classifiers')
    serializer_class = InstrumentAttributeTypeSerializer
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionBackend,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    filter_class = InstrumentAttributeTypeFilterSet
    permission_classes = PomsViewSetBase.permission_classes + [
        ObjectPermissionBase,
    ]
    ordering_fields = ['user_code', 'name', 'short_name', ]
    search_fields = ['user_code', 'name', 'short_name', ]


class InstrumentFilterSet(FilterSet):
    all = AllFakeFilter()
    tags = TagFakeFilter()

    class Meta:
        model = Instrument
        fields = ['user_code', 'name', 'short_name', 'all', 'tags']


class InstrumentViewSet(PomsViewSetBase):
    queryset = Instrument.objects.prefetch_related('manual_pricing_formulas', 'accrual_calculation_schedules',
                                                   'factor_schedules', 'event_schedules')
    serializer_class = InstrumentSerializer
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionBackend,
        AttributePrefetchFilter,
        TagFilterBackend,
        DjangoFilterBackend,
        # OrderingFilter,
        OrderingWithAttributesFilter,
        SearchFilter,
    ]
    filter_class = InstrumentFilterSet
    permission_classes = PomsViewSetBase.permission_classes + [
        ObjectPermissionBase
    ]
    ordering_fields = ['user_code', 'name', 'short_name', ]
    search_fields = ['user_code', 'name', 'short_name', ]


class PriceHistoryFilterSet(FilterSet):
    instrument = django_filters.Filter(name='instrument')
    min_date = django_filters.DateFilter(name='date', lookup_type='gte')
    max_date = django_filters.DateFilter(name='date', lookup_type='lte')

    class Meta:
        model = PriceHistory
        fields = ['instrument', 'min_date', 'max_date']


class PriceHistoryViewSet(PomsViewSetBase):
    queryset = PriceHistory.objects
    serializer_class = PriceHistorySerializer
    filter_backends = [OwnerByInstrumentFilter, DjangoFilterBackend, OrderingFilter]
    filter_class = PriceHistoryFilterSet
    ordering_fields = ['-date']

# class ManualPricingFormulaViewSet(PomsViewSetBase):
#     queryset = ManualPricingFormula.objects
#     serializer_class = ManualPricingFormulaSerializer
#     filter_backends = [OwnerByInstrumentFilter, DjangoFilterBackend, OrderingFilter]


# class AccrualCalculationScheduleViewSet(PomsViewSetBase):
#     queryset = AccrualCalculationSchedule.objects
#     serializer_class = AccrualCalculationScheduleSerializer
#     filter_backends = [OwnerByInstrumentFilter, DjangoFilterBackend, OrderingFilter]


# class InstrumentFactorScheduleViewSet(PomsViewSetBase):
#     queryset = InstrumentFactorSchedule.objects
#     serializer_class = InstrumentFactorScheduleSerializer
#     filter_backends = [OwnerByInstrumentFilter, DjangoFilterBackend, OrderingFilter]


# class EventScheduleViewSet(PomsViewSetBase):
#     queryset = EventSchedule.objects
#     serializer_class = EventScheduleSerializer
#     filter_backends = [OwnerByInstrumentFilter, DjangoFilterBackend, OrderingFilter]
