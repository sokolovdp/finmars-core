from __future__ import unicode_literals

from rest_framework.filters import FilterSet, DjangoFilterBackend, OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from poms.accounts.models import Account, AccountType, AccountClassifier, AccountAttributeType
from poms.accounts.serializers import AccountSerializer, AccountTypeSerializer, AccountClassifierSerializer, \
    AccountAttributeTypeSerializer
from poms.api.mixins import DbTransactionMixin
from poms.audit.mixins import HistoricalMixin
from poms.users.filters import OwnerByMasterUserFilter


class AccountTypeViewSet(DbTransactionMixin, HistoricalMixin, ModelViewSet):
    queryset = AccountType.objects.all()
    serializer_class = AccountTypeSerializer
    permission_classes = [IsAuthenticated, ]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ['code', 'name']
    search_fields = ['code', 'name']


class AccountClassifierViewSet(DbTransactionMixin, HistoricalMixin, ModelViewSet):
    queryset = AccountClassifier.objects.all()
    serializer_class = AccountClassifierSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [OwnerByMasterUserFilter, DjangoFilterBackend, OrderingFilter, SearchFilter, ]
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']


class AccountFilter(FilterSet):
    class Meta:
        model = Account
        fields = []


# PomsObjectPermissionMixin,
# PomsObjectPermissions
# PomsObjectPermissionsFilter
class AccountViewSet(DbTransactionMixin, HistoricalMixin, ModelViewSet):
    queryset = Account.objects.prefetch_related('attributes', 'attributes__attribute_type').all()
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [OwnerByMasterUserFilter, DjangoFilterBackend, OrderingFilter, SearchFilter, ]
    filter_class = AccountFilter
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']


class AccountAttributeTypeViewSet(DbTransactionMixin, HistoricalMixin, ModelViewSet):
    queryset = AccountAttributeType.objects.all()
    serializer_class = AccountAttributeTypeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [OwnerByMasterUserFilter, DjangoFilterBackend, OrderingFilter, SearchFilter, ]
    ordering_fields = ['order', 'name']
    search_fields = ['user_code', 'name', 'short_name']
