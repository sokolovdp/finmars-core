from __future__ import unicode_literals

import django_filters
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.decorators import list_route, detail_route
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.filters import FilterSet
from rest_framework.response import Response

from poms.common.filters import CharFilter, ModelWithPermissionMultipleChoiceFilter, NoOpFilter
from poms.common.views import AbstractClassModelViewSet, AbstractModelViewSet
from poms.instruments.filters import OwnerByInstrumentFilter, PriceHistoryObjectPermissionFilter
from poms.instruments.models import Instrument, PriceHistory, InstrumentClass, DailyPricingModel, \
    AccrualCalculationModel, PaymentSizeDetail, Periodicity, CostMethod, InstrumentType, InstrumentAttributeType, \
    PricingPolicy, InstrumentClassifier, EventScheduleConfig
from poms.instruments.serializers import InstrumentSerializer, PriceHistorySerializer, \
    InstrumentClassSerializer, DailyPricingModelSerializer, AccrualCalculationModelSerializer, \
    PaymentSizeDetailSerializer, PeriodicitySerializer, CostMethodSerializer, InstrumentTypeSerializer, \
    InstrumentAttributeTypeSerializer, PricingPolicySerializer, InstrumentClassifierNodeSerializer, \
    EventScheduleConfigSerializer, InstrumentCalculatePricesAccruedPriceSerializer
from poms.obj_attrs.filters import AttributeTypeValueTypeFilter
from poms.obj_attrs.views import AbstractAttributeTypeViewSet, AbstractClassifierViewSet
from poms.obj_perms.filters import ObjectPermissionMemberFilter, ObjectPermissionGroupFilter, \
    ObjectPermissionPermissionFilter
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


class PeriodicityViewSet(AbstractClassModelViewSet):
    queryset = Periodicity.objects
    serializer_class = PeriodicitySerializer


class CostMethodViewSet(AbstractClassModelViewSet):
    queryset = CostMethod.objects
    serializer_class = CostMethodSerializer


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
    id = NoOpFilter()
    is_deleted = django_filters.BooleanFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    instrument_class = django_filters.ModelMultipleChoiceFilter(queryset=InstrumentClass.objects)
    tag = TagFilter(model=InstrumentType)
    member = ObjectPermissionMemberFilter(object_permission_model=InstrumentType)
    member_group = ObjectPermissionGroupFilter(object_permission_model=InstrumentType)
    permission = ObjectPermissionPermissionFilter(object_permission_model=InstrumentType)

    class Meta:
        model = InstrumentType
        fields = []


class InstrumentTypeViewSet(AbstractWithObjectPermissionViewSet):
    queryset = InstrumentType.objects.prefetch_related('master_user')
    serializer_class = InstrumentTypeSerializer
    # bulk_objects_permissions_serializer_class = InstrumentTypeBulkObjectPermissionSerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        TagFilterBackend,
    ]
    filter_class = InstrumentTypeFilterSet
    ordering_fields = [
        'user_code', 'name', 'short_name',
    ]
    search_fields = [
        'user_code', 'name', 'short_name',
    ]
    # has_feature_is_deleted = True


class InstrumentAttributeTypeFilterSet(FilterSet):
    id = NoOpFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    value_type = AttributeTypeValueTypeFilter()
    member = ObjectPermissionMemberFilter(object_permission_model=InstrumentAttributeType)
    member_group = ObjectPermissionGroupFilter(object_permission_model=InstrumentAttributeType)
    permission = ObjectPermissionPermissionFilter(object_permission_model=InstrumentAttributeType)

    class Meta:
        model = InstrumentAttributeType
        fields = []


class InstrumentAttributeTypeViewSet(AbstractAttributeTypeViewSet):
    queryset = InstrumentAttributeType.objects.prefetch_related('classifiers')
    serializer_class = InstrumentAttributeTypeSerializer
    # bulk_objects_permissions_serializer_class = InstrumentAttributeTypeBulkObjectPermissionSerializer
    filter_class = InstrumentAttributeTypeFilterSet


class InstrumentClassifierFilterSet(FilterSet):
    id = NoOpFilter()
    name = CharFilter()
    level = django_filters.NumberFilter()
    attribute_type = ModelWithPermissionMultipleChoiceFilter(model=InstrumentAttributeType)

    class Meta:
        model = InstrumentClassifier
        fields = []


class InstrumentClassifierViewSet(AbstractClassifierViewSet):
    queryset = InstrumentClassifier.objects
    serializer_class = InstrumentClassifierNodeSerializer
    filter_class = InstrumentClassifierFilterSet


