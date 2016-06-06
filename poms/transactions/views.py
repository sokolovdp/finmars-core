from __future__ import unicode_literals

import django_filters
from rest_framework.filters import FilterSet, DjangoFilterBackend, OrderingFilter, SearchFilter

from poms.common.filters import OrderingWithAttributesFilter
from poms.common.views import PomsClassViewSetBase, PomsViewSetBase
from poms.obj_attrs.filters import AttributePrefetchFilter
from poms.obj_attrs.views import AttributeTypeViewSetBase
from poms.obj_perms.filters import ObjectPermissionPrefetchFilter, ObjectPermissionFilter
from poms.obj_perms.permissions import ObjectPermissionBase
from poms.tags.filters import TagPrefetchFilter, ByTagNameFilter
from poms.transactions.filters import TransactionObjectPermissionFilter
from poms.transactions.models import TransactionClass, Transaction, TransactionType, TransactionAttributeType
from poms.transactions.permissions import TransactionObjectPermission
from poms.transactions.serializers import TransactionClassSerializer, TransactionSerializer, TransactionTypeSerializer, \
    TransactionAttributeTypeSerializer
from poms.users.filters import OwnerByMasterUserFilter


class TransactionClassViewSet(PomsClassViewSetBase):
    queryset = TransactionClass.objects
    serializer_class = TransactionClassSerializer


class TransactionTypeFilterSet(FilterSet):
    tags = django_filters.MethodFilter(action='tags_filter')

    class Meta:
        model = TransactionType
        fields = ['user_code', 'name', 'short_name', 'tags']

    @staticmethod
    def tags_filter(queryset, value):
        return queryset


class TransactionTypeViewSet(PomsViewSetBase):
    queryset = TransactionType.objects.prefetch_related(
        'inputs', 'actions',

        'actions__transactiontypeactiontransaction',
        'actions__transactiontypeactiontransaction__instrument',
        'actions__transactiontypeactiontransaction__instrument_input',
        'actions__transactiontypeactiontransaction__transaction_currency',
        # 'actions__transactiontypeactiontransaction__transaction_currency_input',
        'actions__transactiontypeactiontransaction__settlement_currency',
        # 'actions__transactiontypeactiontransaction__settlement_currency_input',
        'actions__transactiontypeactiontransaction__account_position',
        # 'actions__transactiontypeactiontransaction__account_position_input',
        'actions__transactiontypeactiontransaction__account_cash',
        # 'actions__transactiontypeactiontransaction__account_cash_input',
        'actions__transactiontypeactiontransaction__account_interim',
        # 'actions__transactiontypeactiontransaction__account_interim_input',
        'actions__transactiontypeactiontransaction__strategy1_position',
        # 'actions__transactiontypeactiontransaction__strategy1_position_input',
        'actions__transactiontypeactiontransaction__strategy2_position',
        # 'actions__transactiontypeactiontransaction__strategy2_position_input',
        'actions__transactiontypeactiontransaction__strategy3_position',
        # 'actions__transactiontypeactiontransaction__strategy3_position_input',

        'actions__transactiontypeactioninstrument',
        'actions__transactiontypeactioninstrument__instrument_type',
        # 'actions__transactiontypeactioninstrument__instrument_type_input',
        'actions__transactiontypeactioninstrument__pricing_currency',
        # 'actions__transactiontypeactioninstrument__pricing_currency_input',
        'actions__transactiontypeactioninstrument__accrued_currency',
        # 'actions__transactiontypeactioninstrument__accrued_currency_input',
        'actions__transactiontypeactioninstrument__daily_pricing_model',
        # 'actions__transactiontypeactioninstrument__daily_pricing_model_input',
        'actions__transactiontypeactioninstrument__payment_size_detail',
        # 'actions__transactiontypeactioninstrument__payment_size_detail_input',
    )
    serializer_class = TransactionTypeSerializer
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionPrefetchFilter,
        ObjectPermissionFilter,
        TagPrefetchFilter,
        ByTagNameFilter,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter
    ]
    permission_classes = PomsViewSetBase.permission_classes + [
        ObjectPermissionBase,
    ]
    filter_class = TransactionTypeFilterSet
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']


class TransactionAttributeTypeFilterSet(FilterSet):
    class Meta:
        model = TransactionAttributeType
        fields = ['user_code', 'name', 'short_name']


class TransactionAttributeTypeViewSet(AttributeTypeViewSetBase):
    queryset = TransactionAttributeType.objects
    serializer_class = TransactionAttributeTypeSerializer
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionPrefetchFilter,
        ObjectPermissionFilter,
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
    transaction_date = django_filters.DateFilter()

    class Meta:
        model = Transaction
        fields = ['transaction_date']


class TransactionViewSet(PomsViewSetBase):
    # queryset = Transaction.objects
    queryset = Transaction.objects.select_related(
        'master_user',
        'transaction_class',
        'instrument', 'transaction_currency', 'settlement_currency',
        'portfolio', 'account_cash', 'account_position', 'account_interim',
        'strategy1_position', 'strategy1_cash',
        'strategy2_position', 'strategy2_cash',
        'strategy3_position', 'strategy3_cash'
    ).prefetch_related(
        'portfolio__group_object_permissions', 'portfolio__group_object_permissions__permission',
        'account_cash__group_object_permissions', 'account_cash__group_object_permissions__permission',
        'account_position__group_object_permissions', 'account_position__group_object_permissions__permission',
        'account_interim__group_object_permissions', 'account_interim__group_object_permissions__permission',
        'instrument__group_object_permissions', 'instrument__group_object_permissions__permission',
    )
    serializer_class = TransactionSerializer
    filter_backends = [
        OwnerByMasterUserFilter,
        TransactionObjectPermissionFilter,
        AttributePrefetchFilter,
        DjangoFilterBackend,
        OrderingWithAttributesFilter,
        # OrderingFilter
        SearchFilter,
    ]
    permission_classes = PomsViewSetBase.permission_classes + [
        TransactionObjectPermission,
    ]
    filter_class = TransactionFilterSet
    ordering_fields = ['transaction_date']
