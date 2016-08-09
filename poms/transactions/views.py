from __future__ import unicode_literals

import django_filters
from rest_framework.decorators import detail_route
from rest_framework.filters import FilterSet
from rest_framework.response import Response

from poms.accounts.models import Account
from poms.common.filters import CharFilter, ModelWithPermissionMultipleChoiceFilter, ModelMultipleChoiceFilter
from poms.common.views import AbstractClassModelViewSet, AbstractModelViewSet, AbstractReadOnlyModelViewSet
from poms.currencies.models import Currency
from poms.instruments.models import Instrument, InstrumentType
from poms.obj_attrs.filters import AttributePrefetchFilter
from poms.obj_attrs.views import AbstractAttributeTypeViewSet, AbstractClassifierViewSet
from poms.obj_perms.utils import obj_perms_prefetch
from poms.obj_perms.views import AbstractWithObjectPermissionViewSet
from poms.portfolios.models import Portfolio
from poms.strategies.models import Strategy1, Strategy2, Strategy3
from poms.tags.filters import TagFilterBackend, TagFilter
from poms.transactions.filters import TransactionObjectPermissionFilter, ComplexTransactionPermissionFilter
from poms.transactions.models import TransactionClass, Transaction, TransactionType, TransactionAttributeType, \
    TransactionTypeGroup, ComplexTransaction, TransactionClassifier
from poms.transactions.permissions import TransactionObjectPermission
from poms.transactions.processor import TransactionTypeProcessor
from poms.transactions.serializers import TransactionClassSerializer, TransactionSerializer, TransactionTypeSerializer, \
    TransactionAttributeTypeSerializer, TransactionTypeProcessSerializer, TransactionTypeGroupSerializer, \
    ComplexTransactionSerializer, TransactionClassifierNodeSerializer
from poms.users.filters import OwnerByMasterUserFilter


class TransactionClassViewSet(AbstractClassModelViewSet):
    queryset = TransactionClass.objects
    serializer_class = TransactionClassSerializer


class TransactionTypeGroupFilterSet(FilterSet):
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()

    class Meta:
        model = TransactionTypeGroup
        fields = ['user_code', 'name', 'short_name']


class TransactionTypeGroupViewSet(AbstractWithObjectPermissionViewSet):
    queryset = TransactionTypeGroup.objects
    serializer_class = TransactionTypeGroupSerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]
    filter_class = TransactionTypeGroupFilterSet
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']


class TransactionTypeFilterSet(FilterSet):
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    group = ModelWithPermissionMultipleChoiceFilter(model=TransactionTypeGroup)
    portfolio = ModelWithPermissionMultipleChoiceFilter(model=Portfolio, name='portfolios')
    instrument_type = ModelWithPermissionMultipleChoiceFilter(model=InstrumentType, name='instrument_types')
    tag = TagFilter(model=TransactionType)

    class Meta:
        model = TransactionType
        fields = ['user_code', 'name', 'short_name', 'group', 'portfolio', 'instrument_type', 'tag']


class TransactionTypeViewSet(AbstractWithObjectPermissionViewSet):
    queryset = TransactionType.objects
    prefetch_permissions_for = ('group', 'portfolios', 'instrument_types')
    prefetch_action_instruments = (
        'instrument_type', 'instrument_type_input', 'pricing_currency', 'pricing_currency_input', 'accrued_currency',
        'accrued_currency_input', 'daily_pricing_model', 'daily_pricing_model_input', 'payment_size_detail',
        'payment_size_detail_input',
    )
    prefetch_action_trunsactions = (
        'portfolio', 'portfolio_input', 'instrument', 'instrument_input', 'instrument_phantom', 'transaction_currency',
        'transaction_currency_input', 'settlement_currency', 'settlement_currency_input', 'account_position',
        'account_position_input', 'account_cash', 'account_cash_input', 'account_interim', 'account_interim_input',
        'strategy1_position', 'strategy1_position_input', 'strategy2_position', 'strategy2_position_input',
        'strategy3_position', 'strategy3_position_input', 'strategy3_position', 'strategy3_position_input',
        'responsible', 'responsible_input', 'counterparty', 'counterparty_input',
    )
    serializer_class = TransactionTypeSerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        TagFilterBackend,
    ]
    filter_class = TransactionTypeFilterSet
    ordering_fields = ['user_code', 'name', 'short_name', 'group__user_code', 'group__name', 'group__short_name']
    search_fields = ['user_code', 'name', 'short_name', 'group__user_code', 'group__name', 'group__short_name']

    def get_queryset(self):
        queryset = super(TransactionTypeViewSet, self).get_queryset()
        related = [
            'inputs', 'inputs__content_type', 'group', 'portfolios', 'instrument_types',
            'actions', 'actions__transactiontypeactioninstrument', 'actions__transactiontypeactiontransaction',
        ]
        related += ['actions__transactiontypeactioninstrument__%s' % n for n in self.prefetch_action_instruments]
        related += ['actions__transactiontypeactiontransaction__%s' % n for n in self.prefetch_action_trunsactions]
        queryset = queryset.prefetch_related(*related)
        return queryset

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
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()

    class Meta:
        model = TransactionAttributeType
        fields = ['user_code', 'name', 'short_name']


