from __future__ import unicode_literals

import django_filters
from rest_framework.filters import FilterSet, DjangoFilterBackend, OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet

from poms.api.mixins import DbTransactionMixin
from poms.transactions.models import TransactionClass, Transaction
from poms.transactions.serializers import TransactionClassSerializer, TransactionSerializer
from poms.users.filters import OwnerByMasterUserFilter


class TransactionClassViewSet(DbTransactionMixin, ReadOnlyModelViewSet):
    queryset = TransactionClass.objects.all()
    serializer_class = TransactionClassSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [OrderingFilter, SearchFilter, ]
    ordering_fields = ['id', 'code', 'name']
    search_fields = ['code', 'name']
    pagination_class = None


class TransactionFilter(FilterSet):
    transaction_date = django_filters.DateFilter()

    class Meta:
        model = Transaction
        fields = ['transaction_date']


class TransactionViewSet(DbTransactionMixin, ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [OwnerByMasterUserFilter, DjangoFilterBackend, OrderingFilter, ]
    filter_class = TransactionFilter
    ordering_fields = ['transaction_date']
