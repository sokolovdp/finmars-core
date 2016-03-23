from __future__ import unicode_literals, print_function

import six
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from guardian.shortcuts import get_groups_with_perms, get_perms_for_model, remove_perm, assign_perm, get_group_perms
from rest_framework import serializers
from rest_framework.decorators import detail_route, list_route
from rest_framework.filters import DjangoObjectPermissionsFilter, BaseFilterBackend
from rest_framework.permissions import IsAuthenticated, DjangoObjectPermissions, BasePermission
from rest_framework.response import Response

from poms.api.fields import FilteredPrimaryKeyRelatedField
from poms.users.serializers import PermissionField


class PomsObjectPermission(DjangoObjectPermissions):
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': ['%(app_label)s.view_%(model_name)s'],
        'HEAD': ['%(app_label)s.view_%(model_name)s'],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }


class PomsObjectPermissionsFilter(DjangoObjectPermissionsFilter):
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': ['%(app_label)s.view_%(model_name)s'],
        'HEAD': ['%(app_label)s.view_%(model_name)s'],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }

    def filter_queryset(self, request, queryset, view):
        from guardian.shortcuts import get_objects_for_user
        user = request.user
        model_cls = queryset.model
        kwargs = {
            'app_label': model_cls._meta.app_label,
            'model_name': model_cls._meta.model_name
        }
        permission = self.perm_format % kwargs
        return get_objects_for_user(user, permission, queryset, with_superuser=False, accept_global_perms=False)


class ObjectPermission(object):
    def __init__(self, group=None, permissions=None):
        self.group = group
        self.permissions = permissions


class ObjectPermissionSerializer(serializers.Serializer):
    group = FilteredPrimaryKeyRelatedField(queryset=Group.objects.all(), filter_backends=[])
    # permissions = serializers.ListField(child=serializers.CharField())
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


class PomsModelPermissionMixin(object):
    def get_serializer_class(self):
        if self.request.path.endswith('permissions/'):
            return ObjectPermissionSerializer
        return super(PomsModelPermissionMixin, self).get_serializer_class()

    def check_manage_permission(self, request, group):
        # group_profile = getattr(group, 'profile', None)
        # if group_profile is None:
        #     raise PermissionDenied()
        # if group.pk == 6:
        #     raise PermissionDenied()
        pass

    def _globalize_perms(self, ctype, perms, is_model=False):
        if is_model:
            return {'%s.%s' % (ctype.app_label, p.codename) for p in perms}
        else:
            return {'%s.%s' % (ctype.app_label, p) for p in perms}

    def _perms(self, request, pk=None):
        model = self.get_queryset().model
        ctype = ContentType.objects.get_for_model(model)

        if request.method == 'GET':
            data = []

            for group in Group.objects.filter(permissions__content_type=ctype).distinct():
                data.append(ObjectPermission(
                    group=group,
                    # permissions=self._globalize_perms(ctype, group.permissions.filter(content_type=ctype),
                    #                                   is_model=True)
                    permissions=group.permissions.filter(content_type=ctype)
                ))

            serializer = ObjectPermissionSerializer(data, many=True)
            return Response(serializer.data)

        elif request.method in ['POST', 'PUT']:
            serializer = ObjectPermissionSerializer(data=request.data, context={'request': request, 'model': model})
            serializer.is_valid(raise_exception=True)
            op = serializer.save()

            self.check_manage_permission(request, op.group)

            # all_perms = {'%s.%s' % (ctype.app_label, p.codename) for p in get_perms_for_model(model)}
            new_perms = {'%s.%s' % (ctype.app_label, p.codename) for p in op.permissions if
                         p.content_type_id == ctype.pk}
            old_perms = {'%s.%s' % (ctype.app_label, p.codename) for p in
                         op.group.permissions.filter(content_type=ctype)}

            # all_perms = self._globalize_perms(ctype, get_perms_for_model(model), is_model=True)
            # new_perms = self._globalize_perms(ctype, op.permissions)
            # new_perms = {p for p in new_perms if p in all_perms}  # filter
            # old_perms = self._globalize_perms(ctype, op.group.permissions.filter(content_type=ctype), is_model=True)

            for p in new_perms - old_perms:
                assign_perm(p, op.group)
            for p in old_perms - new_perms:
                remove_perm(p, op.group)

            # op.permissions = new_perms

            serializer = ObjectPermissionSerializer(instance=op, context={'request': request, 'model': model})
            return Response(serializer.data)

        return Response([])

    @list_route(methods=['get', 'post'], url_path='permissions',
                permission_classes=[IsAuthenticated, ObjectPermissionGuard])
    def list_perms(self, request, pk=None):
        return self._perms(request, pk)


class PomsObjectPermissionMixin(PomsModelPermissionMixin):
    def _perms(self, request, pk=None):
        model = self.get_queryset().model
        ctype = ContentType.objects.get_for_model(model)
        instance = self.get_object() if pk else None

        if instance:
            if request.method == 'GET':
                data = []

                pm = {p.codename: p for p in get_perms_for_model(model)}

                perms = get_groups_with_perms(instance, True)
                for group, perms in six.iteritems(perms):
                    data.append(ObjectPermission(
                        group=group,
                        # permissions=self._globalize_perms(ctype, perms)
                        permissions=[pm[codename] for codename in perms if codename in pm]
                    ))

                serializer = ObjectPermissionSerializer(data, many=True)
                return Response(serializer.data)

            elif request.method in ['POST', 'PUT']:
                serializer = ObjectPermissionSerializer(data=request.data, context={'request': request})
                serializer.is_valid(raise_exception=True)
                op = serializer.save()

                self.check_manage_permission(request, op.group)

                new_perms = {'%s.%s' % (ctype.app_label, p.codename) for p in op.permissions
                             if p.content_type_id == ctype.pk}
                old_perms = {'%s.%s' % (ctype.app_label, codename) for codename in get_group_perms(op.group, instance)}
                print(new_perms)
                print(old_perms)

                # all_perms = self._globalize_perms(ctype, get_perms_for_model(model), is_model=True)
                # new_perms = self._globalize_perms(ctype, op.permissions)
                # new_perms = {p for p in new_perms if p in all_perms}  # filter
                # old_perms = self._globalize_perms(ctype, get_group_perms(op.group, instance))

                for p in set(new_perms) - set(old_perms):
                    assign_perm(p, op.group, instance)
                for p in set(old_perms) - set(new_perms):
                    remove_perm(p, op.group, instance)

                # op.permissions = new_perms

                serializer = ObjectPermissionSerializer(instance=op, context={'request': request})
                return Response(serializer.data)
        else:
            return super(PomsObjectPermissionMixin, self)._perms(request, pk)

    @detail_route(methods=['get', 'post'], url_path='permissions',
                  permission_classes=[IsAuthenticated, ObjectPermissionGuard])
    def object_perms(self, request, pk=None):
        return self._perms(request, pk)
