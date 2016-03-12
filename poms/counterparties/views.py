from __future__ import unicode_literals

from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from poms.accounts.serializers import AccountClassifierSerializer
from poms.api.filters import IsOwnerByMasterUserFilter
from poms.api.mixins import DbTransactionMixin
from poms.counterparties.models import CounterpartyClassifier, Counterparty, Responsible
from poms.counterparties.serializers import CounterpartySerializer, ResponsibleSerializer


class CounterpartyClassifierViewSet(DbTransactionMixin, ModelViewSet):
    queryset = CounterpartyClassifier.objects.all()
    serializer_class = AccountClassifierSerializer
    permission_classes = [IsAuthenticated, ]
    filter_backends = [IsOwnerByMasterUserFilter, DjangoFilterBackend, OrderingFilter, SearchFilter, ]
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']


class CounterpartyViewSet(DbTransactionMixin, ModelViewSet):
    queryset = Counterparty.objects.all()
    serializer_class = CounterpartySerializer
    permission_classes = [IsAuthenticated, ]
    filter_backends = [IsOwnerByMasterUserFilter, DjangoFilterBackend, OrderingFilter, SearchFilter, ]
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']


class ResponsibleViewSet(DbTransactionMixin, ModelViewSet):
    queryset = Responsible.objects.all()
    serializer_class = ResponsibleSerializer
    permission_classes = [IsAuthenticated, ]
    filter_backends = [IsOwnerByMasterUserFilter, DjangoFilterBackend, OrderingFilter, SearchFilter, ]
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']
