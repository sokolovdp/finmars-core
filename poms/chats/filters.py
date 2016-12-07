from django.db.models import Q
from rest_framework.filters import BaseFilterBackend

from poms.chats.models import Thread
from poms.obj_perms.filters import ObjectPermissionBackend


class MessagePermissionFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        # member = get_member(request)
        # member = request.user.member
        thread_qs = Thread.objects.filter(master_user=request.user.master_user)
        thread_qs = ObjectPermissionBackend().filter_queryset(request, thread_qs, view)
        # threads = obj_perms_filter_objects(member, self.codename_set, Thread.objects.all())
        return queryset.filter(thread_id__in=thread_qs)


class DirectMessagePermissionFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        member = request.user.member
        return queryset.filter(Q(recipient=member) | Q(sender=member))
