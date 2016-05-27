from __future__ import unicode_literals

import django_filters
from rest_framework.filters import FilterSet, DjangoFilterBackend, OrderingFilter, SearchFilter

from poms.common.views import PomsClassViewSetBase, PomsViewSetBase
from poms.obj_attrs.filters import AttributePrefetchFilter
from poms.obj_attrs.views import AttributeTypeViewSetBase
from poms.obj_perms.filters import ObjectPermissionPrefetchFilter, ObjectPermissionFilter
from poms.obj_perms.permissions import ObjectPermissionBase
from poms.tags.filters import TagPrefetchFilter
from poms.transactions.models import TransactionClass, Transaction, TransactionType, TransactionAttributeType
from poms.transactions.serializers import TransactionClassSerializer, TransactionSerializer, TransactionTypeSerializer, \
    TransactionAttributeTypeSerializer
from poms.users.filters import OwnerByMasterUserFilter


class TransactionClassViewSet(PomsClassViewSetBase):
    queryset = TransactionClass.objects.all()
    serializer_class = TransactionClassSerializer


class TransactionTypeViewSet(PomsViewSetBase):
    queryset = TransactionType.objects.all()
    serializer_class = TransactionTypeSerializer
    filter_backends = [OwnerByMasterUserFilter, TagPrefetchFilter,
                       DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']


class TransactionAttributeTypeFilterSet(FilterSet):
    class Meta:
        model = TransactionAttributeType
        fields = ['user_code', 'name', 'short_name']


class TransactionAttributeTypeViewSet(AttributeTypeViewSetBase):
    queryset = TransactionAttributeType.objects.all()
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
    # queryset = Transaction.objects.prefetch_related(
    #     'transaction_class',
    #     'instrument', 'transaction_currency', 'settlement_currency',
    #     'portfolio', 'account_cash', 'account_position', 'account_interim',
    #     'strategy1_position', 'strategy1_cash', 'strategy2_position', 'strategy2_cash',
    #     'strategy3_position', 'strategy3_cash'
    # )

    queryset = Transaction.objects
    # queryset = Transaction.objects.select_related(
    #     'master_user',
    #     'transaction_class',
    #     'instrument', 'transaction_currency', 'settlement_currency',
    #     'portfolio', 'account_cash', 'account_position', 'account_interim',
    #     'strategy1_position', 'strategy1_cash', 'strategy2_position', 'strategy2_cash',
    #     'strategy3_position', 'strategy3_cash'
    # ).prefetch_related(
    #     'instrument__group_object_permissions', 'instrument__group_object_permissions__permission',
    #     'portfolio__group_object_permissions', 'portfolio__group_object_permissions__permission',
    #     'account_cash__group_object_permissions', 'account_cash__group_object_permissions__permission',
    #     'account_position__group_object_permissions', 'account_position__group_object_permissions__permission',
    #     'account_interim__group_object_permissions', 'account_interim__group_object_permissions__permission',
    #     # 'strategy1_position__group_object_permissions', 'strategy1_position__group_object_permissions__permission',
    #     # 'strategy1_cash__group_object_permissions', 'strategy1_cash__group_object_permissions__permission',
    #     # 'strategy2_position__group_object_permissions', 'strategy2_position__group_object_permissions__permission',
    #     # 'strategy2_cash__group_object_permissions', 'strategy2_cash__group_object_permissions__permission',
    #     # 'strategy3_position__group_object_permissions', 'strategy3_position__group_object_permissions__permission',
    #     # 'strategy3_cash__group_object_permissions', 'strategy3_cash__group_object_permissions__permission',
    # )
    serializer_class = TransactionSerializer
    filter_backends = [OwnerByMasterUserFilter, AttributePrefetchFilter,
                       DjangoFilterBackend, OrderingFilter]
    filter_class = TransactionFilterSet
    ordering_fields = ['transaction_date']
