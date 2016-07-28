from rest_framework.filters import BaseFilterBackend


class BloombergTaskFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        # master_user = get_master_user(request)
        master_user = request.user.master_user
        member = request.user.member
        if member.is_superuser:
            return queryset.filter(master_user=master_user)
        else:
            return queryset.filter(master_user=master_user, member=member)
