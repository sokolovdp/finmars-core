from rest_framework.filters import BaseFilterBackend

from poms.obj_perms.utils import obj_perms_filter_objects


class ObjectPermissionFilter(BaseFilterBackend):
    codename_set = ['view_%(model_name)s', 'change_%(model_name)s', 'manage_%(model_name)s']

    def get_codename_set(self, model_cls):
        kwargs = {
            'app_label': model_cls._meta.app_label,
            'model_name': model_cls._meta.model_name
        }
        return {perm % kwargs for perm in self.codename_set}

    def filter_queryset(self, request, queryset, view):
        member = request.user.member
        if member.is_owner or member.is_admin:
            return queryset
        model_cls = queryset.model
        return obj_perms_filter_objects(member, self.get_codename_set(model_cls), queryset)


class ObjectPermissionPrefetchFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset.prefetch_related(
            'user_object_permissions',
            # 'user_object_permissions__member',
            # 'user_object_permissions__member__groups',
            'user_object_permissions__permission',
            # 'user_object_permissions__permission__content_type',
            'group_object_permissions',
            # 'group_object_permissions__group',
            'group_object_permissions__permission',
            # 'group_object_permissions__permission__content_type',
        )
