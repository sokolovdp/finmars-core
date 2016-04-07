from rest_framework.filters import BaseFilterBackend

from poms.users.utils import get_master_user


class OwnerByUserFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(user=request.user)


class OwnerByMasterUserFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(master_user=get_master_user(request))


class GroupOwnerByMasterUserFilter(OwnerByMasterUserFilter):
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(master_user=get_master_user(request))
