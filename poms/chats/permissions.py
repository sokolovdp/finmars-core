from django.contrib.contenttypes.models import ContentType
from rest_framework.permissions import BasePermission, DjangoObjectPermissions

from poms.chats.models import Thread
from poms.users.fields import get_member


class ThreadObjectPermission(BasePermission):
    perms_map = {
        'GET': [],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }

    def get_required_object_permissions(self, method, model_cls):
        kwargs = {
            'app_label': model_cls._meta.app_label,
            'model_name': model_cls._meta.model_name
        }
        return [perm % kwargs for perm in self.perms_map[method]]

    def has_object_permission(self, request, view, obj):
        model_cls = Thread
        user = request.user

        member = get_member(request)
        thread = obj
        # perms = self.get_required_object_permissions(request.method, model_cls)

        user_permissions = thread.user_object_permissions.select_related('permission', 'permission__content_type').filter(
            member=member
        )
        group_permissions = thread.group_object_permissions.select_related('permission', 'permission__content_type').filter(
            group__in=member.groups.all()
        )

        permissions = {p.permission.codename for p in user_permissions}
        permissions.update(p.permission.codename for p in group_permissions)
        print('->', permissions)

        # for p in perms:
        #     app_label, codename = p.split('.')



        return True
