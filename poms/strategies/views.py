from __future__ import unicode_literals

from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from poms.api.filters import IsOwnerByMasterUserFilter
from poms.api.mixins import DbTransactionMixin
from poms.strategies.models import Strategy
from poms.strategies.serializers import StrategySerializer


class StrategyViewSet(DbTransactionMixin, ModelViewSet):
    queryset = Strategy.objects.all()
    serializer_class = StrategySerializer
    permission_classes = [IsAuthenticated, ]
    filter_backends = [IsOwnerByMasterUserFilter, DjangoFilterBackend, OrderingFilter, SearchFilter, ]
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']
