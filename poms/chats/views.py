from __future__ import unicode_literals

import django_filters
from django.db.models import Count, Prefetch
from django.utils import timezone
from rest_framework.decorators import detail_route
from rest_framework.filters import FilterSet
from rest_framework.response import Response

from poms.chats.filters import MessagePermissionFilter, DirectMessagePermissionFilter
from poms.chats.models import Thread, Message, DirectMessage, ThreadGroup
from poms.chats.permissions import MessagePermission, DirectMessagePermission
from poms.chats.serializers import ThreadSerializer, MessageSerializer, DirectMessageSerializer, ThreadGroupSerializer
from poms.common.filters import CharFilter, ModelWithPermissionMultipleChoiceFilter, ModelMultipleChoiceFilter, \
    NoOpFilter
from poms.common.views import AbstractModelViewSet
from poms.obj_perms.filters import ObjectPermissionMemberFilter, ObjectPermissionGroupFilter, \
    ObjectPermissionPermissionFilter
from poms.obj_perms.views import AbstractWithObjectPermissionViewSet
from poms.tags.filters import TagFilterBackend, TagFilter
from poms.users.filters import OwnerByMasterUserFilter
from poms.users.models import Member
from poms.users.permissions import SuperUserOrReadOnly, SuperUserOnly


class ThreadGroupFilterSet(FilterSet):
    id = NoOpFilter()
    is_deleted = django_filters.BooleanFilter()
    name = CharFilter()
    tag = TagFilter(model=ThreadGroup)

    class Meta:
        model = ThreadGroup
        fields = []


class ThreadGroupViewSet(AbstractModelViewSet):
    queryset = ThreadGroup.objects
    serializer_class = ThreadGroupSerializer
    permission_classes = AbstractModelViewSet.permission_classes + [
        SuperUserOrReadOnly
    ]
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        TagFilterBackend,
    ]
    filter_class = ThreadGroupFilterSet
    ordering_fields = ['id', 'name']
    search_fields = ['name']
    # has_feature_is_deleted = True


class ThreadFilterSet(FilterSet):
    id = NoOpFilter()
    is_deleted = django_filters.BooleanFilter()
    subject = CharFilter()
    created = django_filters.DateFromToRangeFilter()
    closed = django_filters.DateFromToRangeFilter()
    is_closed = django_filters.MethodFilter(action='filter_is_closed')
    thread_group = ModelWithPermissionMultipleChoiceFilter(model=ThreadGroup)
    tag = TagFilter(model=Thread)
    member = ObjectPermissionMemberFilter(object_permission_model=Thread)
    member_group = ObjectPermissionGroupFilter(object_permission_model=Thread)
    permission = ObjectPermissionPermissionFilter(object_permission_model=Thread)

    class Meta:
        model = Thread
        fields = []

    def filter_is_closed(self, qs, value):
        if value:
            value = value.lower()
            if value in ['0', 'false', 'no']:
                return qs.filter(closed__isnull=True)
            if value in ['1', 'true', 'yes']:
                return qs.filter(closed__isnull=False)
        return qs


class ThreadViewSet(AbstractWithObjectPermissionViewSet):
    queryset = Thread.objects. \
        annotate(messages_count=Count('messages')). \
        prefetch_related('thread_group',
                         Prefetch("messages", to_attr="messages_last",
                                  queryset=Message.objects.prefetch_related('sender').filter(
                                      pk__in=Message.objects.distinct('thread').
                                          order_by('thread_id', '-created', '-id').
                                          values_list('id', flat=True))
                                  ))
    prefetch_permissions_for = []
    serializer_class = ThreadSerializer
    # bulk_objects_permissions_serializer_class = ThreadBulkObjectPermissionSerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        TagFilterBackend,
    ]
    filter_class = ThreadFilterSet
    ordering_fields = [
        'id', 'created', 'subject', 'thread_group__name',
    ]
    search_fields = ['subject']

    # has_feature_is_deleted = True

    @detail_route(url_path='close',
                  permission_classes=AbstractWithObjectPermissionViewSet.permission_classes + [SuperUserOnly, ])
    def close(self, request, pk=None):
        instance = self.get_object()
        instance.closed = timezone.now()
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @detail_route(url_path='reopen',
                  permission_classes=AbstractWithObjectPermissionViewSet.permission_classes + [SuperUserOnly, ])
    def reopen(self, request, pk=None):
        instance = self.get_object()
        instance.closed = None
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class MessageFilterSet(FilterSet):
    id = NoOpFilter()
    thread = ModelWithPermissionMultipleChoiceFilter(model=Thread, field_name='subject')
    created = django_filters.DateRangeFilter()
    sender = ModelMultipleChoiceFilter(model=Member, field_name='username')

    class Meta:
        model = Message
        fields = []


class MessageViewSet(AbstractModelViewSet):
    queryset = Message.objects.prefetch_related('thread', 'sender')
    serializer_class = MessageSerializer
    permission_classes = AbstractModelViewSet.permission_classes + [
        MessagePermission,
    ]
    filter_backends = AbstractModelViewSet.filter_backends + [
        MessagePermissionFilter,
    ]
    filter_class = MessageFilterSet
    ordering_fields = ['id', 'created']


class DirectMessageFilterSet(FilterSet):
    id = NoOpFilter()
    created = django_filters.DateFromToRangeFilter()
    recipient = ModelMultipleChoiceFilter(model=Member, field_name='username')
    sender = ModelMultipleChoiceFilter(model=Member, field_name='username')

    class Meta:
        model = DirectMessage
        fields = []


class DirectMessageViewSet(AbstractModelViewSet):
    queryset = DirectMessage.objects.prefetch_related('sender', 'recipient')
    serializer_class = DirectMessageSerializer
    permission_classes = AbstractModelViewSet.permission_classes + [
        DirectMessagePermission,
    ]
    filter_backends = AbstractModelViewSet.filter_backends + [
        DirectMessagePermissionFilter,
    ]
    filter_class = DirectMessageFilterSet
    ordering_fields = ['id', 'created']
