from __future__ import unicode_literals

import django_filters
from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter, FilterSet
from rest_framework.permissions import IsAuthenticated

from poms.common.filters import ClassifierFilterSetBase
from poms.common.views import PomsClassViewSetBase, ClassifierViewSetBase, PomsViewSetBase
from poms.instruments.filters import OwnerByInstrumentFilter
from poms.instruments.models import InstrumentClassifier, Instrument, PriceHistory, InstrumentClass, DailyPricingModel, \
    AccrualCalculationModel, PaymentSizeDetail, PeriodicityPeriod, CostMethod, InstrumentType, InstrumentAttributeType, \
    ManualPricingFormula, AccrualCalculationSchedule, InstrumentFactorSchedule, EventSchedule, PricingPolicy
from poms.instruments.serializers import InstrumentClassifierSerializer, InstrumentSerializer, PriceHistorySerializer, \
    InstrumentClassSerializer, DailyPricingModelSerializer, AccrualCalculationModelSerializer, \
    PaymentSizeDetailSerializer, PeriodicityPeriodSerializer, CostMethodSerializer, InstrumentTypeSerializer, \
    InstrumentAttributeTypeSerializer, ManualPricingFormulaSerializer, AccrualCalculationScheduleSerializer, \
    InstrumentFactorScheduleSerializer, EventScheduleSerializer, PricingPolicySerializer
from poms.obj_attrs.views import AttributeTypeViewSetBase
from poms.users.filters import OwnerByMasterUserFilter


class InstrumentClassViewSet(PomsClassViewSetBase):
    queryset = InstrumentClass.objects.all()
    serializer_class = InstrumentClassSerializer


class DailyPricingModelViewSet(PomsClassViewSetBase):
    queryset = DailyPricingModel.objects.all()
    serializer_class = DailyPricingModelSerializer


class AccrualCalculationModelClassViewSet(PomsClassViewSetBase):
    queryset = AccrualCalculationModel.objects.all()
    serializer_class = AccrualCalculationModelSerializer


class PaymentSizeDetailViewSet(PomsClassViewSetBase):
    queryset = PaymentSizeDetail.objects.all()
    serializer_class = PaymentSizeDetailSerializer


class PeriodicityPeriodViewSet(PomsClassViewSetBase):
    queryset = PeriodicityPeriod.objects.all()
    serializer_class = PeriodicityPeriodSerializer


class CostMethodViewSet(PomsClassViewSetBase):
    queryset = CostMethod.objects.all()
    serializer_class = CostMethodSerializer


class InstrumentTypeViewSet(PomsViewSetBase):
    queryset = InstrumentType.objects.all()
    serializer_class = InstrumentTypeSerializer
    filter_backends = [OwnerByMasterUserFilter, DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']


class InstrumentClassifierFilterSet(ClassifierFilterSetBase):
    class Meta(ClassifierFilterSetBase.Meta):
        model = InstrumentClassifier


class InstrumentClassifierViewSet(ClassifierViewSetBase):
    queryset = InstrumentClassifier.objects.all()
    serializer_class = InstrumentClassifierSerializer
    filter_class = InstrumentClassifierFilterSet


class PricingPolicyViewSet(PomsViewSetBase):
    queryset = PricingPolicy.objects.all()
    serializer_class = PricingPolicySerializer
    filter_backends = [OwnerByMasterUserFilter, DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']


class InstrumentAttributeTypeViewSet(AttributeTypeViewSetBase):
    queryset = InstrumentAttributeType.objects.all()
    serializer_class = InstrumentAttributeTypeSerializer


class InstrumentViewSet(PomsViewSetBase):
    queryset = Instrument.objects.prefetch_related('attributes', 'attributes__attribute_type').all()
    serializer_class = InstrumentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [OwnerByMasterUserFilter, DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']


class PriceHistoryFilterSet(FilterSet):
    instrument = django_filters.Filter(name='instrument')
    min_date = django_filters.DateFilter(name='date', lookup_type='gte')
    max_date = django_filters.DateFilter(name='date', lookup_type='lte')

    class Meta:
        model = PriceHistory
        fields = ['instrument', 'min_date', 'max_date']


class PriceHistoryViewSet(PomsViewSetBase):
    queryset = PriceHistory.objects.all()
    serializer_class = PriceHistorySerializer
    filter_backends = [OwnerByInstrumentFilter, DjangoFilterBackend, OrderingFilter]
    filter_class = PriceHistoryFilterSet
    ordering_fields = ['-date']


class ManualPricingFormulaViewSet(PomsViewSetBase):
    queryset = ManualPricingFormula.objects.all()
    serializer_class = ManualPricingFormulaSerializer
    filter_backends = [OwnerByInstrumentFilter, DjangoFilterBackend, OrderingFilter]


class AccrualCalculationScheduleViewSet(PomsViewSetBase):
    queryset = AccrualCalculationSchedule.objects.all()
    serializer_class = AccrualCalculationScheduleSerializer
    filter_backends = [OwnerByInstrumentFilter, DjangoFilterBackend, OrderingFilter]


class InstrumentFactorScheduleViewSet(PomsViewSetBase):
    queryset = InstrumentFactorSchedule.objects.all()
    serializer_class = InstrumentFactorScheduleSerializer
    filter_backends = [OwnerByInstrumentFilter, DjangoFilterBackend, OrderingFilter]


class EventScheduleViewSet(PomsViewSetBase):
    queryset = EventSchedule.objects.all()
    serializer_class = EventScheduleSerializer
    filter_backends = [OwnerByInstrumentFilter, DjangoFilterBackend, OrderingFilter]
