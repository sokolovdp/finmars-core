from __future__ import unicode_literals

import django_filters
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Prefetch
from rest_framework import serializers
from rest_framework.decorators import list_route, detail_route
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.filters import FilterSet
from rest_framework.response import Response

from poms.common.filters import CharFilter, ModelExtWithPermissionMultipleChoiceFilter, NoOpFilter, \
    ModelExtMultipleChoiceFilter
from poms.common.views import AbstractClassModelViewSet, AbstractModelViewSet
from poms.currencies.models import Currency
from poms.instruments.filters import OwnerByInstrumentFilter, PriceHistoryObjectPermissionFilter
from poms.instruments.models import Instrument, PriceHistory, InstrumentClass, DailyPricingModel, \
    AccrualCalculationModel, PaymentSizeDetail, Periodicity, CostMethod, InstrumentType, InstrumentAttributeType, \
    PricingPolicy, InstrumentClassifier, EventScheduleConfig, InstrumentAttribute, ManualPricingFormula, \
    AccrualCalculationSchedule, EventSchedule, EventScheduleAction
from poms.instruments.serializers import InstrumentSerializer, PriceHistorySerializer, \
    InstrumentClassSerializer, DailyPricingModelSerializer, AccrualCalculationModelSerializer, \
    PaymentSizeDetailSerializer, PeriodicitySerializer, CostMethodSerializer, InstrumentTypeSerializer, \
    InstrumentAttributeTypeSerializer, PricingPolicySerializer, InstrumentClassifierNodeSerializer, \
    EventScheduleConfigSerializer, InstrumentCalculatePricesAccruedPriceSerializer
from poms.instruments.tasks import calculate_prices_accrued_price_async, calculate_prices_accrued_price
from poms.integrations.models import PriceDownloadScheme
from poms.obj_attrs.filters import AttributeTypeValueTypeFilter
from poms.obj_attrs.views import AbstractAttributeTypeViewSet, AbstractClassifierViewSet
from poms.obj_perms.filters import ObjectPermissionMemberFilter, ObjectPermissionGroupFilter, \
    ObjectPermissionPermissionFilter
from poms.obj_perms.utils import get_permissions_prefetch_lookups
from poms.obj_perms.views import AbstractWithObjectPermissionViewSet
from poms.tags.filters import TagFilter
from poms.tags.models import Tag
from poms.transactions.models import TransactionType, TransactionTypeGroup
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
    ordering_fields = [
        'user_code', 'name', 'short_name', 'public_name'
    ]


class InstrumentTypeFilterSet(FilterSet):
    id = NoOpFilter()
    is_deleted = django_filters.BooleanFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    public_name = CharFilter()
    instrument_class = django_filters.ModelMultipleChoiceFilter(queryset=InstrumentClass.objects)
    one_off_event = ModelExtWithPermissionMultipleChoiceFilter(model=TransactionType)
    regular_event = ModelExtWithPermissionMultipleChoiceFilter(model=TransactionType)
    factor_same = ModelExtWithPermissionMultipleChoiceFilter(model=TransactionType)
    factor_up = ModelExtWithPermissionMultipleChoiceFilter(model=TransactionType)
    factor_down = ModelExtWithPermissionMultipleChoiceFilter(model=TransactionType)
    tag = TagFilter(model=InstrumentType)
    member = ObjectPermissionMemberFilter(object_permission_model=InstrumentType)
    member_group = ObjectPermissionGroupFilter(object_permission_model=InstrumentType)
    permission = ObjectPermissionPermissionFilter(object_permission_model=InstrumentType)

    class Meta:
        model = InstrumentType
        fields = []


