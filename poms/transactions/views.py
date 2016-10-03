from __future__ import unicode_literals

import django_filters
from django.db import transaction
from django.db.models import Prefetch
from rest_framework.decorators import detail_route
from rest_framework.filters import FilterSet
from rest_framework.response import Response

from poms.accounts.models import Account
from poms.common.filters import CharFilter, ModelExtWithPermissionMultipleChoiceFilter, ModelExtMultipleChoiceFilter, \
    NoOpFilter
from poms.common.views import AbstractClassModelViewSet, AbstractModelViewSet, AbstractReadOnlyModelViewSet
from poms.counterparties.models import Responsible, Counterparty
from poms.currencies.models import Currency
from poms.instruments.models import Instrument, InstrumentType
from poms.obj_attrs.filters import AttributeTypeValueTypeFilter
from poms.obj_attrs.views import AbstractAttributeTypeViewSet, AbstractClassifierViewSet
from poms.obj_perms.filters import ObjectPermissionMemberFilter, ObjectPermissionGroupFilter, \
    ObjectPermissionPermissionFilter
from poms.obj_perms.utils import obj_perms_prefetch
from poms.obj_perms.views import AbstractWithObjectPermissionViewSet
from poms.portfolios.models import Portfolio
from poms.strategies.models import Strategy1, Strategy2, Strategy3
from poms.tags.filters import TagFilterBackend, TagFilter
from poms.transactions.filters import TransactionObjectPermissionFilter, ComplexTransactionPermissionFilter, \
    TransactionObjectPermissionMemberFilter, TransactionObjectPermissionGroupFilter, \
    TransactionObjectPermissionPermissionFilter
from poms.transactions.models import TransactionClass, Transaction, TransactionType, TransactionAttributeType, \
    TransactionTypeGroup, ComplexTransaction, TransactionClassifier, EventClass, NotificationClass, \
    TransactionAttribute, \
    TransactionTypeInput, TransactionTypeAction
from poms.transactions.permissions import TransactionObjectPermission
from poms.transactions.serializers import TransactionClassSerializer, TransactionSerializer, TransactionTypeSerializer, \
    TransactionAttributeTypeSerializer, TransactionTypeProcessSerializer, TransactionTypeGroupSerializer, \
    ComplexTransactionSerializer, TransactionClassifierNodeSerializer, EventClassSerializer, \
    NotificationClassSerializer, TransactionTypeProcess
from poms.users.filters import OwnerByMasterUserFilter


class EventClassViewSet(AbstractClassModelViewSet):
    queryset = EventClass.objects
    serializer_class = EventClassSerializer


class NotificationClassViewSet(AbstractClassModelViewSet):
    queryset = NotificationClass.objects
    serializer_class = NotificationClassSerializer


class TransactionClassViewSet(AbstractClassModelViewSet):
    queryset = TransactionClass.objects
    serializer_class = TransactionClassSerializer


class TransactionTypeGroupFilterSet(FilterSet):
    id = NoOpFilter()
    is_deleted = django_filters.BooleanFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    public_name = CharFilter()
    tag = TagFilter(model=Account)
    member = ObjectPermissionMemberFilter(object_permission_model=TransactionTypeGroup)
    member_group = ObjectPermissionGroupFilter(object_permission_model=TransactionTypeGroup)
    permission = ObjectPermissionPermissionFilter(object_permission_model=TransactionTypeGroup)

    class Meta:
        model = TransactionTypeGroup
        fields = []


class TransactionTypeGroupViewSet(AbstractWithObjectPermissionViewSet):
    queryset = TransactionTypeGroup.objects
    serializer_class = TransactionTypeGroupSerializer
    # bulk_objects_permissions_serializer_class = TransactionTypeGroupBulkObjectPermissionSerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        TagFilterBackend,
    ]
    filter_class = TransactionTypeGroupFilterSet
    ordering_fields = [
        'user_code', 'name', 'short_name', 'public_name',
    ]
    # search_fields = [
    #     'user_code', 'name', 'short_name'
    # ]
    # has_feature_is_deleted = True


class TransactionTypeFilterSet(FilterSet):
    id = NoOpFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    public_name = CharFilter()
    group = ModelExtWithPermissionMultipleChoiceFilter(model=TransactionTypeGroup)
    instrument_type = ModelExtWithPermissionMultipleChoiceFilter(model=InstrumentType, name='instrument_types')
    is_valid_for_all_portfolios = django_filters.BooleanFilter()
    is_valid_for_all_instruments = django_filters.BooleanFilter()
    portfolio = ModelExtWithPermissionMultipleChoiceFilter(model=Portfolio, name='portfolios')
    tag = TagFilter(model=TransactionType)
    member = ObjectPermissionMemberFilter(object_permission_model=TransactionType)
    member_group = ObjectPermissionGroupFilter(object_permission_model=TransactionType)
    permission = ObjectPermissionPermissionFilter(object_permission_model=TransactionType)

    class Meta:
        model = TransactionType
        fields = []


