from __future__ import unicode_literals

import django_filters
from django.utils import timezone
from django_filters.widgets import BooleanWidget
from rest_framework.decorators import list_route, detail_route
from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter, FilterSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from poms.api.mixins import DbTransactionMixin
from poms.notifications.filters import OwnerByRecipientFilter
from poms.notifications.models import Notification
from poms.notifications.serializers import NotificationSerializer


class NotificationFilter(FilterSet):
    all = django_filters.MethodFilter(action='show_all', widget=BooleanWidget())
    level = django_filters.MultipleChoiceFilter(choices=Notification.LEVELS)
    type = django_filters.CharFilter(lookup_expr='startswith')

    class Meta:
        model = Notification
        fields = ['all', 'level']

    def show_all(self, qs, value):
        # used only for show attr in filter, see OwnerByRecipientFilter
        return qs


class NotificationViewSet(DbTransactionMixin, ReadOnlyModelViewSet):
    queryset = Notification.objects.prefetch_related('actor_content_type', 'actor',
                                                     'target_content_type', 'target',
                                                     'action_object_content_type', 'action_object')
    serializer_class = NotificationSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (OwnerByRecipientFilter, DjangoFilterBackend, OrderingFilter, SearchFilter,)
    filter_class = NotificationFilter
    ordering_fields = ['level', 'create_date']

    # search_fields = ['verb']

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
