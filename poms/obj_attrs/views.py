from rest_framework.exceptions import MethodNotAllowed

from poms.common.views import AbstractModelViewSet
from poms.obj_attrs.filters import OwnerByAttributeTypeFilter
from poms.obj_attrs.models import GenericAttributeType
from poms.obj_perms.views import AbstractWithObjectPermissionViewSet
from poms.users.filters import OwnerByMasterUserFilter


class AbstractAttributeTypeViewSet(AbstractWithObjectPermissionViewSet):
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]
    ordering_fields = [
        'user_code', 'name', 'short_name', 'public_name', 'order',
    ]

    def get_queryset(self):
        qs = super(AbstractAttributeTypeViewSet, self).get_queryset()
        return qs.prefetch_related('options')

    def get_serializer(self, *args, **kwargs):
        # TODO: remove objects_permissions
        # if self.action != 'objects_permissions':
        kwargs['show_classifiers'] = (self.action != 'list') or self.request.query_params.get('show_classifiers', None)
        kwargs['read_only_value_type'] = (self.action != 'create')
        return super(AbstractAttributeTypeViewSet, self).get_serializer(*args, **kwargs)


class AbstractClassifierViewSet(AbstractModelViewSet):
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByAttributeTypeFilter,
    ]
    ordering_fields = [
        'attribute_type', 'attribute_type__user_code', 'attribute_type__name', 'attribute_type__short_name',
        'attribute_type__public_name',
        'name', 'level',
    ]

    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)


class GenericAttributeTypeViewSet(AbstractWithObjectPermissionViewSet):
    queryset = GenericAttributeType.objects.select_related(
        'master_user', 'content_type'
    ).prefetch_related(
        'options', 'classifiers',
    )
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]
    ordering_fields = [
        'user_code', 'name', 'short_name', 'public_name', 'order',
    ]

    # def get_queryset(self):
    #     model = self.get_serializer_class().Meta.target_model
    #     ctype = ContentType.objects.get_for_model(model)
    #     return super(GenericAttributeTypeViewSet, self).get_queryset().filter(content_type=ctype)

    def get_serializer(self, *args, **kwargs):
        kwargs['show_classifiers'] = (self.action != 'list') or self.request.query_params.get('show_classifiers', None)
        kwargs['read_only_value_type'] = (self.action != 'create')
        return super(GenericAttributeTypeViewSet, self).get_serializer(*args, **kwargs)
