from __future__ import unicode_literals

import django_filters
from django_filters import FilterSet
from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from poms.audit.models import AuthLogEntry
from poms.audit.serializers import AuthLogEntrySerializer
from poms.users.filters import OwnerByUserFilter


class AuthLogEntryFilterSet(FilterSet):
    date = django_filters.DateFromToRangeFilter()

    class Meta:
        model = AuthLogEntry
        fields = ('user_ip', 'is_success', 'date',)


class AuthLogEntryViewSet(ReadOnlyModelViewSet):
    queryset = AuthLogEntry.objects.select_related('user')
    serializer_class = AuthLogEntrySerializer
    permission_classes = (
        IsAuthenticated,
    )
    filter_backends = (
        OwnerByUserFilter,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    )
    filter_class = AuthLogEntryFilterSet
    ordering_fields = ('date',)
    search_fields = ('user_ip', 'user_agent',)
