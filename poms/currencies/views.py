from __future__ import unicode_literals, print_function

import django_filters
import six
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from guardian.shortcuts import get_groups_with_perms, get_perms_for_model, remove_perm, assign_perm, get_group_perms
from rest_framework import serializers
from rest_framework.decorators import detail_route, list_route
from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter, FilterSet, \
    DjangoObjectPermissionsFilter, BaseFilterBackend
from rest_framework.permissions import IsAuthenticated, DjangoObjectPermissions, BasePermission
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from poms.api.fields import FilteredPrimaryKeyRelatedField
from poms.api.filters import IsOwnerByMasterUserOrSystemFilter
from poms.api.mixins import DbTransactionMixin
from poms.api.permissions import IsOwnerOrReadonly
from poms.currencies.models import Currency, CurrencyHistory
from poms.currencies.serializers import CurrencySerializer, CurrencyHistorySerializer


class CurrencyFilter(FilterSet):
    is_global = django_filters.MethodFilter(action='is_global_filter')

    class Meta:
        model = Currency
        fields = ['is_global']

    def is_global_filter(self, qs, value):
        if value is not None and (value.lower() in ['1', 'true']):
            return qs.filter(master_user__isnull=True)
        elif value is not None and (value.lower() in ['0', 'false']):
            return qs.filter(master_user__isnull=False)
        return qs


class DjangoObjectPermissions2(DjangoObjectPermissions):
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': ['%(app_label)s.view_%(model_name)s'],
        'HEAD': ['%(app_label)s.view_%(model_name)s'],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }


class DjangoObjectPermissionsFilter2(DjangoObjectPermissionsFilter):
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


class ObjectPermissionSerializer(serializers.Serializer):
    # group = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all())
    group = FilteredPrimaryKeyRelatedField(queryset=Group.objects.all(), filter_backends=[])
    permissions = serializers.ListField(child=serializers.CharField())

    # permissions = PermissionField(queryset=Permission.objects.all(), many=True)

    def create(self, validated_data):
        return ObjectPermission(**validated_data)

    def update(self, instance, validated_data):
        return None


class ModelPermissionMixin(object):
    def get_serializer_class(self):
        if self.request.path.endswith('permissions/'):
            return ObjectPermissionSerializer
        return super(ModelPermissionMixin, self).get_serializer_class()

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
                    permissions=self._globalize_perms(ctype, group.permissions.filter(content_type=ctype), is_model=True)
                ))

            serializer = ObjectPermissionSerializer(data, many=True)
            return Response(serializer.data)

        elif request.method in ['POST', 'PUT']:
            serializer = ObjectPermissionSerializer(data=request.data, context={'request': request, 'model': model})
            serializer.is_valid(raise_exception=True)
            op = serializer.save()

            self.check_manage_permission(request, op.group)

            all_perms = self._globalize_perms(ctype, get_perms_for_model(model), is_model=True)
            new_perms = self._globalize_perms(ctype, op.permissions)
            new_perms = {p for p in new_perms if p in all_perms}  # filter
            old_perms = self._globalize_perms(ctype, op.group.permissions.filter(content_type=ctype), is_model=True)

            for p in new_perms - old_perms:
                assign_perm('%s.%s' % (ctype.app_label, p), op.group)
            for p in old_perms - new_perms:
                remove_perm('%s.%s' % (ctype.app_label, p), op.group)

            op.permissions = new_perms

            serializer = ObjectPermissionSerializer(instance=op, context={'request': request, 'model': model})
            return Response(serializer.data)

        return Response([])

    @list_route(methods=['get', 'post'], url_path='permissions',
                permission_classes=[IsAuthenticated, ObjectPermissionGuard])
    def list_perms(self, request, pk=None):
        return self._perms(request, pk)


class ObjectPermissionMixin(ModelPermissionMixin):
    def _perms(self, request, pk=None):
        model = self.get_queryset().model
        ctype = ContentType.objects.get_for_model(model)
        instance = self.get_object() if pk else None

        if instance:
            if request.method == 'GET':
                data = []

                perms = get_groups_with_perms(instance, True)
                for group, perms in six.iteritems(perms):
                    data.append(ObjectPermission(
                        group=group,
                        permissions=self._globalize_perms(ctype, perms)
                    ))

                serializer = ObjectPermissionSerializer(data, many=True)
                return Response(serializer.data)

            elif request.method in ['POST', 'PUT']:
                serializer = ObjectPermissionSerializer(data=request.data, context={'request': request})
                serializer.is_valid(raise_exception=True)
                op = serializer.save()

                self.check_manage_permission(request, op.group)

                all_perms = self._globalize_perms(ctype, get_perms_for_model(model), is_model=True)
                new_perms = self._globalize_perms(ctype, op.permissions)
                new_perms = {p for p in new_perms if p in all_perms}  # filter
                old_perms = self._globalize_perms(ctype, get_group_perms(op.group, instance))

                for p in set(new_perms) - set(old_perms):
                    assign_perm(p, op.group, instance)
                for p in set(old_perms) - set(new_perms):
                    remove_perm(p, op.group, instance)

                op.permissions = new_perms

                serializer = ObjectPermissionSerializer(instance=op, context={'request': request})
                return Response(serializer.data)
        else:
            return super(ObjectPermissionMixin, self)._perms(request, pk)

    @detail_route(methods=['get', 'post'], url_path='permissions',
                  permission_classes=[IsAuthenticated, ObjectPermissionGuard])
    def object_perms(self, request, pk=None):
        return self._perms(request, pk)


class CurrencyViewSet(DbTransactionMixin, ObjectPermissionMixin, ModelViewSet):
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
    permission_classes = [IsAuthenticated, DjangoObjectPermissions2]
    filter_backends = [DjangoObjectPermissionsFilter2, DjangoFilterBackend, OrderingFilter, SearchFilter, ]
    filter_class = CurrencyFilter
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']


class CurrencyHistoryFilter(FilterSet):
    currency = django_filters.Filter(name='currency')
    min_date = django_filters.DateFilter(name='date', lookup_type='gte')
    max_date = django_filters.DateFilter(name='date', lookup_type='lte')

    class Meta:
        model = CurrencyHistory
        fields = ['currency', 'min_date', 'max_date']


class CurrencyHistoryViewSet(DbTransactionMixin, ModelViewSet):
    queryset = CurrencyHistory.objects.all()
    serializer_class = CurrencyHistorySerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadonly]
    filter_backends = [IsOwnerByMasterUserOrSystemFilter, DjangoFilterBackend, OrderingFilter, ]
    filter_class = CurrencyHistoryFilter
    ordering_fields = ['-date']
