from __future__ import unicode_literals

import django_filters
from django.contrib.messages import get_messages, info, success
from django.utils import timezone
from django_filters.widgets import BooleanWidget
from rest_framework.decorators import list_route, detail_route
from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter, FilterSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ViewSet

from poms.common.mixins import DbTransactionMixin
from poms.notifications.filters import NotificationFilter
from poms.notifications.models import Notification
from poms.notifications.serializers import NotificationSerializer


class NotificationFilterSet(FilterSet):
    all = django_filters.MethodFilter(action='show_all', widget=BooleanWidget())

    class Meta:
        model = Notification
        fields = ['all']

    def show_all(self, qs, value):
        # used only for show attr in filter, see OwnerByRecipientFilter
        return qs


class NotificationViewSet(DbTransactionMixin, ReadOnlyModelViewSet):
    queryset = Notification.objects.prefetch_related(
        'recipient', 'recipient_member',
        'actor', 'actor_content_type',
        'action_object', 'action_object_content_type',
        'target', 'target_content_type'
    )
    serializer_class = NotificationSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (
        NotificationFilter,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    )
    filter_class = NotificationFilterSet
    ordering_fields = ['level', 'create_date']

    # search_fields = ['verb']

    @list_route(methods=['get'], url_path='status')
    def get_status(self, request, pk=None):
        unread_count = request.user.notifications.filter(read_date__isnull=True).count()
        return Response({
            "unread_count": unread_count
        })

    @list_route(methods=['post'], url_path='mark-all-as-read')
    def mark_all_as_read(self, request, pk=None):
        request.user.notifications.filter(read_date__isnull=True).update(read_date=timezone.now())
        return Response([])

    @detail_route(methods=['post'], url_path='mark-as-read')
    def mark_as_read(self, request, pk=None):
        instance = self.get_object()
        instance.mark_as_read()
        serializer = self.get_serializer(instance=instance)
        return Response(serializer.data)


class MessageViewSet(ViewSet):
    def list(self, request, *args, **kwargs):
        data = []
        info(request._request, 'info1')
        success(request._request, 'success1')
        for m in get_messages(request):
            data.append([m.level, m.message])
        return Response(data)