class TransactionTypeViewSet(AbstractWithObjectPermissionViewSet):
    queryset = TransactionType.objects.select_related('group').prefetch_related(
        'portfolios', 'instrument_types',
        Prefetch('inputs', queryset=TransactionTypeInput.objects.select_related(
            'content_type', 'instrument_type', 'instrument', 'currency', 'counterparty', 'responsible', 'strategy1',
            'strategy2', 'strategy3', 'daily_pricing_model', 'payment_size_detail', 'price_download_scheme',
        )),
        Prefetch('actions', queryset=TransactionTypeAction.objects.select_related(
            'transactiontypeactioninstrument',
            'transactiontypeactioninstrument__instrument_type',
            # 'transactiontypeactioninstrument__instrument_type_input',
            'transactiontypeactioninstrument__pricing_currency',
            # 'transactiontypeactioninstrument__pricing_currency_input',
            'transactiontypeactioninstrument__accrued_currency',
            # 'transactiontypeactioninstrument__accrued_currency_input',
            'transactiontypeactioninstrument__daily_pricing_model',
            # 'transactiontypeactioninstrument__daily_pricing_model_input',
            'transactiontypeactioninstrument__payment_size_detail',
            # 'transactiontypeactioninstrument__payment_size_detail_input',

            'transactiontypeactiontransaction',
            'transactiontypeactiontransaction__portfolio',
            # 'transactiontypeactiontransaction__portfolio_input',
            'transactiontypeactiontransaction__instrument',
            # 'transactiontypeactiontransaction__instrument_input',
            # 'transactiontypeactiontransaction__instrument_phantom',
            'transactiontypeactiontransaction__transaction_currency',
            # 'transactiontypeactiontransaction__transaction_currency_input',
            'transactiontypeactiontransaction__settlement_currency',
            # 'transactiontypeactiontransaction__settlement_currency_input',
            'transactiontypeactiontransaction__account_position',
            # 'transactiontypeactiontransaction__account_position_input',
            'transactiontypeactiontransaction__account_cash',
            # 'transactiontypeactiontransaction__account_cash_input',
            'transactiontypeactiontransaction__account_interim',
            # 'transactiontypeactiontransaction__account_interim_input',
            'transactiontypeactiontransaction__strategy1_position',
            # 'transactiontypeactiontransaction__strategy1_position_input',
            'transactiontypeactiontransaction__strategy2_position',
            # 'transactiontypeactiontransaction__strategy2_position_input',
            'transactiontypeactiontransaction__strategy3_position',
            # 'transactiontypeactiontransaction__strategy3_position_input',
            'transactiontypeactiontransaction__strategy3_position',
            # 'transactiontypeactiontransaction__strategy3_position_input',
            'transactiontypeactiontransaction__responsible',
            # 'transactiontypeactiontransaction__responsible_input',
            'transactiontypeactiontransaction__counterparty',
            # 'transactiontypeactiontransaction__counterparty_input',
        )),
    )
    prefetch_permissions_for = (
        ('group', TransactionTypeGroup),
        ('portfolios', Portfolio),
        ('instrument_types', InstrumentType),
    )
    # prefetch_action_instruments = (
    #     'instrument_type', 'instrument_type_input', 'pricing_currency', 'pricing_currency_input', 'accrued_currency',
    #     'accrued_currency_input', 'daily_pricing_model', 'daily_pricing_model_input', 'payment_size_detail',
    #     'payment_size_detail_input',
    # )
    # prefetch_action_trunsactions = (
    #     'portfolio', 'portfolio_input', 'instrument', 'instrument_input', 'instrument_phantom', 'transaction_currency',
    #     'transaction_currency_input', 'settlement_currency', 'settlement_currency_input', 'account_position',
    #     'account_position_input', 'account_cash', 'account_cash_input', 'account_interim', 'account_interim_input',
    #     'strategy1_position', 'strategy1_position_input', 'strategy2_position', 'strategy2_position_input',
    #     'strategy3_position', 'strategy3_position_input', 'strategy3_position', 'strategy3_position_input',
    #     'responsible', 'responsible_input', 'counterparty', 'counterparty_input',
    # )
    serializer_class = TransactionTypeSerializer
    # bulk_objects_permissions_serializer_class = TransactionTypeBulkObjectPermissionSerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        TagFilterBackend,
    ]
    filter_class = TransactionTypeFilterSet
    ordering_fields = [
        'user_code', 'name', 'short_name', 'public_name',
        'group', 'group__user_code', 'group__name', 'group__short_name', 'group__public_name',
    ]

    # search_fields = [
    #     'user_code', 'name', 'short_name',
    # ]

    @detail_route(methods=['get', 'put'], url_path='process', serializer_class=TransactionTypeProcessSerializer)
    def process(self, request, pk=None):
        instance = TransactionTypeProcess(transaction_type=self.get_object())
        if request.method == 'GET':
            serializer = self.get_serializer(instance=instance)
            return Response(serializer.data)
        else:
            serializer = self.get_serializer(instance=instance, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            # processor = TransactionTypeProcessor(self._detail_instance, serializer.validated_data)
            # instruments, transactions = processor.run(save)
            # instruments_s = []
            # transactions_s = []
            # for i in instruments:
            #     s = InstrumentSerializer(instance=i, context=self.get_serializer_context())
            #     instruments_s.append(s.data)
            # for t in transactions:
            #     s = TransactionSerializer(instance=t, context=self.get_serializer_context())
            #     transactions_s.append(s.data)
            # d = serializer.data.copy()
            # d['instruments'] = instruments_s
            # d['transactions'] = transactions_s
            try:
                return Response(serializer.data)
            finally:
                transaction.set_rollback(True)


class TransactionAttributeTypeFilterSet(FilterSet):
    id = NoOpFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    public_name = CharFilter()
    value_type = AttributeTypeValueTypeFilter()
    member = ObjectPermissionMemberFilter(object_permission_model=TransactionAttributeType)
    member_group = ObjectPermissionGroupFilter(object_permission_model=TransactionAttributeType)
    permission = ObjectPermissionPermissionFilter(object_permission_model=TransactionAttributeType)

    class Meta:
        model = TransactionAttributeType
        fields = []


class TransactionAttributeTypeViewSet(AbstractAttributeTypeViewSet):
    queryset = TransactionAttributeType.objects
    serializer_class = TransactionAttributeTypeSerializer
    # bulk_objects_permissions_serializer_class = TransactionAttributeTypeBulkObjectPermissionSerializer
    filter_class = TransactionAttributeTypeFilterSet


class TransactionClassifierFilterSet(FilterSet):
    id = NoOpFilter()
    name = CharFilter()
    level = django_filters.NumberFilter()
    attribute_type = ModelExtWithPermissionMultipleChoiceFilter(model=TransactionAttributeType)

    class Meta:
        model = TransactionClassifier
        fields = []


class TransactionClassifierViewSet(AbstractClassifierViewSet):
    queryset = TransactionClassifier.objects
    serializer_class = TransactionClassifierNodeSerializer
    filter_class = TransactionClassifierFilterSet


class TransactionFilterSet(FilterSet):
    id = NoOpFilter()
    complex_transaction = ModelExtMultipleChoiceFilter(model=ComplexTransaction, field_name='id',
                                                       master_user_path='transaction_type__master_user')
    complex_transaction__code = django_filters.RangeFilter()
    complex_transaction__transaction_type = django_filters.Filter(name='complex_transaction__transaction_type')
    transaction_class = django_filters.ModelMultipleChoiceFilter(queryset=TransactionClass.objects)
    transaction_code = django_filters.RangeFilter()
    portfolio = ModelExtWithPermissionMultipleChoiceFilter(model=Portfolio)
    instrument = ModelExtWithPermissionMultipleChoiceFilter(model=Instrument)
    transaction_currency = ModelExtMultipleChoiceFilter(model=Currency)
    position_size_with_sign = django_filters.RangeFilter()
    settlement_currency = ModelExtMultipleChoiceFilter(model=Currency)
    cash_consideration = django_filters.RangeFilter()
    principal_with_sign = django_filters.RangeFilter()
    carry_with_sign = django_filters.RangeFilter()
    overheads_with_sign = django_filters.RangeFilter()
    transaction_date = django_filters.DateFromToRangeFilter()
    accounting_date = django_filters.DateFromToRangeFilter()
    cash_date = django_filters.DateFromToRangeFilter()
    account_position = ModelExtWithPermissionMultipleChoiceFilter(model=Account)
    account_cash = ModelExtWithPermissionMultipleChoiceFilter(model=Account)
    account_interim = ModelExtWithPermissionMultipleChoiceFilter(model=Account)
    strategy1_position = ModelExtWithPermissionMultipleChoiceFilter(model=Strategy1)
    strategy1_cash = ModelExtWithPermissionMultipleChoiceFilter(model=Strategy1)
    strategy2_position = ModelExtWithPermissionMultipleChoiceFilter(model=Strategy2)
    strategy2_cash = ModelExtWithPermissionMultipleChoiceFilter(model=Strategy2)
    strategy3_position = ModelExtWithPermissionMultipleChoiceFilter(model=Strategy3)
    strategy3_cash = ModelExtWithPermissionMultipleChoiceFilter(model=Strategy3)
    reference_fx_rate = django_filters.RangeFilter()
    is_locked = django_filters.BooleanFilter()
    is_canceled = django_filters.BooleanFilter()
    factor = django_filters.RangeFilter()
    trade_price = django_filters.RangeFilter()
    principal_amount = django_filters.RangeFilter()
    carry_amount = django_filters.RangeFilter()
    overheads = django_filters.RangeFilter()
    responsible = ModelExtWithPermissionMultipleChoiceFilter(model=Responsible)
    counterparty = ModelExtWithPermissionMultipleChoiceFilter(model=Counterparty)

    account_member = TransactionObjectPermissionMemberFilter(object_permission_model=Account)
    account_member_group = TransactionObjectPermissionGroupFilter(object_permission_model=Account)
    account_permission = TransactionObjectPermissionPermissionFilter(object_permission_model=Account)
    portfolio_member = TransactionObjectPermissionMemberFilter(object_permission_model=Portfolio)
    portfolio_member_group = TransactionObjectPermissionGroupFilter(object_permission_model=Portfolio)
    portfolio_permission = TransactionObjectPermissionPermissionFilter(object_permission_model=Portfolio)

    class Meta:
        model = Transaction
        fields = []


class TransactionViewSet(AbstractModelViewSet):
    queryset = Transaction.objects.select_related(
        'master_user', 'complex_transaction', 'complex_transaction__transaction_type', 'transaction_class',
        'portfolio', 'instrument', 'transaction_currency', 'settlement_currency',
        'account_cash', 'account_position', 'account_interim',
        'strategy1_position', 'strategy1_cash', 'strategy2_position', 'strategy2_cash',
        'strategy3_position', 'strategy3_cash', 'responsible', 'counterparty',
    ).prefetch_related(
        Prefetch('attributes', queryset=TransactionAttribute.objects.select_related('attribute_type', 'classifier')),
    )
    prefetch_permissions_for = (
        ('portfolio', Portfolio),
        ('instrument', Instrument),
        ('account_cash', Account),
        ('account_position', Account),
        ('account_interim', Account),
        ('strategy1_position', Strategy1),
        ('strategy1_cash', Strategy1),
        ('strategy2_position', Strategy2),
        ('strategy2_cash', Strategy2),
        ('strategy3_position', Strategy3),
        ('strategy3_cash', Strategy3),
        ('responsible', Responsible),
        ('counterparty', Counterparty),
        ('attributes__attribute_type', TransactionAttributeType),
    )
    serializer_class = TransactionSerializer
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        TransactionObjectPermissionFilter,
    ]
    permission_classes = AbstractModelViewSet.permission_classes + [
        TransactionObjectPermission,
    ]
    filter_class = TransactionFilterSet
    ordering_fields = [
        'complex_transaction', 'complex_transaction__code', 'complex_transaction_order',
        'transaction_code',
        'portfolio', 'portfolio__user_code', 'portfolio__name', 'portfolio__short_name', 'portfolio__public_name',
        'instrument', 'instrument__user_code', 'instrument__name', 'instrument__short_name', 'instrument__public_name',
        'transaction_currency', 'transaction_currency__user_code', 'transaction_currency__name',
        'transaction_currency__short_name', 'transaction_currency__public_name',
        'position_size_with_sign',
        'settlement_currency', 'settlement_currency__user_code', 'settlement_currency__name',
        'settlement_currency__short_name', 'settlement_currency__public_name',
        'cash_consideration', 'principal_with_sign', 'carry_with_sign', 'overheads_with_sign',
        'transaction_date', 'accounting_date', 'cash_date',
        'account_cash', 'account_cash__user_code', 'account_cash__name', 'account_cash__short_name',
        'account_cash__public_name',
        'account_cash', 'account_cash__user_code', 'account_position__name', 'account_position__short_name',
        'account_position__public_name',
        'account_interim', 'account_interim__user_code', 'account_interim__name', 'account_interim__short_name',
        'account_interim__public_name',
        'strategy1_position', 'strategy1_position__user_code', 'strategy1_position__name',
        'strategy1_position__short_name', 'strategy1_position__public_name',
        'strategy1_cash', 'strategy1_cash__user_code', 'strategy1_cash__name', 'strategy1_cash__short_name',
        'strategy1_cash__public_name',
        'strategy2_position', 'strategy2_position__user_code', 'strategy2_position__name',
        'strategy2_position__short_name', 'strategy2_position__public_name',
        'strategy2_cash', 'strategy2_cash__user_code', 'strategy2_cash__name', 'strategy2_cash__short_name',
        'strategy2_cash__public_name',
        'strategy3_position', 'strategy3_position__user_code', 'strategy3_position__name',
        'strategy3_position__short_name', 'strategy3_position__public_name',
        'strategy3_cash', 'strategy3_cash__user_code', 'strategy3_cash__name', 'strategy3_cash__short_name',
        'strategy3_cash__public_name',
        'reference_fx_rate', 'is_locked', 'is_canceled', 'factor', 'trade_price', 'principal_amount', 'carry_amount',
        'overheads',
        'responsible', 'responsible__user_code', 'responsible__name', 'responsible__short_name',
        'responsible__public_name',
        'counterparty', 'counterparty__user_code', 'counterparty__name', 'counterparty__short_name',
        'counterparty__public_name',
    ]

    # search_fields = ['transaction_code', 'complex_transaction__code', 'complex_transaction_order']

    def get_queryset(self):
        queryset = super(TransactionViewSet, self).get_queryset()
        queryset = obj_perms_prefetch(queryset, my=False, lookups_related=self.prefetch_permissions_for)
        return queryset


