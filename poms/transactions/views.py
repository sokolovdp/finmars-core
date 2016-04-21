from __future__ import unicode_literals

import django_filters
from rest_framework.filters import FilterSet, DjangoFilterBackend, OrderingFilter, SearchFilter

from poms.common.views import PomsClassViewSetBase, PomsViewSetBase
from poms.obj_attrs.views import AttributeTypeViewSetBase
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
    filter_backends = [OwnerByMasterUserFilter, DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']


class TransactionAttributeTypeViewSet(AttributeTypeViewSetBase):
    queryset = TransactionAttributeType.objects.all()
    serializer_class = TransactionAttributeTypeSerializer


class TransactionFilter(FilterSet):
    transaction_date = django_filters.DateFilter()

    class Meta:
        model = Transaction
        fields = ['transaction_date']


class TransactionViewSet(PomsViewSetBase):
    queryset = Transaction.objects.prefetch_related('attributes', 'attributes__attribute_type').all()
    serializer_class = TransactionSerializer
    filter_backends = [OwnerByMasterUserFilter, DjangoFilterBackend, OrderingFilter]
    filter_class = TransactionFilter
    ordering_fields = ['transaction_date']
