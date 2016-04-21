from __future__ import unicode_literals

import django_filters
from rest_framework.filters import FilterSet, DjangoFilterBackend, OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from poms.audit.mixins import HistoricalMixin
from poms.common.mixins import DbTransactionMixin
from poms.common.views import PomsClassViewSetBase
from poms.transactions.models import TransactionClass, Transaction
from poms.transactions.serializers import TransactionClassSerializer, TransactionSerializer
from poms.users.filters import OwnerByMasterUserFilter


class TransactionClassViewSet(PomsClassViewSetBase):
    queryset = TransactionClass.objects.all()
    serializer_class = TransactionClassSerializer


class TransactionFilter(FilterSet):
    transaction_date = django_filters.DateFilter()

    class Meta:
        model = Transaction
        fields = ['transaction_date']


class TransactionViewSet(DbTransactionMixin, HistoricalMixin, ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [OwnerByMasterUserFilter, DjangoFilterBackend, OrderingFilter, ]
    filter_class = TransactionFilter
    ordering_fields = ['transaction_date']
