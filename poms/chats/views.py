from __future__ import unicode_literals

import django_filters
from rest_framework.filters import OrderingFilter, SearchFilter, DjangoFilterBackend, FilterSet

from poms.chats.filters import MessagePermissionFilter, DirectMessagePermissionFilter
from poms.chats.models import Thread, Message, DirectMessage, ThreadStatus
from poms.chats.permissions import MessagePermission, DirectMessagePermission
from poms.chats.serializers import ThreadSerializer, MessageSerializer, DirectMessageSerializer, ThreadStatusSerializer
from poms.common.filters import CharFilter, ModelWithPermissionMultipleChoiceFilter, ModelMultipleChoiceFilter
from poms.common.views import AbstractModelViewSet
from poms.obj_perms.views import AbstractViewSetWithObjectPermission
from poms.users.filters import OwnerByMasterUserFilter
from poms.users.models import Member
from poms.users.permissions import SuperUserOrReadOnly


class ThreadStatusViewSet(AbstractModelViewSet):
    queryset = ThreadStatus.objects.all()
    serializer_class = ThreadStatusSerializer
    permission_classes = AbstractModelViewSet.permission_classes + [
        # IsAuthenticated,
        SuperUserOrReadOnly
    ]
    filter_backends = [
        OwnerByMasterUserFilter,
        OrderingFilter,
        SearchFilter,
    ]
    ordering_fields = ['id', 'name']
    search_fields = ['name']


class ThreadFilterSet(FilterSet):
    subject = CharFilter()
    created = django_filters.DateFromToRangeFilter()
    status = ModelMultipleChoiceFilter(model=ThreadStatus)
    status__is_closed = django_filters.BooleanFilter()

    class Meta:
        model = Thread
        fields = ['subject', 'created', 'status', 'status__is_closed']


class ThreadViewSet(AbstractViewSetWithObjectPermission):
    queryset = Thread.objects.all()
    serializer_class = ThreadSerializer
    # permission_classes = [
    #     IsAuthenticated,
    #     ObjectPermissionBase
    # ]
    filter_backends = [
        OwnerByMasterUserFilter,
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


class MessageFilterSet(FilterSet):
    thread = ModelWithPermissionMultipleChoiceFilter(model=Thread, field_name='subject')
    created = django_filters.DateFilter()
    sender = ModelMultipleChoiceFilter(model=Member, field_name='username')

    class Meta:
        model = Message
        fields = ['thread', 'created']


class MessageViewSet(AbstractModelViewSet):
    queryset = Message.objects
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
    queryset = DirectMessage.objects.all()
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
