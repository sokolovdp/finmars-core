from __future__ import unicode_literals

from rest_framework.filters import FilterSet, DjangoFilterBackend, OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from poms.accounts.models import Account, AccountType, AccountClassifier
from poms.accounts.serializers import AccountSerializer, AccountTypeSerializer, AccountClassifierSerializer
from poms.api.mixins import DbTransactionMixin
from poms.audit.mixins import HistoricalMixin
from poms.users.filters import OwnerByMasterUserFilter, PomsObjectPermissionsFilter
from poms.users.mixins import PomsObjectPermissionMixin
from poms.users.permissions import PomsObjectPermissions


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


class AccountViewSet(DbTransactionMixin, PomsObjectPermissionMixin, HistoricalMixin, ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated, PomsObjectPermissions]
    filter_backends = [OwnerByMasterUserFilter, PomsObjectPermissionsFilter, DjangoFilterBackend, OrderingFilter,
                       SearchFilter, ]
    filter_class = AccountFilter
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']
