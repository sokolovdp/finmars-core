from __future__ import unicode_literals

import django_filters
from rest_framework.filters import FilterSet

from poms.common.filters import CharFilter, ModelWithPermissionMultipleChoiceFilter, IsDefaultFilter
from poms.common.views import AbstractClassModelViewSet, AbstractModelViewSet
from poms.instruments.filters import OwnerByInstrumentFilter, PriceHistoryObjectPermissionFilter
from poms.instruments.models import Instrument, PriceHistory, InstrumentClass, DailyPricingModel, \
    AccrualCalculationModel, PaymentSizeDetail, PeriodicityPeriod, CostMethod, InstrumentType, InstrumentAttributeType, \
    PricingPolicy, PriceDownloadMode, InstrumentClassifier
from poms.instruments.serializers import InstrumentSerializer, PriceHistorySerializer, \
    InstrumentClassSerializer, DailyPricingModelSerializer, AccrualCalculationModelSerializer, \
    PaymentSizeDetailSerializer, PeriodicityPeriodSerializer, CostMethodSerializer, InstrumentTypeSerializer, \
    InstrumentAttributeTypeSerializer, PricingPolicySerializer, PriceDownloadModeSerializer, \
    InstrumentClassifierNodeSerializer
from poms.obj_attrs.filters import AttributePrefetchFilter
from poms.obj_attrs.views import AbstractAttributeTypeViewSet, AbstractClassifierViewSet
from poms.obj_perms.views import AbstractWithObjectPermissionViewSet
from poms.tags.filters import TagFilterBackend, TagFilter
from poms.users.filters import OwnerByMasterUserFilter
from poms.users.permissions import SuperUserOrReadOnly


class InstrumentClassViewSet(AbstractClassModelViewSet):
    queryset = InstrumentClass.objects
    serializer_class = InstrumentClassSerializer


class DailyPricingModelViewSet(AbstractClassModelViewSet):
    queryset = DailyPricingModel.objects
    serializer_class = DailyPricingModelSerializer


class AccrualCalculationModelClassViewSet(AbstractClassModelViewSet):
    queryset = AccrualCalculationModel.objects
    serializer_class = AccrualCalculationModelSerializer


class PaymentSizeDetailViewSet(AbstractClassModelViewSet):
    queryset = PaymentSizeDetail.objects
    serializer_class = PaymentSizeDetailSerializer


class PeriodicityPeriodViewSet(AbstractClassModelViewSet):
    queryset = PeriodicityPeriod.objects
    serializer_class = PeriodicityPeriodSerializer


class CostMethodViewSet(AbstractClassModelViewSet):
    queryset = CostMethod.objects
    serializer_class = CostMethodSerializer


class PriceDownloadModeViewSet(AbstractClassModelViewSet):
    queryset = PriceDownloadMode.objects
    serializer_class = PriceDownloadModeSerializer


class PricingPolicyViewSet(AbstractModelViewSet):
    queryset = PricingPolicy.objects
    serializer_class = PricingPolicySerializer
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]
    permission_classes = AbstractModelViewSet.permission_classes + [
        SuperUserOrReadOnly,
    ]
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']


class InstrumentTypeFilterSet(FilterSet):
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    is_default = IsDefaultFilter(source='instrument_type')
    tag = TagFilter(model=InstrumentType)

    class Meta:
        model = InstrumentType
        fields = ['user_code', 'name', 'short_name', 'is_default', 'tag']


class InstrumentTypeViewSet(AbstractWithObjectPermissionViewSet):
    queryset = InstrumentType.objects.select_related('master_user')
    serializer_class = InstrumentTypeSerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        TagFilterBackend,
    ]
    filter_class = InstrumentTypeFilterSet
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']


class InstrumentAttributeTypeFilterSet(FilterSet):
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()

    class Meta:
        model = InstrumentAttributeType
        fields = ['user_code', 'name', 'short_name']


class InstrumentAttributeTypeViewSet(AbstractAttributeTypeViewSet):
    queryset = InstrumentAttributeType.objects.prefetch_related('classifiers')
    serializer_class = InstrumentAttributeTypeSerializer
    filter_class = InstrumentAttributeTypeFilterSet


class InstrumentClassifierFilterSet(FilterSet):
    name = CharFilter()
    attribute_type = ModelWithPermissionMultipleChoiceFilter(model=InstrumentAttributeType)

    # parent = ModelWithPermissionMultipleChoiceFilter(model=InstrumentClassifier, master_user_path='attribute_type__master_user')

    class Meta:
        model = InstrumentClassifier
        fields = ['name', 'level', 'attribute_type', ]


class InstrumentClassifierViewSet(AbstractClassifierViewSet):
    queryset = InstrumentClassifier.objects
    serializer_class = InstrumentClassifierNodeSerializer
    filter_class = InstrumentClassifierFilterSet


class InstrumentFilterSet(FilterSet):
    isin = CharFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    user_text_1 = CharFilter()
    user_text_2 = CharFilter()
    user_text_3 = CharFilter()
    instrument_type = ModelWithPermissionMultipleChoiceFilter(model=InstrumentType)
    tag = TagFilter(model=Instrument)

    class Meta:
        model = Instrument
        fields = ['isin', 'user_code', 'name', 'short_name', 'user_text_1', 'user_text_2', 'user_text_3', 'tag']


class InstrumentViewSet(AbstractWithObjectPermissionViewSet):
    queryset = Instrument.objects.select_related('instrument_type', 'pricing_currency', 'accrued_currency'). \
        prefetch_related('manual_pricing_formulas', 'accrual_calculation_schedules', 'factor_schedules',
                         'event_schedules')
    serializer_class = InstrumentSerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        AttributePrefetchFilter,
        TagFilterBackend,
    ]
    filter_class = InstrumentFilterSet
    ordering_fields = ['isin', 'user_code', 'name', 'short_name',
                       'instrument_type__user_code', 'instrument_type__name', 'instrument_type__short_name']
    search_fields = ['isin', 'user_code', 'name', 'short_name',
                     'instrument_type__user_code', 'instrument_type__name', 'instrument_type__short_name']


class PriceHistoryFilterSet(FilterSet):
    instrument = ModelWithPermissionMultipleChoiceFilter(model=Instrument)
    date = django_filters.DateFromToRangeFilter()

    class Meta:
        model = PriceHistory
        fields = ['instrument', 'date', ]


class PriceHistoryViewSet(AbstractModelViewSet):
    queryset = PriceHistory.objects.select_related('instrument').prefetch_related(
        'instrument__user_object_permissions', 'instrument__user_object_permissions__permission',
        'instrument__group_object_permissions', 'instrument__group_object_permissions__permission',
    )
    serializer_class = PriceHistorySerializer
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByInstrumentFilter,
        PriceHistoryObjectPermissionFilter,
    ]
    filter_class = PriceHistoryFilterSet
    ordering_fields = ['-date']
    search_fields = ['instrument__user_code', 'instrument__name', 'instrument__short_name', ]
