from __future__ import unicode_literals

import django_filters
from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter, FilterSet

from poms.common.filters import CharFilter, ModelWithPermissionMultipleChoiceFilter
from poms.common.views import PomsClassViewSetBase, PomsViewSetBase
from poms.instruments.filters import OwnerByInstrumentFilter, PriceHistoryObjectPermissionFilter
from poms.instruments.models import Instrument, PriceHistory, InstrumentClass, DailyPricingModel, \
    AccrualCalculationModel, PaymentSizeDetail, PeriodicityPeriod, CostMethod, InstrumentType, InstrumentAttributeType, \
    PricingPolicy
from poms.instruments.serializers import InstrumentSerializer, PriceHistorySerializer, \
    InstrumentClassSerializer, DailyPricingModelSerializer, AccrualCalculationModelSerializer, \
    PaymentSizeDetailSerializer, PeriodicityPeriodSerializer, CostMethodSerializer, InstrumentTypeSerializer, \
    InstrumentAttributeTypeSerializer, PricingPolicySerializer
from poms.obj_attrs.filters import AttributePrefetchFilter
from poms.obj_attrs.views import AttributeTypeViewSetBase
from poms.obj_perms.views import AbstractViewSetWithObjectPermission
from poms.tags.filters import TagFilterBackend, TagFilter
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
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    tag = TagFilter(model=InstrumentType)

    class Meta:
        model = InstrumentType
        fields = ['user_code', 'name', 'short_name', 'tag']


class InstrumentTypeViewSet(AbstractViewSetWithObjectPermission):
    queryset = InstrumentType.objects
    serializer_class = InstrumentTypeSerializer
    filter_backends = [
        OwnerByMasterUserFilter,
        # ObjectPermissionBackend,
        TagFilterBackend,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    filter_class = InstrumentTypeFilterSet
    # permission_classes = PomsViewSetBase.permission_classes + [
    #     ObjectPermissionBase,
    # ]
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']

    # def get_serializer(self, *args, **kwargs):
    #     kwargs['show_object_permissions'] = (self.action != 'list')
    #     return super(InstrumentTypeViewSet, self).get_serializer(*args, **kwargs)


class InstrumentAttributeTypeFilterSet(FilterSet):
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()

    class Meta:
        model = InstrumentAttributeType
        fields = ['user_code', 'name', 'short_name']


class InstrumentAttributeTypeViewSet(AttributeTypeViewSetBase):
    queryset = InstrumentAttributeType.objects.prefetch_related('classifiers')
    serializer_class = InstrumentAttributeTypeSerializer
    # filter_backends = [
    #     OwnerByMasterUserFilter,
    #     # ObjectPermissionBackend,
    #     DjangoFilterBackend,
    #     OrderingFilter,
    #     SearchFilter,
    # ]
    filter_class = InstrumentAttributeTypeFilterSet
    # permission_classes = PomsViewSetBase.permission_classes + [
    #     ObjectPermissionBase,
    # ]
    # ordering_fields = ['user_code', 'name', 'short_name', ]
    # search_fields = ['user_code', 'name', 'short_name', ]

    # def get_serializer(self, *args, **kwargs):
    #     kwargs['show_object_permissions'] = (self.action != 'list')
    #     return super(InstrumentAttributeTypeViewSet, self).get_serializer(*args, **kwargs)


class InstrumentFilterSet(FilterSet):
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
        fields = ['user_code', 'name', 'short_name', 'user_text_1', 'user_text_2', 'user_text_3', 'tag']


class InstrumentViewSet(AbstractViewSetWithObjectPermission):
    queryset = Instrument.objects.prefetch_related(
        'pricing_currency', 'accrued_currency', 'manual_pricing_formulas', 'accrual_calculation_schedules',
        'factor_schedules', 'event_schedules')
    serializer_class = InstrumentSerializer
    filter_backends = [
        OwnerByMasterUserFilter,
        # ObjectPermissionBackend,
        AttributePrefetchFilter,
        TagFilterBackend,
        DjangoFilterBackend,
        OrderingFilter,
        # OrderingWithAttributesFilter,
        SearchFilter,
    ]
    filter_class = InstrumentFilterSet
    # permission_classes = PomsViewSetBase.permission_classes + [
    #     ObjectPermissionBase
    # ]
    ordering_fields = ['user_code', 'name', 'short_name', 'instrument_type__user_code', 'instrument_type__name',
                       'instrument_type__short_name']
    search_fields = ['user_code', 'name', 'short_name', 'instrument_type__user_code', 'instrument_type__name',
                     'instrument_type__short_name']

    def get_serializer(self, *args, **kwargs):
        kwargs['show_object_permissions'] = (self.action != 'list')
        return super(InstrumentViewSet, self).get_serializer(*args, **kwargs)


class PriceHistoryFilterSet(FilterSet):
    instrument = ModelWithPermissionMultipleChoiceFilter(model=Instrument)
    date = django_filters.DateFromToRangeFilter()

    class Meta:
        model = PriceHistory
        fields = ['instrument', 'date', ]


class PriceHistoryViewSet(PomsViewSetBase):
    queryset = PriceHistory.objects.prefetch_related(
        'instrument',
        'instrument__user_object_permissions', 'instrument__user_object_permissions__permission',
        'instrument__group_object_permissions', 'instrument__group_object_permissions__permission',
    )
    serializer_class = PriceHistorySerializer
    filter_backends = [
        OwnerByInstrumentFilter,
        PriceHistoryObjectPermissionFilter,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    filter_class = PriceHistoryFilterSet
    ordering_fields = ['-date']
    search_fields = ['instrument__user_code', 'instrument__name', 'instrument__short_name', ]
