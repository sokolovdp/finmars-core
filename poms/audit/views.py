from __future__ import unicode_literals

import django_filters
from django_filters import FilterSet
from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from poms.audit.filters import ObjectHistoryContentTypeMultipleChoiceFilter
from poms.audit.models import AuthLogEntry, ObjectHistoryEntry
from poms.audit.serializers import AuthLogEntrySerializer, ObjectHistoryEntrySerializer
from poms.common.filters import ModelWithPermissionMultipleChoiceFilter
from poms.users.filters import OwnerByUserFilter
from poms.users.models import Member
from poms.users.permissions import SuperUserOnly


class AuthLogEntryFilterSet(FilterSet):
    date = django_filters.DateFromToRangeFilter()

    class Meta:
        model = AuthLogEntry
        fields = ('user_ip', 'is_success', 'date',)


class AuthLogViewSet(ReadOnlyModelViewSet):
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


class ObjectHistoryEntryFilterSet(FilterSet):
    created = django_filters.DateFromToRangeFilter()
    member = ModelWithPermissionMultipleChoiceFilter(model=Member, field_name='username')
    # content_type = django_filters.ModelChoiceFilter(queryset=ContentType.objects.order_by('app_label', 'model'))
    content_type = ObjectHistoryContentTypeMultipleChoiceFilter()

    class Meta:
        model = ObjectHistoryEntry
        fields = ('created', 'member', 'content_type', 'object_id')


class ObjectHistoryViewSet(ReadOnlyModelViewSet):
    queryset = ObjectHistoryEntry.objects.prefetch_related('master_user', 'member', 'content_type')
    serializer_class = ObjectHistoryEntrySerializer
    permission_classes = (
        IsAuthenticated,
        SuperUserOnly
    )
    filter_backends = (
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    )
    filter_class = ObjectHistoryEntryFilterSet
    ordering_fields = ('created', 'content_type',)
    search_fields = ('created',)
