from rest_framework.filters import BaseFilterBackend


class OwnerByUserFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(user=request.user)


class OwnerByMasterUserFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        from poms.users.fields import get_master_user
        return queryset.filter(master_user=get_master_user(request))

# class GuardByUserFilter(BaseFilterBackend):
#     def filter_queryset(self, request, queryset, view):
#         user = request.user
#         return queryset.filter(user)
#
#
# class GuardByMasterUserFilter(BaseFilterBackend):
#     def filter_queryset(self, request, queryset, view):
#         user = request.user
#         return queryset.filter(master_user__in=user.member_of.all())
