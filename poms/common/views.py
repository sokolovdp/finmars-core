from __future__ import unicode_literals

from django.db.models import ProtectedError
from django.http import Http404
from django.utils.translation import ugettext_lazy as _
from mptt.utils import get_cached_trees
from rest_framework import status
from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from poms.audit.mixins import HistoricalMixin
from poms.common.filters import ClassifierFilter, ClassifierPrefetchFilter
from poms.common.mixins import DbTransactionMixin
from poms.users.filters import OwnerByMasterUserFilter


class PomsViewSetBase(DbTransactionMixin, HistoricalMixin, ModelViewSet):
    permission_classes = [
        IsAuthenticated
    ]

    def update(self, request, *args, **kwargs):
        response = super(PomsViewSetBase, self).update(request, *args, **kwargs)
        # total reload object, due many to many don't correctly returned
        if response.status_code == status.HTTP_200_OK:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        return response

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
        except ProtectedError:
            return Response({
                'non_fields_error': _(
                    'Cannot delete instance because they are referenced through a protected foreign key'),
            }, status=status.HTTP_409_CONFLICT)
        return Response(status=status.HTTP_204_NO_CONTENT)


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
    filter_backends = [
        OwnerByMasterUserFilter,
        ClassifierFilter,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter
    ]
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']

    # pagination_class = None

    # def list(self, request, *args, **kwargs):
    #     queryset = self.filter_queryset(self.get_queryset())
    #     roots = get_cached_trees(queryset)
    #     serializer = self.get_serializer(roots, many=True)
    #     return Response(serializer.data)

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


# class ClassifierNodeViewSetBase(DbTransactionMixin, HistoricalMixin, UpdateModelMixin, ReadOnlyModelViewSet):
class ClassifierNodeViewSetBase(DbTransactionMixin, HistoricalMixin, ModelViewSet):
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
