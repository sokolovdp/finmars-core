from __future__ import unicode_literals

import django_filters
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django_filters import FilterSet
from notifications.models import Notification
from rest_framework.decorators import list_route
from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter, BaseFilterBackend
from rest_framework.mixins import UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from poms.api.filters import IsOwnerFilter
from poms.api.mixins import DbTransactionMixin
from poms.audit.models import AuthLog
from poms.audit.serializers import AuthLogSerializer, NotificationSerializer


class AuthLogFilter(FilterSet):
    class Meta:
        model = AuthLog
        fields = ['user_ip', 'is_success']


class AuthLogViewSet(DbTransactionMixin, ReadOnlyModelViewSet):
    queryset = AuthLog.objects.all()
    serializer_class = AuthLogSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (IsOwnerFilter, DjangoFilterBackend, OrderingFilter, SearchFilter,)
    filter_class = AuthLogFilter
    ordering_fields = ['user_ip']
    search_fields = ['user_ip', 'user_agent']


class MyNotificationFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        # user_model = get_user_model()
        # ct = ContentType.objects.get_for_model(user_model)
        queryset = queryset.filter(recipient=request.user)
        if request.GET.get('all') in ['1', 'true']:
            return queryset
        else:
            return queryset.unread()


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