class InstrumentTypeViewSet(AbstractWithObjectPermissionViewSet):
    queryset = InstrumentType.objects.select_related(
        'master_user', 'instrument_class',
        'one_off_event', 'one_off_event__group',
        'regular_event', 'regular_event__group',
        'factor_same', 'factor_same__group',
        'factor_up', 'factor_up__group',
        'factor_down', 'factor_down__group',
    ).prefetch_related(
        'tags',
        *get_permissions_prefetch_lookups(
            (None, InstrumentType),
            ('one_off_event', TransactionType),
            ('one_off_event__group', TransactionTypeGroup),
            ('regular_event', TransactionType),
            ('regular_event__group', TransactionTypeGroup),
            ('factor_same', TransactionType),
            ('factor_same__group', TransactionTypeGroup),
            ('factor_up', TransactionType),
            ('factor_up__group', TransactionTypeGroup),
            ('factor_down', TransactionType),
            ('factor_down__group', TransactionTypeGroup),
            ('tags', Tag)
        )
    )
    serializer_class = InstrumentTypeSerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]
    filter_class = InstrumentTypeFilterSet
    ordering_fields = [
        'user_code', 'name', 'short_name', 'public_name',
    ]


class InstrumentAttributeTypeFilterSet(FilterSet):
    id = NoOpFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    public_name = CharFilter()
    value_type = AttributeTypeValueTypeFilter()
    member = ObjectPermissionMemberFilter(object_permission_model=InstrumentAttributeType)
    member_group = ObjectPermissionGroupFilter(object_permission_model=InstrumentAttributeType)
    permission = ObjectPermissionPermissionFilter(object_permission_model=InstrumentAttributeType)

    class Meta:
        model = InstrumentAttributeType
        fields = []


class InstrumentAttributeTypeViewSet(AbstractAttributeTypeViewSet):
    queryset = InstrumentAttributeType.objects.select_related(
        'master_user'
    ).prefetch_related(
        'classifiers',
        *get_permissions_prefetch_lookups(
            (None, InstrumentAttributeType)
        )
    )
    serializer_class = InstrumentAttributeTypeSerializer
    filter_class = InstrumentAttributeTypeFilterSet


class InstrumentClassifierFilterSet(FilterSet):
    id = NoOpFilter()
    name = CharFilter()
    level = django_filters.NumberFilter()
    attribute_type = ModelExtWithPermissionMultipleChoiceFilter(model=InstrumentAttributeType)

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
    public_name = CharFilter()
    short_name = CharFilter()
    instrument_type = ModelExtWithPermissionMultipleChoiceFilter(model=InstrumentType)
    instrument_type__instrument_class = django_filters.ModelMultipleChoiceFilter(queryset=InstrumentClass.objects)
    pricing_currency = ModelExtMultipleChoiceFilter(model=Currency)
    price_multiplier = django_filters.RangeFilter()
    accrued_currency = ModelExtMultipleChoiceFilter(model=Currency)
    accrued_multiplier = django_filters.RangeFilter()
    payment_size_detail = django_filters.ModelMultipleChoiceFilter(queryset=PaymentSizeDetail.objects)
    default_price = django_filters.RangeFilter()
    default_accrued = django_filters.RangeFilter()
    user_text_1 = CharFilter()
    user_text_2 = CharFilter()
    user_text_3 = CharFilter()
    reference_for_pricing = CharFilter()
    daily_pricing_model = django_filters.ModelMultipleChoiceFilter(queryset=DailyPricingModel.objects)
    price_download_scheme = ModelExtMultipleChoiceFilter(model=PriceDownloadScheme, field_name='scheme_name')
    maturity_date = django_filters.DateFromToRangeFilter()
    tag = TagFilter(model=Instrument)
    member = ObjectPermissionMemberFilter(object_permission_model=Instrument)
    member_group = ObjectPermissionGroupFilter(object_permission_model=Instrument)
    permission = ObjectPermissionPermissionFilter(object_permission_model=Instrument)

    class Meta:
        model = Instrument
        fields = []


