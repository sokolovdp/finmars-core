from __future__ import unicode_literals

import django_filters
from django.utils import timezone
from rest_framework.decorators import detail_route
from rest_framework.filters import OrderingFilter, SearchFilter, DjangoFilterBackend, FilterSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from poms.chats.filters import MessagePermissionFilter, DirectMessagePermissionFilter
from poms.chats.models import Thread, Message, DirectMessage, ThreadGroup
from poms.chats.permissions import MessagePermission, DirectMessagePermission
from poms.chats.serializers import ThreadSerializer, MessageSerializer, DirectMessageSerializer, ThreadGroupSerializer
from poms.common.filters import CharFilter, ModelWithPermissionMultipleChoiceFilter, ModelMultipleChoiceFilter
from poms.common.views import AbstractModelViewSet
from poms.obj_perms.views import AbstractWithObjectPermissionViewSet
from poms.tags.filters import TagFilterBackend, TagFilter
from poms.users.filters import OwnerByMasterUserFilter
from poms.users.models import Member
from poms.users.permissions import SuperUserOrReadOnly


class ThreadGroupFilterSet(FilterSet):
    name = CharFilter()
    tag = TagFilter(model=ThreadGroup)

    class Meta:
        model = ThreadGroup
        fields = ['name', 'tag']


class ThreadGroupViewSet(AbstractModelViewSet):
    queryset = ThreadGroup.objects
    serializer_class = ThreadGroupSerializer
    permission_classes = [
        IsAuthenticated,
        SuperUserOrReadOnly
    ]
    filter_backends = [
        OwnerByMasterUserFilter,
        TagFilterBackend,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    filter_class = ThreadGroupFilterSet
    ordering_fields = ['id', 'name']
    search_fields = ['name']


class ThreadFilterSet(FilterSet):
    subject = CharFilter()
    created = django_filters.DateFromToRangeFilter()
    closed = django_filters.DateFromToRangeFilter()
    # status = ModelMultipleChoiceFilter(model=ThreadStatus)
    is_closed = django_filters.MethodFilter(action='filter_is_closed')
    tag = TagFilter(model=Thread)
    thread_group = ModelWithPermissionMultipleChoiceFilter(model=ThreadGroup)

    class Meta:
        model = Thread
        fields = ['subject', 'created', 'closed', 'is_closed', 'tag', 'thread_group']

    def filter_is_closed(self, qs, value):
        if value:
            value = value.lower()
            if value in ['0', 'false', 'no']:
                return qs.filter(closed__isnull=True)
            if value in ['1', 'true', 'yes']:
                return qs.filter(closed__isnull=False)
        return qs


class ThreadViewSet(AbstractWithObjectPermissionViewSet):
    queryset = Thread.objects
    serializer_class = ThreadSerializer
    # permission_classes = [
    #     IsAuthenticated,
    #     ObjectPermissionBase
    # ]
    filter_backends = [
        OwnerByMasterUserFilter,
        TagFilterBackend,
        # ObjectPermissionBackend,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    filter_class = ThreadFilterSet
    ordering_fields = ['id', 'created', 'subject']
    search_fields = ['subject']

    # def get_serializer(self, *args, **kwargs):
    #     kwargs['show_object_permissions'] = (self.action != 'list')
    #     return super(ThreadViewSet, self).get_serializer(*args, **kwargs)

    @detail_route(url_path='close')
    def close(self, request, pk=None):
        instance = self.get_object()
        instance.closed = timezone.now()
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @detail_route(url_path='reopen')
    def reopen(self, request, pk=None):
        instance = self.get_object()
        instance.closed = None
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class MessageFilterSet(FilterSet):
    thread = ModelWithPermissionMultipleChoiceFilter(model=Thread, field_name='subject')
    created = django_filters.DateFilter()
    sender = ModelMultipleChoiceFilter(model=Member, field_name='username')

    class Meta:
        model = Message
        fields = ['thread', 'created']


class MessageViewSet(AbstractModelViewSet):
    queryset = Message.objects.select_related('thread', 'sender')
    serializer_class = MessageSerializer
    permission_classes = AbstractModelViewSet.permission_classes + [
        MessagePermission,
    ]
    filter_backends = [
        MessagePermissionFilter,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    filter_class = MessageFilterSet
    ordering_fields = ['id', 'created']


class DirectMessageFilterSet(FilterSet):
    created = django_filters.DateFromToRangeFilter()
    recipient = ModelMultipleChoiceFilter(model=Member, field_name='username')
    sender = ModelMultipleChoiceFilter(model=Member, field_name='username')

    class Meta:
        model = DirectMessage
        fields = ['created', 'recipient', 'sender']


class DirectMessageViewSet(AbstractModelViewSet):
    queryset = DirectMessage.objects.select_related('sender', 'recipient')
    serializer_class = DirectMessageSerializer
    permission_classes = AbstractModelViewSet.permission_classes + [
        DirectMessagePermission,
    ]
    filter_backends = [
        DirectMessagePermissionFilter,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    filter_class = DirectMessageFilterSet
    ordering_fields = ['id', 'created']
