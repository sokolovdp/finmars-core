from __future__ import unicode_literals

from django.http import Http404
from mptt.utils import get_cached_trees
from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter
from rest_framework.mixins import UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from poms.audit.mixins import HistoricalMixin
from poms.common.filters import ClassifierPrefetchFilter
from poms.common.mixins import DbTransactionMixin
from poms.users.filters import OwnerByMasterUserFilter


class PomsViewSetBase(DbTransactionMixin, HistoricalMixin, ModelViewSet):
    permission_classes = [
        IsAuthenticated
    ]

    def update(self, request, *args, **kwargs):
        super(PomsViewSetBase, self).update(request, *args, **kwargs)
        # total reload object, due many to many don't correctly returned
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class PomsClassViewSetBase(ReadOnlyModelViewSet):
    permission_classes = [
        IsAuthenticated
    ]
    filter_backends = [
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter
    ]
    ordering_fields = [
        'id',
        'system_code',
        'name'
    ]
    search_fields = [
        'system_code',
        'name'
    ]
    pagination_class = None


class ClassifierViewSetBase(PomsViewSetBase):
    # ClassifierFilter
    filter_backends = [OwnerByMasterUserFilter,
                       DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']
    pagination_class = None

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        roots = get_cached_trees(queryset)
        serializer = self.get_serializer(roots, many=True)
        return Response(serializer.data)

    def get_object(self):
        obj = super(ClassifierViewSetBase, self).get_object()
        if not obj.is_root_node():
            raise Http404
        trees = get_cached_trees(self.filter_queryset(obj.get_family()))
        obj = trees[0]
        return obj

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # reload tree from
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class ClassifierNodeViewSetBase(DbTransactionMixin, HistoricalMixin, UpdateModelMixin, ReadOnlyModelViewSet):
    filter_backends = [
        OwnerByMasterUserFilter,
        ClassifierPrefetchFilter,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter
    ]
    ordering_fields = [
        'user_code',
        'name',
        'short_name'
    ]
    search_fields = [
        'user_code',
        'name',
        'short_name'
    ]
