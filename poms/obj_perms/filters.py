import django_filters
from django import forms
from rest_framework.filters import BaseFilterBackend

from poms.obj_perms.utils import obj_perms_filter_objects


class AllFakeFilter(django_filters.Filter):
    field_class = forms.ChoiceField

    def __init__(self, *args, **kwargs):
        kwargs['choices'] = (
            (0, '0: Granted only'),
            (1, '1: Show all'),
        )
        super(AllFakeFilter, self).__init__(*args, **kwargs)

    def filter(self, qs, value):
        return qs


# class ObjectPermissionFilter(BaseFilterBackend):
#     codename_set = ['view_%(model_name)s', 'change_%(model_name)s', 'manage_%(model_name)s']
#
#     def get_codename_set(self, model_cls):
#         kwargs = {
#             'app_label': model_cls._meta.app_label,
#             'model_name': model_cls._meta.model_name
#         }
#         return {perm % kwargs for perm in self.codename_set}
#
#     def filter_queryset(self, request, queryset, view):
#         # member = request.user.member
#         # if member.is_superuser:
#         #     return queryset
#         # model_cls = queryset.model
#         # return obj_perms_filter_objects(member, self.get_codename_set(model_cls), queryset)
#         # return self.simple_filter_queryset(request.user.member, queryset)
#         if request.query_params.get('all', '') in ['1', 'yes', 'true']:
#             return queryset
#         return self.simple_filter_queryset(request.user.member, queryset)
#
#     def simple_filter_queryset(self, member, queryset):
#         if member.is_superuser:
#             return queryset
#         model_cls = queryset.model
#         return obj_perms_filter_objects(member, self.get_codename_set(model_cls), queryset)
#
#
# class ObjectPermissionPrefetchFilter(BaseFilterBackend):
#     def filter_queryset(self, request, queryset, view):
#         return queryset.prefetch_related(
#             'user_object_permissions',
#             'user_object_permissions__member',
#             'user_object_permissions__member__groups',
#             'user_object_permissions__permission',
#             # 'user_object_permissions__permission__content_type',
#             'group_object_permissions',
#             # 'group_object_permissions__group',
#             'group_object_permissions__permission',
#             # 'group_object_permissions__permission__content_type',
#         )


class BaseObjectPermissionBackend(BaseFilterBackend):
    codename_set = ['view_%(model_name)s', 'change_%(model_name)s', 'manage_%(model_name)s']
    can_view_all = True

    def get_codename_set(self, model_cls):
        kwargs = {
            'app_label': model_cls._meta.app_label,
            'model_name': model_cls._meta.model_name
        }
        return {perm % kwargs for perm in self.codename_set}

    def filter_queryset(self, request, queryset, view):
        queryset = queryset.prefetch_related(
            'user_object_permissions',
            'user_object_permissions__member',
            'user_object_permissions__member__groups',
            'user_object_permissions__permission',
            # 'user_object_permissions__permission__content_type',
            'group_object_permissions',
            # 'group_object_permissions__group',
            'group_object_permissions__permission',
            # 'group_object_permissions__permission__content_type',
        )
        if self.can_view_all:
            if request.query_params.get('all', '') in ['1', 'yes', 'true']:
                return queryset
        return obj_perms_filter_objects(request.user.member, self.get_codename_set(queryset.model), queryset)


class ObjectPermissionBackend(BaseObjectPermissionBackend):
    can_view_all = True


class FieldObjectPermissionBackend(BaseObjectPermissionBackend):
    can_view_all = False
