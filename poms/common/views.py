from __future__ import unicode_literals

from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from poms.audit.mixins import HistoricalMixin
from poms.common.filters import ClassifierRootFilter
from poms.common.mixins import DbTransactionMixin
from poms.users.filters import OwnerByMasterUserFilter


class PomsViewSetBase(DbTransactionMixin, HistoricalMixin, ModelViewSet):
    permission_classes = [IsAuthenticated]
    pass


class PomsClassViewSetBase(ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ['id', 'system_code', 'name']
    search_fields = ['system_code', 'name']
    pagination_class = None


class ClassifierViewSetBase(PomsViewSetBase):
    # ClassifierFilter
    filter_backends = [OwnerByMasterUserFilter, ClassifierRootFilter, DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']
    pagination_class = None
