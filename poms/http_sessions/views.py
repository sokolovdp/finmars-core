from __future__ import unicode_literals

from rest_framework.filters import FilterSet
from rest_framework.mixins import DestroyModelMixin

from poms.common.filters import CharFilter
from poms.common.views import AbstractReadOnlyModelViewSet
from poms.http_sessions.models import Session
from poms.http_sessions.serializers import SessionSerializer
from poms.users.filters import OwnerByUserFilter


class SessionFilterSet(FilterSet):
    user_agent = CharFilter()

    class Meta:
        model = Session
        fields = ('user_ip', 'user_agent',)


class SessionViewSet(DestroyModelMixin, AbstractReadOnlyModelViewSet):
    queryset = Session.objects
    lookup_field = 'id'
    serializer_class = SessionSerializer
    filter_backends = AbstractReadOnlyModelViewSet.filter_backends + [
        OwnerByUserFilter,
    ]
    filter_class = SessionFilterSet
    ordering_fields = ('user_ip',)
    search_fields = ('user_ip', 'user_agent',)
