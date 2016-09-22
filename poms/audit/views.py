from __future__ import unicode_literals

import django_filters
from rest_framework.filters import FilterSet

from poms.audit.filters import ObjectHistory4ContentTypeMultipleChoiceFilter
from poms.audit.models import AuthLogEntry, ObjectHistory4Entry
from poms.audit.serializers import AuthLogEntrySerializer, ObjectHistory4EntrySerializer
from poms.common.filters import ModelWithPermissionMultipleChoiceFilter
from poms.common.views import AbstractReadOnlyModelViewSet
from poms.users.filters import OwnerByUserFilter, OwnerByMasterUserFilter
from poms.users.models import Member
from poms.users.permissions import SuperUserOnly


class AuthLogEntryFilterSet(FilterSet):
    date = django_filters.DateFromToRangeFilter()

    class Meta:
        model = AuthLogEntry
        fields = ('user_ip', 'is_success', 'date',)


class AuthLogViewSet(AbstractReadOnlyModelViewSet):
    queryset = AuthLogEntry.objects.prefetch_related('user')
    serializer_class = AuthLogEntrySerializer
    filter_backends = AbstractReadOnlyModelViewSet.filter_backends + [
        OwnerByUserFilter,
    ]
    filter_class = AuthLogEntryFilterSet
    ordering_fields = ('date',)
    search_fields = ('user_ip', 'user_agent',)


class ObjectHistory4EntryFilterSet(FilterSet):
    created = django_filters.DateFromToRangeFilter()
    member = ModelWithPermissionMultipleChoiceFilter(model=Member, field_name='username')
    actor_content_type = ObjectHistory4ContentTypeMultipleChoiceFilter()
    content_type = ObjectHistory4ContentTypeMultipleChoiceFilter()
    value_content_type = ObjectHistory4ContentTypeMultipleChoiceFilter()
    old_value_content_type = ObjectHistory4ContentTypeMultipleChoiceFilter()

    class Meta:
        model = ObjectHistory4Entry
        fields = (
            'created', 'member', 'group_id',
            'actor_content_type', 'actor_object_id', 'actor_object_repr',
            'action_flag',
            'content_type', 'object_id', 'object_repr',
            'value', 'value_content_type', 'value_object_id',
            'old_value', 'old_value_content_type', 'old_value_object_id',
        )


class ObjectHistory4ViewSet(AbstractReadOnlyModelViewSet):
    queryset = ObjectHistory4Entry.objects.prefetch_related(
        'master_user', 'member', 'actor_content_type', 'content_type', 'value_content_type', 'old_value_content_type',
        'actor_content_object', 'content_object', 'value_content_object', 'old_value_content_object')
    serializer_class = ObjectHistory4EntrySerializer
    filter_backends = AbstractReadOnlyModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]
    permission_classes = AbstractReadOnlyModelViewSet.permission_classes + [
        SuperUserOnly,
    ]
    filter_class = ObjectHistory4EntryFilterSet
    ordering_fields = ('created',)
    search_fields = ('created',)
