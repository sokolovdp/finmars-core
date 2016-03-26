from __future__ import unicode_literals

from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from poms.api.mixins import DbTransactionMixin
from poms.audit.mixins import HistoricalMixin
from poms.portfolios.models import PortfolioClassifier, Portfolio
from poms.portfolios.serializers import PortfolioClassifierSerializer, PortfolioSerializer
from poms.users.filters import OwnerByMasterUserFilter


class PortfolioClassifierViewSet(DbTransactionMixin, HistoricalMixin, ModelViewSet):
    queryset = PortfolioClassifier.objects.all()
    serializer_class = PortfolioClassifierSerializer
    permission_classes = [IsAuthenticated, ]
    filter_backends = [OwnerByMasterUserFilter, DjangoFilterBackend, OrderingFilter, SearchFilter, ]
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']


class PortfolioViewSet(DbTransactionMixin, HistoricalMixin, ModelViewSet):
    queryset = Portfolio.objects.all()
    serializer_class = PortfolioSerializer
    permission_classes = [IsAuthenticated, ]
    filter_backends = [OwnerByMasterUserFilter, DjangoFilterBackend, OrderingFilter, SearchFilter, ]
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']
