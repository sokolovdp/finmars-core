from __future__ import unicode_literals

import django_filters
from rest_framework.filters import OrderingFilter, SearchFilter, DjangoFilterBackend, FilterSet
from rest_framework.permissions import IsAuthenticated

from poms.chats.filters import MessageThreadOwnerByMasterUserFilter, DirectMessageFilter, \
    ThreadObjectPermissionFilter, MessageObjectPermissionFilter
from poms.chats.models import Thread, Message, DirectMessage, ThreadStatus
from poms.chats.permissions import ThreadObjectPermission, MessagePermission, DirectMessagePermission
from poms.chats.serializers import ThreadSerializer, MessageSerializer, DirectMessageSerializer, ThreadStatusSerializer
from poms.common.views import PomsViewSetBase
from poms.obj_perms.filters import ObjectPermissionPrefetchFilter
from poms.users.filters import OwnerByMasterUserFilter


class ThreadStatusViewSet(PomsViewSetBase):
    queryset = ThreadStatus.objects.all()
    serializer_class = ThreadStatusSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [OwnerByMasterUserFilter, OrderingFilter, SearchFilter, ]
    ordering_fields = ['id', 'name']
    search_fields = ['name']


class ThreadFilterSet(FilterSet):
    created = django_filters.DateFilter()

    class Meta:
        model = Thread
        fields = ['subject', 'created', 'modified']


class ThreadViewSet(PomsViewSetBase):
    queryset = Thread.objects.all()
    serializer_class = ThreadSerializer
    permission_classes = [IsAuthenticated, ThreadObjectPermission]
    filter_backends = [OwnerByMasterUserFilter, ObjectPermissionPrefetchFilter,
                       ThreadObjectPermissionFilter,
                       DjangoFilterBackend, OrderingFilter, SearchFilter, ]
    filter_class = ThreadFilterSet
    ordering_fields = ['id', 'created', 'subject']
    search_fields = ['subject']


class MessageFilterSet(FilterSet):
    thread = django_filters.NumberFilter()
    created = django_filters.DateFilter()

    class Meta:
        model = Message
        fields = ['thread', 'created']


class MessageViewSet(PomsViewSetBase):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated, MessagePermission]
    filter_backends = [MessageThreadOwnerByMasterUserFilter, MessageObjectPermissionFilter, DjangoFilterBackend,
                       OrderingFilter, SearchFilter, ]
    filter_class = MessageFilterSet
    ordering_fields = ['id', 'created']


class DirectMessageViewSet(PomsViewSetBase):
    queryset = DirectMessage.objects.all()
    serializer_class = DirectMessageSerializer
    permission_classes = [IsAuthenticated, DirectMessagePermission]
    filter_backends = [DirectMessageFilter, DjangoFilterBackend, OrderingFilter, SearchFilter, ]
    ordering_fields = ['id', 'created']
