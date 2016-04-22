from rest_framework.filters import BaseFilterBackend


class OwnerByUserFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(user=request.user)


class OwnerByMasterUserFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        # master_user = get_master_user(request)
        master_user = request.user.master_user
        return queryset.filter(master_user=master_user)


class GroupOwnerByMasterUserFilter(OwnerByMasterUserFilter):
    def filter_queryset(self, request, queryset, view):
        # master_user = get_master_user(request)
        master_user = request.user.master_user
        return queryset.filter(master_user=master_user)
