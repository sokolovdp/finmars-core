from __future__ import unicode_literals, print_function

from django.contrib.contenttypes.models import ContentType
from guardian.shortcuts import get_perms_for_model, remove_perm, assign_perm, get_group_perms
from rest_framework import serializers
from rest_framework.decorators import detail_route, list_route
from rest_framework.filters import BaseFilterBackend
from rest_framework.permissions import IsAuthenticated, DjangoObjectPermissions, BasePermission
from rest_framework.response import Response

from poms.api.fields import FilteredPrimaryKeyRelatedField
from poms.users.fields import get_master_user, get_member
from poms.users.models import GroupProfile
from poms.users.serializers import PermissionField


class PomsObjectPermissions(DjangoObjectPermissions):
    pass


# class PomsObjectPermission(DjangoObjectPermissions):
#     perms_map = {
#         'GET': ['%(app_label)s.view_%(model_name)s'],
#         'OPTIONS': ['%(app_label)s.view_%(model_name)s'],
#         'HEAD': ['%(app_label)s.view_%(model_name)s'],
#         'POST': ['%(app_label)s.add_%(model_name)s'],
#         'PUT': ['%(app_label)s.change_%(model_name)s'],
#         'PATCH': ['%(app_label)s.change_%(model_name)s'],
#         'DELETE': ['%(app_label)s.delete_%(model_name)s'],
#     }
#
#
# class PomsObjectPermissionsFilter(DjangoObjectPermissionsFilter):
#     perms_map = {
#         'GET': ['%(app_label)s.view_%(model_name)s'],
#         'OPTIONS': ['%(app_label)s.view_%(model_name)s'],
#         'HEAD': ['%(app_label)s.view_%(model_name)s'],
#         'POST': ['%(app_label)s.add_%(model_name)s'],
#         'PUT': ['%(app_label)s.change_%(model_name)s'],
#         'PATCH': ['%(app_label)s.change_%(model_name)s'],
#         'DELETE': ['%(app_label)s.delete_%(model_name)s'],
#     }
#
#     def filter_queryset(self, request, queryset, view):
#         user = request.user
#         model = queryset.model
#         kwargs = {
#             'app_label': model._meta.app_label,
#             'model_name': model._meta.model_name
#         }
#         permission = self.perm_format % kwargs
#         return get_objects_for_user(user, permission, queryset, with_superuser=False, accept_global_perms=False)


class ObjectPermission(object):
    def __init__(self, user=None, group=None, permissions=None):
        self.user = user
        self.group = group
        self.permissions = permissions


class ObjectPermissionSerializer(serializers.Serializer):
    group = FilteredPrimaryKeyRelatedField(queryset=GroupProfile.objects.all(), filter_backends=[])
    permissions = PermissionField(many=True)

    def create(self, validated_data):
        return ObjectPermission(**validated_data)

    def update(self, instance, validated_data):
        return None


class ObjectPermissionGroupFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(profile__isnull=False)


class ObjectPermissionGuard(BasePermission):
    # def has_permission(self, request, view):
    #     profile = getattr(request.user, 'profile', None)
    #     return getattr(profile, 'is_admin', False)

    # def has_object_permission(self, request, view, obj):
    #     # <Currency: USD>
    #     # print(repr(obj))
    #     if request.method in SAFE_METHODS:
    #         return True
    #     return False
    pass

