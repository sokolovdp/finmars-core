from rest_framework.exceptions import MethodNotAllowed

from poms.common.views import AbstractModelViewSet
from poms.obj_attrs.filters import OwnerByAttributeTypeFilter
from poms.obj_perms.views import AbstractWithObjectPermissionViewSet
from poms.users.filters import OwnerByMasterUserFilter


class AbstractAttributeTypeViewSet(AbstractWithObjectPermissionViewSet):
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]
    ordering_fields = [
        'user_code', 'name', 'short_name', 'order',
    ]
    search_fields = [
        'user_code', 'name', 'short_name'
    ]

    def get_queryset(self):
        qs = super(AbstractAttributeTypeViewSet, self).get_queryset()
        return qs.prefetch_related('options')

    def get_serializer(self, *args, **kwargs):
        # TODO: remove objects_permissions
        if self.action != 'objects_permissions':
            kwargs['show_classifiers'] = (self.action != 'list') or self.request.query_params.get('show_classifiers', None)
            kwargs['read_only_value_type'] = (self.action != 'create')
        return super(AbstractAttributeTypeViewSet, self).get_serializer(*args, **kwargs)


class AbstractClassifierViewSet(AbstractModelViewSet):
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByAttributeTypeFilter,
    ]

    ordering_fields = ['name', 'level', ]
    search_fields = ['name', ]

    # def get_queryset(self):
    #     qs = super(AbstractClassifierViewSet, self).get_queryset()
    #
    #     # f_attribute_type = qs.model._meta.get_field('attribute_type').rel.to
    #     # at_qs = f_attribute_type.objects.filter(master_user=self.request.user.master_user)
    #     # at_qs = ObjectPermissionBackend().filter_queryset(self.request, at_qs, self)
    #
    #     return qs.filter(attribute_type__in=at_qs).prefetch_related('attribute_type')

    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)