class InstrumentFilterSet(FilterSet):
    id = NoOpFilter()
    is_deleted = django_filters.BooleanFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    user_text_1 = CharFilter()
    user_text_2 = CharFilter()
    user_text_3 = CharFilter()
    reference_for_pricing = CharFilter()
    instrument_type = ModelWithPermissionMultipleChoiceFilter(model=InstrumentType)
    tag = TagFilter(model=Instrument)
    member = ObjectPermissionMemberFilter(object_permission_model=InstrumentAttributeType)
    member_group = ObjectPermissionGroupFilter(object_permission_model=InstrumentAttributeType)
    permission = ObjectPermissionPermissionFilter(object_permission_model=InstrumentAttributeType)

    class Meta:
        model = Instrument
        fields = []


class InstrumentViewSet(AbstractWithObjectPermissionViewSet):
    queryset = Instrument.objects.prefetch_related(
        'instrument_type', 'pricing_currency', 'accrued_currency', 'attributes', 'attributes__attribute_type',
        'manual_pricing_formulas', 'accrual_calculation_schedules', 'factor_schedules',
        'event_schedules', 'event_schedules__actions')
    serializer_class = InstrumentSerializer
    # bulk_objects_permissions_serializer_class = InstrumentBulkObjectPermissionSerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        TagFilterBackend,
    ]
    filter_class = InstrumentFilterSet
    ordering_fields = [
        'user_code', 'name', 'short_name', 'reference_for_pricing',
        'instrument_type__user_code', 'instrument_type__name', 'instrument_type__short_name']
    search_fields = [
        'user_code', 'name', 'short_name', 'reference_for_pricing',
    ]

    # has_feature_is_deleted = True

    @list_route(methods=['post'], url_path='rebuild-events', serializer_class=serializers.Serializer)
    def rebuild_all_events(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        processed = 0
        for instance in queryset:
            try:
                instance.rebuild_event_schedules()
            except ValueError as e:
                pass
            processed += 1
        return Response({'processed': processed})

    @detail_route(methods=['put', 'patch'], url_path='rebuild-events', serializer_class=serializers.Serializer)
    def rebuild_events(self, request, pk):
        instance = self.get_object()
        try:
            instance.rebuild_event_schedules()
        except ValueError as e:
            pass
        return Response({'processed': 1})

    @list_route(methods=['post'], url_path='recalculate-prices-accrued-price',
                serializer_class=InstrumentCalculatePricesAccruedPriceSerializer)
    def calculate_prices_accrued_price(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        begin_date = serializer.validated_data['begin_date']
        end_date = serializer.validated_data['end_date']

        instruments = Instrument.objects.filter(master_user=request.user.master_user)
        # instruments = self.filter_queryset(self.get_queryset())
        for instrument in instruments:
            instrument.calculate_prices_accrued_price(begin_date, end_date)
        return Response(serializer.data)


class PriceHistoryFilterSet(FilterSet):
    id = NoOpFilter()
    date = django_filters.DateFromToRangeFilter()
    instrument = ModelWithPermissionMultipleChoiceFilter(model=Instrument)

    class Meta:
        model = PriceHistory
        fields = []


class PriceHistoryViewSet(AbstractModelViewSet):
    queryset = PriceHistory.objects.prefetch_related(
        'instrument',
        'instrument__user_object_permissions', 'instrument__user_object_permissions__permission',
        'instrument__group_object_permissions', 'instrument__group_object_permissions__permission',
    )
    serializer_class = PriceHistorySerializer
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByInstrumentFilter,
        PriceHistoryObjectPermissionFilter,
    ]
    filter_class = PriceHistoryFilterSet
    ordering_fields = [
        'date',
        'instrument__user_code', 'instrument__name', 'instrument__short_name',
    ]
    search_fields = [
        'instrument__user_code', 'instrument__name', 'instrument__short_name',
    ]

    # @list_route(methods=['post'], url_path='recalculate-prices-accrued-price', serializer_class=serializers.Serializer)
    # def calculate_prices_accrued_price(self, request):
    #     queryset = self.filter_queryset(self.get_queryset())
    #     instrument_accruals = {}
    #     processed = 0
    #     for p in queryset:
    #         accruals = instrument_accruals.get(p.instrument_id, None)
    #         if accruals is None:
    #             accruals = list(p.instrument.accrual_calculation_schedules.order_by('accrual_start_date'))
    #             if accruals is None:
    #                 accruals = []
    #             instrument_accruals.get(p.instrument_id, accruals)
    #         p.calculate_accrued_price(accruals=accruals, save=True)
    #         processed += 1
    #     return Response({'processed': processed})


class EventScheduleConfigViewSet(AbstractModelViewSet):
    queryset = EventScheduleConfig.objects
    serializer_class = EventScheduleConfigSerializer
    permission_classes = AbstractModelViewSet.permission_classes + [
        SuperUserOrReadOnly,
    ]
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]

    def get_object(self):
        try:
            return self.request.user.master_user.instrument_event_schedule_config
        except ObjectDoesNotExist:
            obj = EventScheduleConfig.create_default(master_user=self.request.user.master_user)
            return obj

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed(method=request.method)
