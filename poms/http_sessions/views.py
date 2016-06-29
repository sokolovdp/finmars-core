from __future__ import unicode_literals

from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter, FilterSet
from rest_framework.mixins import DestroyModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from poms.common.filters import CharFilter
from poms.common.mixins import DbTransactionMixin
from poms.http_sessions.models import Session
from poms.http_sessions.serializers import SessionSerializer
from poms.users.filters import OwnerByUserFilter


class SessionFilterSet(FilterSet):
    user_agent = CharFilter()

    class Meta:
        model = Session
        fields = ['user_ip', 'user_agent']


class SessionViewSet(DbTransactionMixin, DestroyModelMixin, ReadOnlyModelViewSet):
    queryset = Session.objects
    lookup_field = 'id'
    serializer_class = SessionSerializer
    permission_classes = (
        IsAuthenticated,
    )
    filter_backends = (
        OwnerByUserFilter,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    )
    filter_class = SessionFilterSet
    ordering_fields = ['user_ip']
    search_fields = ['user_ip', 'user_agent']
