from __future__ import unicode_literals

import django_filters
from rest_framework.decorators import detail_route
from rest_framework.filters import FilterSet, DjangoFilterBackend, OrderingFilter, SearchFilter
from rest_framework.response import Response

from poms.common.views import PomsClassViewSetBase, PomsViewSetBase
from poms.obj_attrs.filters import AttributePrefetchFilter
from poms.obj_attrs.views import AttributeTypeViewSetBase
from poms.obj_perms.filters import ObjectPermissionBackend
from poms.obj_perms.permissions import ObjectPermissionBase
from poms.tags.filters import TagFakeFilter, TagFilterBackend
from poms.transactions.filters import TransactionObjectPermissionFilter
from poms.transactions.models import TransactionClass, Transaction, TransactionType, TransactionAttributeType, \
    TransactionTypeGroup
from poms.transactions.permissions import TransactionObjectPermission
from poms.transactions.processor import TransactionTypeProcessor
from poms.transactions.serializers import TransactionClassSerializer, TransactionSerializer, TransactionTypeSerializer, \
    TransactionAttributeTypeSerializer, TransactionTypeProcessSerializer, TransactionTypeGroupSerializer
from poms.users.filters import OwnerByMasterUserFilter


class TransactionClassViewSet(PomsClassViewSetBase):
    queryset = TransactionClass.objects
    serializer_class = TransactionClassSerializer


class TransactionTypeGroupFilterSet(FilterSet):
    user_code = django_filters.CharFilter(lookup_expr='icontains')
    name = django_filters.CharFilter(lookup_expr='icontains')
    short_name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = TransactionTypeGroup
        fields = ['user_code', 'name', 'short_name']


class TransactionTypeGroupViewSet(PomsViewSetBase):
    queryset = TransactionTypeGroup.objects
    serializer_class = TransactionTypeGroupSerializer
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionBackend,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    filter_class = TransactionTypeGroupFilterSet
    permission_classes = PomsViewSetBase.permission_classes + [
        ObjectPermissionBase,
    ]
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']


class TransactionTypeFilterSet(FilterSet):
    user_code = django_filters.CharFilter(lookup_expr='icontains')
    name = django_filters.CharFilter(lookup_expr='icontains')
    short_name = django_filters.CharFilter(lookup_expr='icontains')
    group = django_filters.Filter(name='group')
    tags = TagFakeFilter()

    class Meta:
        model = TransactionType
        fields = ['user_code', 'name', 'short_name', 'group', 'tags']

    @staticmethod
    def tags_filter(queryset, value):
        return queryset


