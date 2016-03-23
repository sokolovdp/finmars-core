from __future__ import unicode_literals

import django_filters
from rest_framework.decorators import list_route
from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter, BaseFilterBackend, FilterSet
from rest_framework.mixins import UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from poms.api.mixins import DbTransactionMixin
from poms.notifications.models import Notification
from poms.notifications.serializers import NotificationSerializer


class MyNotificationFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        # user_model = get_user_model()
        # ct = ContentType.objects.get_for_model(user_model)
        queryset = queryset.filter(recipient=request.user)
        if request.GET.get('all') in ['1', 'true']:
            return queryset
        else:
            return queryset.filter(unread=True)


class NotificationFilter(FilterSet):
    all = django_filters.MethodFilter(action='show_all')
    verb = django_filters.CharFilter(lookup_type='contains')

    class Meta:
        model = Notification
        fields = ['all', 'level', 'verb']

    def show_all(self, qs, value):
        return qs


class NotificationViewSet(DbTransactionMixin, UpdateModelMixin, ReadOnlyModelViewSet):
    queryset = Notification.objects.filter(deleted=False)
    serializer_class = NotificationSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (MyNotificationFilter, DjangoFilterBackend, OrderingFilter, SearchFilter,)
    filter_class = NotificationFilter
    ordering_fields = ['level', 'timestamp']

    # search_fields = ['verb']

    @list_route(methods=['post'], url_path='mark-all-as-read')
    def mark_all_as_read(self, request):
        request.user.notifications.mark_all_as_read()
        return Response({})
