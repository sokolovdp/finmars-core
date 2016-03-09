from __future__ import unicode_literals

import django_filters
from rest_framework.filters import FilterSet, DjangoFilterBackend, OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet

from poms.api.filters import IsOwnerByMasterUserFilter
from poms.transactions.models import TransactionClass, Transaction
from poms.transactions.serializers import TransactionClassSerializer, TransactionSerializer


class TransactionClassViewSet(ReadOnlyModelViewSet):
    queryset = TransactionClass.objects.all()
    serializer_class = TransactionClassSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None


class TransactionFilter(FilterSet):
    transaction_date = django_filters.DateFilter()

    class Meta:
        model = Transaction
        fields = ['transaction_date']


class TransactionViewSet(ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = (IsOwnerByMasterUserFilter, DjangoFilterBackend, OrderingFilter)
    filter_class = TransactionFilter
    ordering_fields = ['transaction_date']