class TransactionTypeViewSet(PomsViewSetBase):
    queryset = TransactionType.objects.prefetch_related(
        'inputs',
        'inputs__content_type',

        'actions',

        'actions__transactiontypeactioninstrument',
        'actions__transactiontypeactioninstrument__instrument_type',
        'actions__transactiontypeactioninstrument__instrument_type_input',
        'actions__transactiontypeactioninstrument__pricing_currency',
        'actions__transactiontypeactioninstrument__pricing_currency_input',
        'actions__transactiontypeactioninstrument__accrued_currency',
        'actions__transactiontypeactioninstrument__accrued_currency_input',
        'actions__transactiontypeactioninstrument__daily_pricing_model',
        'actions__transactiontypeactioninstrument__daily_pricing_model_input',
        'actions__transactiontypeactioninstrument__payment_size_detail',
        'actions__transactiontypeactioninstrument__payment_size_detail_input',

        'actions__transactiontypeactiontransaction',
        'actions__transactiontypeactiontransaction__portfolio',
        'actions__transactiontypeactiontransaction__portfolio_input',
        'actions__transactiontypeactiontransaction__instrument',
        'actions__transactiontypeactiontransaction__instrument_input',
        'actions__transactiontypeactiontransaction__instrument_phantom',
        'actions__transactiontypeactiontransaction__transaction_currency',
        'actions__transactiontypeactiontransaction__transaction_currency_input',
        'actions__transactiontypeactiontransaction__settlement_currency',
        'actions__transactiontypeactiontransaction__settlement_currency_input',
        'actions__transactiontypeactiontransaction__account_position',
        'actions__transactiontypeactiontransaction__account_position_input',
        'actions__transactiontypeactiontransaction__account_cash',
        'actions__transactiontypeactiontransaction__account_cash_input',
        'actions__transactiontypeactiontransaction__account_interim',
        'actions__transactiontypeactiontransaction__account_interim_input',
        'actions__transactiontypeactiontransaction__strategy1_position',
        'actions__transactiontypeactiontransaction__strategy1_position_input',
        'actions__transactiontypeactiontransaction__strategy2_position',
        'actions__transactiontypeactiontransaction__strategy2_position_input',
        'actions__transactiontypeactiontransaction__strategy3_position',
        'actions__transactiontypeactiontransaction__strategy3_position_input',
        'actions__transactiontypeactiontransaction__strategy3_position',
        'actions__transactiontypeactiontransaction__strategy3_position_input',
        'actions__transactiontypeactiontransaction__responsible',
        'actions__transactiontypeactiontransaction__responsible_input',
        'actions__transactiontypeactiontransaction__counterparty',
        'actions__transactiontypeactiontransaction__counterparty_input',
    )
    serializer_class = TransactionTypeSerializer
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionBackend,
        TagFilterBackend,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter
    ]
    permission_classes = PomsViewSetBase.permission_classes + [
        ObjectPermissionBase,
    ]
    filter_class = TransactionTypeFilterSet
    ordering_fields = ['user_code', 'name', 'short_name', 'group__user_code', 'group__name', 'group__short_name']
    search_fields = ['user_code', 'name', 'short_name', 'group__user_code', 'group__name', 'group__short_name']

    # def get_serializer(self, *args, **kwargs):
    #     if self.request.path.endswith('/process/') or self.request.path.endswith('/check/'):
    #         kwargs['context'] = self.get_serializer_context()
    #         return TransactionTypeProcessSerializer(transaction_type=self._detail_instance, **kwargs)
    #     else:
    #         return super(TransactionTypeViewSet, self).get_serializer(*args, **kwargs)

    def get_serializer_context(self):
        context = super(TransactionTypeViewSet, self).get_serializer_context()
        context['transaction_type'] = getattr(self, '_detail_instance', None)
        return context

    @detail_route(methods=['get', 'put'], url_path='process', serializer_class=TransactionTypeProcessSerializer)
    def process(self, request, pk=None):
        return self.process_or_check(request, False)

    @detail_route(methods=['get', 'put'], url_path='check', serializer_class=TransactionTypeProcessSerializer)
    def check(self, request, pk=None):
        return self.process_or_check(request, True)

    def process_or_check(self, request, check_mode=True):
        self._detail_instance = self.get_object()
        if request.method == 'GET':
            serializer = TransactionTypeProcessSerializer(transaction_type=self._detail_instance,
                                                          context=self.get_serializer_context())
            return Response(serializer.data)
        else:
            from poms.instruments.serializers import InstrumentSerializer

            serializer = TransactionTypeProcessSerializer(transaction_type=self._detail_instance,
                                                          data=request.data,
                                                          context=self.get_serializer_context())
            serializer.is_valid(raise_exception=True)
            processor = TransactionTypeProcessor(self._detail_instance, serializer.validated_data)
            instruments, transactions = processor.run(check_mode)
            instruments_s = []
            transactions_s = []
            for i in instruments:
                s = InstrumentSerializer(instance=i, context=self.get_serializer_context())
                instruments_s.append(s.data)
            for t in transactions:
                s = TransactionSerializer(instance=t, context=self.get_serializer_context())
                transactions_s.append(s.data)
            d = serializer.data.copy()
            d['instruments'] = instruments_s
            d['transactions'] = transactions_s
            return Response(d)


class TransactionAttributeTypeFilterSet(FilterSet):
    user_code = django_filters.CharFilter(lookup_expr='icontains')
    name = django_filters.CharFilter(lookup_expr='icontains')
    short_name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = TransactionAttributeType
        fields = ['user_code', 'name', 'short_name']


