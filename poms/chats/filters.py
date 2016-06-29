from django.db.models import Q
from rest_framework.filters import BaseFilterBackend

from poms.chats.models import Thread
from poms.obj_perms.filters import FieldObjectPermissionBackend


# class ThreadObjectPermissionFilter(BaseFilterBackend):
#     codename_set = ['view_thread', 'change_thread', 'manage_thread']
#
#     def filter_queryset(self, request, queryset, view):
#         # member = get_member(request)
#         member = request.user.member
#         return obj_perms_filter_objects(member, self.codename_set, queryset)


# class MessageThreadOwnerByMasterUserFilter(BaseFilterBackend):
#     def filter_queryset(self, request, queryset, view):
#         # from poms.users.utils import get_master_user
#         # return queryset.filter(thread__master_user=get_master_user(request))
#         master_user = request.user.master_user
#         return queryset.filter(thread__master_user=master_user)


class MessagePermissionFilter(BaseFilterBackend):
    # codename_set = ['view_thread', 'change_thread', 'manage_thread']

    def filter_queryset(self, request, queryset, view):
        # member = get_member(request)
        # member = request.user.member
        thread_qs = Thread.objects.filter(master_user=request.user.master_user)
        thread_qs = FieldObjectPermissionBackend().filter_queryset(request, thread_qs, view)
        # threads = obj_perms_filter_objects(member, self.codename_set, Thread.objects.all())
        return queryset.filter(thread_id__in=thread_qs)


class DirectMessagePermissionFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        # user = request.user
        member = request.user.member
        return queryset.filter(Q(recipient=member) | Q(sender=member))


# class ThreadFilter(ModelWithPermissionMultipleChoiceFilter):
#     model = Thread
#     field_name = 'subject'
