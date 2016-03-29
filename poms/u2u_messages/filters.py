from rest_framework.filters import BaseFilterBackend


class ChannelOwnerByMasterUserFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        from poms.users.fields import get_master_user
        return queryset.filter(channel__master_user=get_master_user(request))
