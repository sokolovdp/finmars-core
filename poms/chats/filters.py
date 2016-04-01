from django.db.models import Q
from rest_framework.filters import BaseFilterBackend


class ThreadOwnerByMasterUserFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        from poms.users.fields import get_master_user
        return queryset.filter(thread__master_user=get_master_user(request))


class DirectMessageOwnerByMasterUserFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        user = request.user
        return queryset.filter(Q(recipient=user) | Q(sender=user))

