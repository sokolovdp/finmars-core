from __future__ import unicode_literals

from django_filters import FilterSet
from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from poms.api.mixins import DbTransactionMixin
from poms.audit.models import AuthLogEntry
from poms.audit.serializers import AuthLogEntrySerializer
from poms.users.filters import OwnerByUserFilter


class AuthLogEntryFilter(FilterSet):
    class Meta:
        model = AuthLogEntry
        fields = ['user_ip', 'is_success']


class AuthLogEntryViewSet(DbTransactionMixin, ReadOnlyModelViewSet):
    queryset = AuthLogEntry.objects.all()
    serializer_class = AuthLogEntrySerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (OwnerByUserFilter, DjangoFilterBackend, OrderingFilter, SearchFilter,)
    filter_class = AuthLogEntryFilter
    ordering_fields = ['user_ip']
    search_fields = ['user_ip', 'user_agent']