class TransactionAttributeTypeViewSet(AbstractAttributeTypeViewSet):
    queryset = TransactionAttributeType.objects
    serializer_class = TransactionAttributeTypeSerializer
    filter_class = TransactionAttributeTypeFilterSet


class TransactionClassifierFilterSet(FilterSet):
    name = CharFilter()
    attribute_type = ModelWithPermissionMultipleChoiceFilter(model=TransactionAttributeType)

    # parent = ModelWithPermissionMultipleChoiceFilter(model=TransactionClassifier, master_user_path='attribute_type__master_user')

    class Meta:
        model = TransactionClassifier
        fields = ['name', 'level', 'attribute_type', ]


class TransactionClassifierViewSet(AbstractClassifierViewSet):
    queryset = TransactionClassifier.objects
    serializer_class = TransactionClassifierNodeSerializer
    filter_class = TransactionClassifierFilterSet


class TransactionFilterSet(FilterSet):
    transaction_code = django_filters.RangeFilter()
    transaction_date = django_filters.DateFromToRangeFilter()
    accounting_date = django_filters.DateFromToRangeFilter()
    cash_date = django_filters.DateFromToRangeFilter()
    portfolio = ModelWithPermissionMultipleChoiceFilter(model=Portfolio)
    instrument = ModelWithPermissionMultipleChoiceFilter(model=Instrument)
    transaction_currency = ModelMultipleChoiceFilter(model=Currency)
    settlement_currency = ModelMultipleChoiceFilter(model=Currency)
    account_cash = ModelWithPermissionMultipleChoiceFilter(model=Account)
    account_position = ModelWithPermissionMultipleChoiceFilter(model=Account)
    account_interim = ModelWithPermissionMultipleChoiceFilter(model=Account)
    strategy1_position = ModelWithPermissionMultipleChoiceFilter(model=Strategy1,
                                                                 master_user_path='subgroup__group__master_user')
    strategy1_cash = ModelWithPermissionMultipleChoiceFilter(model=Strategy1,
                                                             master_user_path='subgroup__group__master_user')
    strategy2_position = ModelWithPermissionMultipleChoiceFilter(model=Strategy2,
                                                                 master_user_path='subgroup__group__master_user')
    strategy2_cash = ModelWithPermissionMultipleChoiceFilter(model=Strategy2,
                                                             master_user_path='subgroup__group__master_user')
    strategy3_position = ModelWithPermissionMultipleChoiceFilter(model=Strategy3,
                                                                 master_user_path='subgroup__group__master_user')
    strategy3_cash = ModelWithPermissionMultipleChoiceFilter(model=Strategy3,
                                                             master_user_path='subgroup__group__master_user')

    complex_transaction = django_filters.Filter(name='complex_transaction')
    complex_transaction__code = django_filters.RangeFilter()
    complex_transaction__transaction_type = django_filters.Filter(name='complex_transaction__transaction_type')

    # portfolio = django_filters.Filter(name='portfolio')
    # instrument = django_filters.Filter(name='instrument')
    # transaction_currency = django_filters.Filter(name='transaction_currency')
    # settlement_currency = django_filters.Filter(name='settlement_currency')
    # account_cash = django_filters.Filter(name='account_cash')
    # account_position = django_filters.Filter(name='account_position')
    # account_interim = django_filters.Filter(name='account_interim')
    # strategy1_position = django_filters.Filter(name='strategy1_position')
    # strategy1_cash = django_filters.Filter(name='strategy1_cash')
    # strategy2_position = django_filters.Filter(name='strategy2_position')
    # strategy2_cash = django_filters.Filter(name='strategy2_cash')
    # strategy3_position = django_filters.Filter(name='strategy3_position')
    # strategy3_cash = django_filters.Filter(name='strategy3_cash')

    class Meta:
        model = Transaction
        fields = ['transaction_code', 'transaction_date', 'accounting_date', 'cash_date',
                  'complex_transaction', 'complex_transaction__code',
                  'complex_transaction__transaction_type',
                  'portfolio', 'instrument', 'transaction_currency', 'settlement_currency',
                  'account_cash', 'account_position', 'account_interim',
                  'strategy1_position', 'strategy1_cash',
                  'strategy2_position', 'strategy2_cash',
                  'strategy3_position', 'strategy3_cash', ]


