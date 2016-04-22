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
        # member = get_member(request)
        member = request.user.member
        model_cls = queryset.model
        return obj_perms_filter_objects(member, self.get_codename_set(model_cls), queryset)
