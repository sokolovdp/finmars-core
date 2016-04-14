from rest_framework.permissions import BasePermission

from poms.obj_perms.utils import get_granted_permissions
from poms.users.utils import get_member


class ObjectPermissionBase(BasePermission):
    perms_map = {
        'GET': [],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['add_%(model_name)s'],
        'PUT': ['change_%(model_name)s'],
        'PATCH': ['change_%(model_name)s'],
        'DELETE': ['delete_%(model_name)s'],
    }

    def get_required_object_permissions(self, method, model_cls):
        kwargs = {
            'app_label': model_cls._meta.app_label,
            'model_name': model_cls._meta.model_name
        }
        return {perm % kwargs for perm in self.perms_map[method]}

    def has_object_permission(self, request, view, obj):
        req_perms = self.get_required_object_permissions(request.method, obj)
        if not req_perms:
            return True

        member = get_member(request)
        perms = get_granted_permissions(member, obj)
        # user_perms = obj.user_object_permissions.select_related('permission',
        #                                                         'permission__content_type').filter(
        #     member=member
        # )
        # group_perms = obj.group_object_permissions.select_related('permission',
        #                                                           'permission__content_type').filter(
        #     group__in=member.groups.all()
        # )
        # permissions = {p.permission.codename for p in user_perms}
        # permissions.update(p.permission.codename for p in group_perms)

        return req_perms.issubset(perms)
