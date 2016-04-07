from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from rest_framework.filters import BaseFilterBackend

from poms.chats.models import Thread
from poms.obj_perms.models import ThreadGroupObjectPermission, ThreadUserObjectPermission
from poms.users.utils import get_member


class ThreadObjectPermissionFilter(BaseFilterBackend):
    codename_set = ['view_thread', 'change_thread', 'manage_thread']

    def filter_queryset(self, request, queryset, view):
        member = get_member(request)
        ctype = ContentType.objects.get_for_model(Thread)

        f = Q(id__in=ThreadUserObjectPermission.objects.
              filter(member=member,
                     permission__content_type=ctype,
                     permission__codename__in=self.codename_set).
              values_list('content_object__id', flat=True))
        f |= Q(id__in=ThreadGroupObjectPermission.objects.
               filter(group__in=member.groups.all(),
                      permission__content_type=ctype,
                      permission__codename__in=self.codename_set).
               values_list('content_object__id', flat=True))

        return queryset.prefetch_related(
            'user_object_permissions', 'user_object_permissions__permission',
            'group_object_permissions', 'group_object_permissions__permission',
        ).filter(f)


class MessageObjectPermissionFilter(BaseFilterBackend):
    codename_set = ['view_thread', 'change_thread', 'manage_thread']

    def filter_queryset(self, request, queryset, view):
        member = get_member(request)
        ctype = ContentType.objects.get_for_model(Thread)

        f = Q(thread__id__in=ThreadUserObjectPermission.objects.
              filter(member=member,
                     permission__content_type=ctype,
                     permission__codename__in=self.codename_set).
              values_list('content_object__id', flat=True))
        f |= Q(thread__id__in=ThreadGroupObjectPermission.objects.
               filter(group__in=member.groups.all(),
                      permission__content_type=ctype,
                      permission__codename__in=self.codename_set).
               values_list('content_object__id', flat=True))

        return queryset.filter(f)


class ThreadOwnerByMasterUserFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        from poms.users.utils import get_master_user
        return queryset.filter(thread__master_user=get_master_user(request))


class DirectMessageOwnerByMasterUserFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        user = request.user
        return queryset.filter(Q(recipient=user) | Q(sender=user))
