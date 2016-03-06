from __future__ import unicode_literals

from django_filters import FilterSet
from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from poms.api.filters import IsOwnerFilter
from poms.audit.models import AuthLog
from poms.audit.serializers import AuthLogSerializer


class AuthLogFilter(FilterSet):
    class Meta:
        model = AuthLog
        fields = ['user_ip', 'is_success']


class AuthLogViewSet(ReadOnlyModelViewSet):
    queryset = AuthLog.objects.all()
    serializer_class = AuthLogSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (IsOwnerFilter, DjangoFilterBackend, OrderingFilter, SearchFilter,)
    filter_class = AuthLogFilter
    ordering_fields = ['user_ip']
    search_fields = ['user_ip', 'user_agent']