class ComplexTransactionFilterSet(FilterSet):
    id = NoOpFilter()
    transaction_type = ModelExtWithPermissionMultipleChoiceFilter(model=TransactionType)
    code = django_filters.RangeFilter()

    class Meta:
        model = ComplexTransaction
        fields = []


class ComplexTransactionViewSet(AbstractReadOnlyModelViewSet):
    queryset = ComplexTransaction.objects.select_related(
        'transaction_type',
    ).prefetch_related(
        Prefetch('transactions', queryset=Transaction.objects.select_related(
            'master_user', 'complex_transaction', 'complex_transaction__transaction_type', 'transaction_class',
            'portfolio', 'instrument', 'transaction_currency', 'settlement_currency',
            'account_cash', 'account_position', 'account_interim',
            'strategy1_position', 'strategy1_cash', 'strategy2_position', 'strategy2_cash',
            'strategy3_position', 'strategy3_cash', 'responsible', 'counterparty',
        ).prefetch_related(
            Prefetch('attributes',
                     queryset=TransactionAttribute.objects.select_related('attribute_type', 'classifier')),
        ).order_by('complex_transaction_order', 'transaction_date')),
    )
    prefetch_permissions_for = [
        ('transaction_type', TransactionType),
        ('transactions__portfolio', Portfolio),
        ('transactions__instrument', Instrument),
        ('transactions__account_cash', Account),
        ('transactions__account_position', Account),
        ('transactions__account_interim', Account),
        ('transactions__strategy1_position', Strategy1),
        ('transactions__strategy1_cash', Strategy1),
        ('transactions__strategy2_position', Strategy2),
        ('transactions__strategy2_cash', Strategy2),
        ('transactions__strategy3_position', Strategy3),
        ('transactions__strategy3_cash', Strategy3),
        ('transactions__responsible', Responsible),
        ('transactions__counterparty', Counterparty),
        # TODO: Cannot find 'attribute_type' on RelatedManager object, 'transactions__attributes__attribute_type__user_object_permissions' is an invalid parameter to prefetch_related()
        # ('transactions__attributes__attribute_type', TransactionAttributeType),
    ]
    serializer_class = ComplexTransactionSerializer
    filter_backends = AbstractReadOnlyModelViewSet.filter_backends + [
        ComplexTransactionPermissionFilter,
    ]
    filter_class = ComplexTransactionFilterSet
    ordering_fields = ['code', ]

    # search_fields = ['code', ]

    def get_queryset(self):
        queryset = super(ComplexTransactionViewSet, self).get_queryset()
        queryset = obj_perms_prefetch(queryset, my=False, lookups_related=self.prefetch_permissions_for)
        return queryset
