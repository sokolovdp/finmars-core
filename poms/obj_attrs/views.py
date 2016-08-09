from rest_framework.exceptions import MethodNotAllowed

from poms.common.views import AbstractModelViewSet
from poms.obj_attrs.filters import OwnerByAttributeTypeFilter
from poms.obj_perms.views import AbstractWithObjectPermissionViewSet
from poms.users.filters import OwnerByMasterUserFilter


class AbstractAttributeTypeViewSet(AbstractWithObjectPermissionViewSet):
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]

    ordering_fields = ['user_code', 'name', 'short_name', 'order', ]
    search_fields = ['user_code', 'name', 'short_name']

    def get_queryset(self):
        qs = super(AbstractAttributeTypeViewSet, self).get_queryset()
        return qs.prefetch_related('options')

    def get_serializer(self, *args, **kwargs):
        kwargs['hide_classifiers'] = (self.action == 'list')
        kwargs['read_only_value_type'] = (self.action != 'create')
        return super(AbstractAttributeTypeViewSet, self).get_serializer(*args, **kwargs)

# class AbstractClassifierViewSet(AbstractModelViewSet):
#     filter_backends = AbstractModelViewSet.filter_backends + [
#         OwnerByMasterUserFilter,
#         ClassifierFilter,
#     ]
#     ordering_fields = ['user_code', 'name', 'short_name', ]
#     search_fields = ['user_code', 'name', 'short_name', ]
#
#     # pagination_class = None
#
#     # def list(self, request, *args, **kwargs):
#     #     queryset = self.filter_queryset(self.get_queryset())
#     #     roots = get_cached_trees(queryset)
#     #     serializer = self.get_serializer(roots, many=True)
#     #     return Response(serializer.data)
#
#     def get_object(self):
#         obj = super(AbstractClassifierViewSet, self).get_object()
#         if not obj.is_root_node():
#             raise Http404
#         trees = get_cached_trees(self.filter_queryset(obj.get_family()))
#         obj = trees[0]
#         return obj
#
#     def update(self, request, *args, **kwargs):
#         partial = kwargs.pop('partial', False)
#         instance = self.get_object()
#         serializer = self.get_serializer(instance, data=request.data, partial=partial)
#         serializer.is_valid(raise_exception=True)
#         self.perform_update(serializer)
#
#         # reload tree from
#         instance = self.get_object()
#         serializer = self.get_serializer(instance)
#         return Response(serializer.data)
#
#
# class AbstractClassifierNodeViewSet(AbstractModelViewSet):
#     filter_backends = AbstractModelViewSet.filter_backends + [
#         OwnerByMasterUserFilter,
#         ClassifierPrefetchFilter,
#     ]
#     ordering_fields = ['user_code', 'name', 'short_name', ]
#     search_fields = ['user_code', 'name', 'short_name', ]


class AbstractClassifierViewSet(AbstractModelViewSet):
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByAttributeTypeFilter,
    ]

    ordering_fields = ['name', 'level', ]
    search_fields = ['name', ]

    def get_queryset(self):
        qs = super(AbstractClassifierViewSet, self).get_queryset()

        f_attribute_type = qs.model._meta.get_field('attribute_type').rel.to
        at_qs = f_attribute_type.objects.filter(master_user=self.request.user.master_user)
        # at_qs = ObjectPermissionBackend().filter_queryset(self.request, at_qs, self)

        return qs.filter(attribute_type__in=at_qs).select_related('attribute_type')

    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)
