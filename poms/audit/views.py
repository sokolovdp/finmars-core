from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django_filters import FilterSet
from notifications.models import Notification
from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter, BaseFilterBackend
from rest_framework.permissions import IsAuthenticated
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
        return queryset.filter(recipient=request.user)


class NotificationViewSet(DbTransactionMixin, ReadOnlyModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (MyNotificationFilter, DjangoFilterBackend, OrderingFilter, SearchFilter,)
    # filter_class = AuthLogFilter
    # ordering_fields = ['user_ip']
    # search_fields = ['user_ip', 'user_agent']
