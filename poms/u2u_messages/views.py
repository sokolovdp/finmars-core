from __future__ import unicode_literals

import django_filters
from rest_framework.filters import OrderingFilter, SearchFilter, DjangoFilterBackend, FilterSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from poms.api.mixins import DbTransactionMixin
from poms.u2u_messages.filters import ThreadOwnerByMasterUserFilter, DirectMessageOwnerByMasterUserFilter
from poms.u2u_messages.models import Thread, Message, DirectMessage
from poms.u2u_messages.serializers import ThreadSerializer, MessageSerializer, DirectMessageSerializer
from poms.users.filters import OwnerByMasterUserFilter


class ThreadViewSet(DbTransactionMixin, ModelViewSet):
    queryset = Thread.objects.all()
    serializer_class = ThreadSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [OwnerByMasterUserFilter, OrderingFilter, SearchFilter, ]
    ordering_fields = ['id', 'name']
    search_fields = ['name']


class MemberFilter(FilterSet):
    channel = django_filters.NumberFilter()

    class Meta:
        model = Message
        fields = ['channel']


class MessageFilter(FilterSet):
    channel = django_filters.NumberFilter()

    class Meta:
        model = Message
        fields = ['channel']


class MessageViewSet(DbTransactionMixin, ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [ThreadOwnerByMasterUserFilter, DjangoFilterBackend, OrderingFilter, SearchFilter, ]
    filter_class = MessageFilter
    ordering_fields = ['id', 'create_date']


class DirectMessageViewSet(DbTransactionMixin, ModelViewSet):
    queryset = DirectMessage.objects.all()
    serializer_class = DirectMessageSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DirectMessageOwnerByMasterUserFilter, DjangoFilterBackend, OrderingFilter, SearchFilter, ]
    ordering_fields = ['id', 'create_date']