class TransactionViewSet(AbstractModelViewSet):
    queryset = Transaction.objects.prefetch_related(
        'master_user',
        'complex_transaction', 'complex_transaction__transaction_type',
        'transaction_class',
        'portfolio',
        # 'portfolio__user_object_permissions', 'portfolio__user_object_permissions__permission',
        # 'portfolio__group_object_permissions', 'portfolio__group_object_permissions__permission',
        'instrument',
        # 'instrument__user_object_permissions', 'instrument__user_object_permissions__permission',
        # 'instrument__group_object_permissions', 'instrument__group_object_permissions__permission',
        'account_cash',
        # 'account_cash__user_object_permissions', 'account_cash__user_object_permissions__permission',
        # 'account_cash__group_object_permissions', 'account_cash__group_object_permissions__permission',
        'account_position',
        # 'account_position__user_object_permissions', 'account_position__user_object_permissions__permission',
        # 'account_position__group_object_permissions', 'account_position__group_object_permissions__permission',
        'account_interim',
        # 'account_interim__user_object_permissions', 'account_interim__user_object_permissions__permission',
        # 'account_interim__group_object_permissions', 'account_interim__group_object_permissions__permission',
        'strategy1_position',
        # 'strategy1_position__user_object_permissions', 'strategy1_position__user_object_permissions__permission',
        # 'strategy1_position__group_object_permissions', 'strategy1_position__group_object_permissions__permission',
        'strategy1_cash',
        # 'strategy1_cash__user_object_permissions', 'strategy1_cash__user_object_permissions__permission',
        # 'strategy1_cash__group_object_permissions', 'strategy1_cash__group_object_permissions__permission',
        'strategy2_position',
        # 'strategy2_position__user_object_permissions', 'strategy2_position__user_object_permissions__permission',
        # 'strategy2_position__group_object_permissions', 'strategy2_position__group_object_permissions__permission',
        'strategy2_cash',
        # 'strategy2_cash__user_object_permissions', 'strategy2_cash__user_object_permissions__permission',
        # 'strategy2_cash__group_object_permissions', 'strategy2_cash__group_object_permissions__permission',
        'strategy3_position',
        # 'strategy3_position__user_object_permissions', 'strategy3_position__user_object_permissions__permission',
        # 'strategy3_position__group_object_permissions', 'strategy3_position__group_object_permissions__permission',
        'strategy3_cash',
        # 'strategy3_cash__user_object_permissions', 'strategy3_cash__user_object_permissions__permission',
        # 'strategy3_cash__group_object_permissions', 'strategy3_cash__group_object_permissions__permission',
    )
    prefetch_permissions_for = (
        'portfolio', 'instrument', 'account_cash', 'account_position', 'account_interim', 'strategy1_position',
        'strategy1_cash', 'strategy2_position', 'strategy2_cash', 'strategy3_position', 'strategy3_cash',
    )
    serializer_class = TransactionSerializer
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        TransactionObjectPermissionFilter,
        AttributePrefetchFilter,
    ]
    permission_classes = AbstractModelViewSet.permission_classes + [
        TransactionObjectPermission,
    ]
    filter_class = TransactionFilterSet
    ordering_fields = [
        'transaction_code', 'transaction_date', 'accounting_date', 'cash_date',
        'complex_transaction__code', 'complex_transaction_order',
        'portfolio__user_code', 'portfolio__name', 'portfolio__short_name',
        'instrument__user_code', 'instrument__name', 'instrument__short_name',
        'transaction_currency__user_code', 'transaction_currency__name', 'transaction_currency__short_name',
        'settlement_currency__user_code', 'settlement_currency__name', 'settlement_currency__short_name',
        'account_cash__user_code', 'account_cash__name', 'account_cash__short_name',
        'account_position__user_code', 'account_position__name', 'account_position__short_name',
        'account_interim__user_code', 'account_interim__name', 'account_interim__short_name',
        'strategy1_position__user_code', 'strategy1_position__name', 'strategy1_position__short_name',
        'strategy1_cash__user_code', 'strategy1_cash__name', 'strategy1_cash__short_name',
        'strategy2_position__user_code', 'strategy2_position__name', 'strategy2_position__short_name',
        'strategy2_cash__user_code', 'strategy2_cash__name', 'strategy2_cash__short_name',
        'strategy3_position__user_code', 'strategy3_position__name', 'strategy3_position__short_name',
        'strategy3_cash__user_code', 'strategy3_cash__name', 'strategy3_cash__short_name',
    ]
    search_fields = ['transaction_code', 'complex_transaction__code', 'complex_transaction_order']

    def get_queryset(self):
        queryset = super(TransactionViewSet, self).get_queryset()
        queryset = obj_perms_prefetch(queryset, my=False, lookups_related=self.prefetch_permissions_for)
        return queryset


class ComplexTransactionFilterSet(FilterSet):
    code = django_filters.RangeFilter()

    class Meta:
        model = ComplexTransaction
        fields = ['code', ]


class ComplexTransactionViewSet(AbstractReadOnlyModelViewSet):
    queryset = ComplexTransaction.objects.select_related(
        'transaction_type',
        'transaction_type__master_user'
    ).prefetch_related(
        # 'transaction_type',
        # 'transaction_type__master_user',
        'transactions',
        'transactions__master_user',
    )
    serializer_class = ComplexTransactionSerializer
    filter_backends = AbstractReadOnlyModelViewSet.filter_backends + [
        ComplexTransactionPermissionFilter,
    ]
    filter_class = ComplexTransactionFilterSet
    ordering_fields = ['code', ]
    search_fields = ['code', ]

    # def get_queryset(self):
    #     queryset = super(ComplexTransactionViewSet, self).get_queryset()
    #     # queryset = obj_perms_prefetch(queryset, my=False, lookups_related=self.prefetch_permissions_for)
    #     return queryset
