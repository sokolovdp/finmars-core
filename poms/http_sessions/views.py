from __future__ import unicode_literals

from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter, FilterSet
from rest_framework.mixins import DestroyModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from poms.api.filters import IsOwnerFilter
from poms.api.mixins import DbTransactionMixin
from poms.http_sessions.models import Session
from poms.http_sessions.serializers import SessionSerializer


class SessionFilter(FilterSet):
    class Meta:
        model = Session
        fields = ['user_ip']


class SessionViewSet(DbTransactionMixin, DestroyModelMixin, ReadOnlyModelViewSet):
    queryset = Session.objects.all()
    lookup_field = 'id'
    serializer_class = SessionSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (IsOwnerFilter, DjangoFilterBackend, OrderingFilter, SearchFilter,)
    filter_class = SessionFilter
    ordering_fields = ['user_ip']
    search_fields = ['user_ip', 'user_agent']
