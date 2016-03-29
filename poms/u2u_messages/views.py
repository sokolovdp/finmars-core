from __future__ import unicode_literals

import django_filters
from rest_framework.filters import OrderingFilter, SearchFilter, DjangoFilterBackend, FilterSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from poms.api.mixins import DbTransactionMixin
from poms.u2u_messages.filters import ChannelOwnerByMasterUserFilter
from poms.u2u_messages.models import Channel, Message, Member
from poms.u2u_messages.serializers import ChannelSerializer, MessageSerializer, MemberSerializer
from poms.users.filters import OwnerByMasterUserFilter


class ChannelViewSet(DbTransactionMixin, ModelViewSet):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [OwnerByMasterUserFilter, OrderingFilter, SearchFilter, ]
    ordering_fields = ['id', 'name']
    search_fields = ['name']


class MemberFilter(FilterSet):
    channel = django_filters.NumberFilter()

    class Meta:
        model = Message
        fields = ['channel']


class MemberViewSet(DbTransactionMixin, ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [ChannelOwnerByMasterUserFilter, DjangoFilterBackend, ]
    filter_class = MemberFilter


class MessageFilter(FilterSet):
    channel = django_filters.NumberFilter()

    class Meta:
        model = Message
        fields = ['channel']


class MessageViewSet(DbTransactionMixin, ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [ChannelOwnerByMasterUserFilter, DjangoFilterBackend, OrderingFilter, SearchFilter, ]
    filter_class = MessageFilter
    ordering_fields = ['id', 'create_date']
