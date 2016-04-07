from __future__ import unicode_literals

import django_filters
from rest_framework.filters import OrderingFilter, SearchFilter, DjangoFilterBackend, FilterSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from poms.api.mixins import DbTransactionMixin
from poms.audit.mixins import HistoricalMixin
from poms.chats.filters import ThreadOwnerByMasterUserFilter, DirectMessageOwnerByMasterUserFilter, \
    ThreadObjectPermissionFilter, MessageObjectPermissionFilter
from poms.chats.models import Thread, Message, DirectMessage, ThreadStatus
from poms.chats.permissions import ThreadObjectPermission
from poms.chats.serializers import ThreadSerializer, MessageSerializer, DirectMessageSerializer, ThreadStatusSerializer
from poms.users.filters import OwnerByMasterUserFilter


class ThreadStatusViewSet(DbTransactionMixin, HistoricalMixin, ModelViewSet):
    queryset = ThreadStatus.objects.all()
    serializer_class = ThreadStatusSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [OwnerByMasterUserFilter, OrderingFilter, SearchFilter, ]
    ordering_fields = ['id', 'name']
    search_fields = ['name']


class ThreadViewSet(DbTransactionMixin, HistoricalMixin, ModelViewSet):
    queryset = Thread.objects.all()
    serializer_class = ThreadSerializer
    permission_classes = [IsAuthenticated, ThreadObjectPermission]
    filter_backends = [OwnerByMasterUserFilter, ThreadObjectPermissionFilter, OrderingFilter, SearchFilter, ]
    ordering_fields = ['id', 'subject']
    search_fields = ['subject']


class MessageFilter(FilterSet):
    thread = django_filters.NumberFilter()

    class Meta:
        model = Message
        fields = ['thread']


class MessageViewSet(DbTransactionMixin, HistoricalMixin, ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [ThreadOwnerByMasterUserFilter, MessageObjectPermissionFilter, DjangoFilterBackend,
                       OrderingFilter, SearchFilter, ]
    filter_class = MessageFilter
    ordering_fields = ['id', 'create_date']


class DirectMessageViewSet(DbTransactionMixin, HistoricalMixin, ModelViewSet):
    queryset = DirectMessage.objects.all()
    serializer_class = DirectMessageSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DirectMessageOwnerByMasterUserFilter, DjangoFilterBackend, OrderingFilter, SearchFilter, ]
    ordering_fields = ['id', 'create_date']