class InstrumentViewSet(AbstractWithObjectPermissionViewSet):
    queryset = Instrument.objects.select_related(
        'instrument_type', 'instrument_type__instrument_class', 'pricing_currency', 'accrued_currency',
        'payment_size_detail', 'daily_pricing_model', 'price_download_scheme', 'price_download_scheme__provider',
    ).prefetch_related(
        Prefetch(
            'attributes',
            queryset=InstrumentAttribute.objects.select_related('attribute_type', 'classifier')
        ),
        Prefetch(
            'manual_pricing_formulas',
            queryset=ManualPricingFormula.objects.select_related('pricing_policy')
        ),
        Prefetch(
            'accrual_calculation_schedules',
            queryset=AccrualCalculationSchedule.objects.select_related('accrual_calculation_model', 'periodicity')
        ),
        'factor_schedules',
        Prefetch(
            'event_schedules',
            queryset=EventSchedule.objects.select_related(
                'event_class', 'notification_class', 'periodicity'
            ).prefetch_related(
                Prefetch(
                    'actions',
                    queryset=EventScheduleAction.objects.select_related(
                        'transaction_type',
                        'transaction_type__group'
                    ).prefetch_related(
                        *get_permissions_prefetch_lookups(
                            ('transaction_type', TransactionType),
                            ('transaction_type__group', TransactionTypeGroup)
                        )
                    )
                ),
            )),
        'tags',
        *get_permissions_prefetch_lookups(
            (None, Instrument),
            ('tags', Tag),
            ('instrument_type', InstrumentType),
            ('attributes__attribute_type', InstrumentAttributeType),
        )
    )
    serializer_class = InstrumentSerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]
    filter_class = InstrumentFilterSet
    ordering_fields = [
        'user_code', 'name', 'short_name', 'public_name', 'reference_for_pricing',
        'instrument_type', 'instrument_type__user_code', 'instrument_type__name', 'instrument_type__short_name',
        'instrument_type__public_name',
        'pricing_currency', 'pricing_currency__user_code', 'pricing_currency__name', 'pricing_currency__short_name',
        'pricing_currency__public_name', 'price_multiplier',
        'accrued_currency', 'accrued_currency__user_code', 'accrued_currency__name', 'accrued_currency__short_name',
        'accrued_currency__public_name', 'accrued_multiplier',
        'default_price', 'default_accrued', 'user_text_1', 'user_text_2', 'user_text_3',
        'reference_for_pricing',
        'maturity_date',
    ]

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

        # instruments = Instrument.objects.filter(master_user=request.user.master_user)
        # instruments = self.filter_queryset(self.get_queryset())
        # for instrument in instruments:
        #     instrument.calculate_prices_accrued_price(begin_date, end_date)

        calculate_prices_accrued_price(master_user=request.user.master_user, begin_date=begin_date, end_date=end_date)
        # calculate_prices_accrued_price_async.apply_async(
        #     kwargs={
        #         'master_user': request.user.master_user.id,
        #         'begin_date': begin_date.toordinal(),
        #         'end_date': end_date.toordinal(),
        #     }
        # ).wait()

        return Response(serializer.data)


class PriceHistoryFilterSet(FilterSet):
    id = NoOpFilter()
    instrument = ModelExtWithPermissionMultipleChoiceFilter(model=Instrument)
    pricing_policy = ModelExtMultipleChoiceFilter(model=PricingPolicy)
    date = django_filters.DateFromToRangeFilter()
    principal_price = django_filters.RangeFilter()
    accrued_price = django_filters.RangeFilter()

    class Meta:
        model = PriceHistory
        fields = []


class PriceHistoryViewSet(AbstractModelViewSet):
    queryset = PriceHistory.objects.select_related(
        'instrument', 'instrument__instrument_type', 'instrument__instrument_type__instrument_class', 'pricing_policy'
    ).prefetch_related(
        *get_permissions_prefetch_lookups(
            ('instrument', Instrument),
            ('instrument__instrument_type', InstrumentType),
        )
    )
    serializer_class = PriceHistorySerializer
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByInstrumentFilter,
        PriceHistoryObjectPermissionFilter,
    ]
    filter_class = PriceHistoryFilterSet
    ordering_fields = [
        'instrument', 'instrument__user_code', 'instrument__name', 'instrument__short_name', 'instrument__public_name',
        'pricing_policy', 'pricing_policy__user_code', 'pricing_policy__name', 'pricing_policy__short_name',
        'pricing_policy__public_name',
        'date', 'principal_price', 'accrued_price',
    ]


class EventScheduleConfigViewSet(AbstractModelViewSet):
    queryset = EventScheduleConfig.objects.select_related('notification_class')
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
