from rest_framework.permissions import BasePermission

from poms.obj_perms.utils import get_granted_permissions


class PomsObjectPermission(BasePermission):
    perms_map = {
        'GET': [],
        'OPTIONS': [],
        'HEAD': [],

        # 'POST': ['add_%(model_name)s'],
        # 'PUT': ['change_%(model_name)s'],
        # 'PATCH': ['change_%(model_name)s'],
        # 'DELETE': ['delete_%(model_name)s'],

        'POST': ['add_%(model_name)s'],
        'PUT': ['change_%(model_name)s'],
        'PATCH': ['change_%(model_name)s'],
        'DELETE': ['change_%(model_name)s'],
    }

    def get_required_object_permissions(self, method, model_cls):
        kwargs = {
            'app_label': model_cls._meta.app_label,
            'model_name': model_cls._meta.model_name
        }
        return {perm % kwargs for perm in self.perms_map[method]}

    def has_object_permission(self, request, view, obj):
        # member = request.user.member
        # if member.is_superuser:
        #     return True
        # req_perms = self.get_required_object_permissions(request.method, obj)
        # if not req_perms:
        #     return True
        # perms = get_granted_permissions(member, obj)
        # return req_perms.issubset(perms)
        return self.simple_has_object_permission(request.user.member, request.method, obj)

    def simple_has_object_permission(self, member, http_method, obj):
        if member.is_superuser:
            return True
        req_perms = self.get_required_object_permissions(http_method, obj)
        if not req_perms:
            return True
        perms = get_granted_permissions(member, obj)
        return req_perms.issubset(perms)
