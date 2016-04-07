from django.db.models import Q
from rest_framework.filters import BaseFilterBackend

from poms.chats.models import Thread
from poms.obj_perms.utils import obj_perms_filter_objects
from poms.users.utils import get_member


class ThreadObjectPermissionFilter(BaseFilterBackend):
    codename_set = ['view_thread', 'change_thread', 'manage_thread']

    def filter_queryset(self, request, queryset, view):
        member = get_member(request)
        return obj_perms_filter_objects(member, self.codename_set, queryset)


class MessageObjectPermissionFilter(BaseFilterBackend):
    codename_set = ['view_thread', 'change_thread', 'manage_thread']

    def filter_queryset(self, request, queryset, view):
        member = get_member(request)
        threads = obj_perms_filter_objects(member, self.codename_set, Thread.objects.all())
        return queryset.filter(thread_id__in=threads)


class ThreadOwnerByMasterUserFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        from poms.users.utils import get_master_user
        return queryset.filter(thread__master_user=get_master_user(request))


class DirectMessageOwnerByMasterUserFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        user = request.user
        return queryset.filter(Q(recipient=user) | Q(sender=user))
