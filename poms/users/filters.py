from rest_framework.filters import BaseFilterBackend

from poms.users.backends import filter_objects_for_user


class OwnerByUserFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(user=request.user)


class OwnerByMasterUserFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        from poms.users.fields import get_master_user
        return queryset.filter(master_user=get_master_user(request))


class PomsObjectPermissionsFilter(BaseFilterBackend):
    # perm_format = '%(app_label)s.view_%(model_name)s'
    perm_format = '%(app_label)s.change_%(model_name)s'

    def filter_queryset(self, request, queryset, view):
        user = request.user
        model_cls = queryset.model
        kwargs = {
            'app_label': model_cls._meta.app_label,
            'model_name': model_cls._meta.model_name
        }
        perm = self.perm_format % kwargs
        return filter_objects_for_user(user, [perm], queryset)
