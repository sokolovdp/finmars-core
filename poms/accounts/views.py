from __future__ import unicode_literals

from rest_framework.filters import FilterSet, DjangoFilterBackend, OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from poms.accounts.models import Account
from poms.accounts.serializers import AccountSerializer
from poms.api.filters import IsOwnerByMasterUserFilter


class AccountFilter(FilterSet):
    class Meta:
        model = Account
        fields = []


class AccountViewSet(ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated, ]
    filter_backends = [IsOwnerByMasterUserFilter, DjangoFilterBackend, OrderingFilter, SearchFilter, ]
    filter_class = AccountFilter
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']
