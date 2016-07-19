from rest_framework.filters import BaseFilterBackend


class HistoryFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        master_user = request.user.master_user
        return queryset.filter(info__master_user=master_user)
