from __future__ import unicode_literals

import django_filters
import six
from rest_framework.decorators import detail_route, list_route
from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter, FilterSet, \
    DjangoObjectPermissionsFilter
from rest_framework.permissions import IsAuthenticated, DjangoObjectPermissions
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

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


class CurrencyViewSet(DbTransactionMixin, ModelViewSet):
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
    permission_classes = [IsAuthenticated, DjangoObjectPermissions2]
    filter_backends = [DjangoObjectPermissionsFilter2, DjangoFilterBackend, OrderingFilter, SearchFilter, ]
    filter_class = CurrencyFilter
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']

    @list_route(methods=['get'], url_path='permissions')
    def get_list_permissions(self, request, pk=None):
        perms = request.user.get_all_permissions()
        return Response(perms)

    @list_route(methods=['get'], url_path='groups-with-permissions')
    def list_groups_with_perms(self, request, pk=None):
        from guardian.shortcuts import get_perms_for_model
        from django.contrib.auth.models import Group
        from django.contrib.contenttypes.models import ContentType
        ctype = ContentType.objects.get_for_model(Currency)
        res = []
        res.append(
            {
                'group': None,
                'permissions': [p.codename for p in get_perms_for_model(Currency)]
            }
        )
        for g in Group.objects.filter(permissions__content_type=ctype).distinct():
            res.append({
                'group': g.pk,
                'permissions': [p.codename for p in g.permissions.filter(content_type=ctype)]
            })
        return Response(res)

    @detail_route(methods=['get'], url_path='permissions')
    def get_perms(self, request, pk=None):
        from guardian.shortcuts import get_perms
        instance = self.get_object()
        perms = get_perms(request.user, instance)
        return Response(perms)

    @detail_route(methods=['get'], url_path='groups-with-permissions')
    def get_groups_with_perms(self, request, pk=None):
        from guardian.shortcuts import get_groups_with_perms
        instance = self.get_object()
        perms = get_groups_with_perms(instance, True)
        res = []
        for g, permissions in six.iteritems(perms):
            res.append({
                'group': g.pk,
                'permissions': permissions,
            })
        return Response(res)


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