class TransactionAttributeTypeViewSet(AttributeTypeViewSetBase):
    queryset = TransactionAttributeType.objects
    serializer_class = TransactionAttributeTypeSerializer
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionBackend,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    filter_class = TransactionAttributeTypeFilterSet
    permission_classes = PomsViewSetBase.permission_classes + [
        ObjectPermissionBase,
    ]
    ordering_fields = ['user_code', 'name', 'short_name', ]
    search_fields = ['user_code', 'name', 'short_name', ]


class TransactionFilterSet(FilterSet):
    transaction_code = django_filters.NumericRangeFilter()
    transaction_date = django_filters.DateFromToRangeFilter()
    accounting_date = django_filters.DateFromToRangeFilter()
    cash_date = django_filters.DateFromToRangeFilter()
    complex_transaction = django_filters.Filter(name='complex_transaction')

    class Meta:
        model = Transaction
        fields = ['transaction_code', 'transaction_date', 'accounting_date', 'cash_date']


class TransactionViewSet(PomsViewSetBase):
    # queryset = Transaction.objects
    queryset = Transaction.objects.select_related(
        'master_user',
        'complex_transaction', 'complex_transaction__transaction_type',
        'transaction_class',
        'instrument', 'transaction_currency', 'settlement_currency',
        'portfolio', 'account_cash', 'account_position', 'account_interim',
        'strategy1_position', 'strategy1_cash',
        'strategy2_position', 'strategy2_cash',
        'strategy3_position', 'strategy3_cash'
    ).prefetch_related(
        'portfolio__user_object_permissions', 'portfolio__user_object_permissions__permission',
        'portfolio__group_object_permissions', 'portfolio__group_object_permissions__permission',
        'instrument__user_object_permissions', 'instrument__user_object_permissions__permission',
        'instrument__group_object_permissions', 'instrument__group_object_permissions__permission',
        'account_cash__user_object_permissions', 'account_cash__user_object_permissions__permission',
        'account_cash__group_object_permissions', 'account_cash__group_object_permissions__permission',
        'account_position__user_object_permissions', 'account_position__user_object_permissions__permission',
        'account_position__group_object_permissions', 'account_position__group_object_permissions__permission',
        'account_interim__user_object_permissions', 'account_interim__user_object_permissions__permission',
        'account_interim__group_object_permissions', 'account_interim__group_object_permissions__permission',
        'strategy1_position__user_object_permissions', 'strategy1_position__user_object_permissions__permission',
        'strategy1_position__group_object_permissions', 'strategy1_position__group_object_permissions__permission',
        'strategy1_cash__user_object_permissions', 'strategy1_cash__user_object_permissions__permission',
        'strategy1_cash__group_object_permissions', 'strategy1_cash__group_object_permissions__permission',
        'strategy2_position__user_object_permissions', 'strategy2_position__user_object_permissions__permission',
        'strategy2_position__group_object_permissions', 'strategy2_position__group_object_permissions__permission',
        'strategy2_cash__user_object_permissions', 'strategy2_cash__user_object_permissions__permission',
        'strategy2_cash__group_object_permissions', 'strategy2_cash__group_object_permissions__permission',
        'strategy3_position__user_object_permissions', 'strategy3_position__user_object_permissions__permission',
        'strategy3_position__group_object_permissions', 'strategy3_position__group_object_permissions__permission',
        'strategy3_cash__user_object_permissions', 'strategy3_cash__user_object_permissions__permission',
        'strategy3_cash__group_object_permissions', 'strategy3_cash__group_object_permissions__permission',
    )
    serializer_class = TransactionSerializer
    filter_backends = [
        OwnerByMasterUserFilter,
        TransactionObjectPermissionFilter,
        AttributePrefetchFilter,
        DjangoFilterBackend,
        # OrderingWithAttributesFilter,
        OrderingFilter,
        SearchFilter,
    ]
    permission_classes = PomsViewSetBase.permission_classes + [
        TransactionObjectPermission,
    ]
    filter_class = TransactionFilterSet
    ordering_fields = ['transaction_code', 'transaction_date', 'accounting_date', 'cash_date']
    search_fields = ['transaction_code']

    ordering_fields = ['user_code', 'name', 'short_name', 'group__user_code', 'group__name', 'group__short_name']
    search_fields = ['user_code', 'name', 'short_name', 'group__user_code', 'group__name', 'group__short_name']
