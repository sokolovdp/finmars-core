from django.contrib.contenttypes.models import ContentType
from rest_framework.exceptions import MethodNotAllowed

from poms.common.views import AbstractModelViewSet
from poms.obj_attrs.filters import OwnerByAttributeTypeFilter
from poms.obj_attrs.models import GenericAttributeType
from poms.obj_attrs.serializers import GenericAttributeTypeSerializer
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

class GenericClassifierViewSet(AbstractModelViewSet):
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByAttributeTypeFilter,
    ]
    serializer_class = GenericAttributeTypeSerializer
    target_model = None
    ordering_fields = [
        'attribute_type', 'attribute_type__user_code', 'attribute_type__name', 'attribute_type__short_name',
        'attribute_type__public_name',
        'name', 'level',
    ]


class GenericAttributeTypeViewSet(AbstractWithObjectPermissionViewSet):
    queryset = GenericAttributeType.objects.select_related(
        'master_user', 'content_type'
    ).prefetch_related(
        'options', 'classifiers',
    )
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]
    serializer_class = GenericAttributeTypeSerializer
    ordering_fields = [
        'user_code', 'name', 'short_name', 'public_name', 'order',
    ]
    target_model = None

    def get_queryset(self):
        return super(GenericAttributeTypeViewSet, self).get_queryset().filter(content_type=self.target_model_content_type)

    def get_serializer(self, *args, **kwargs):
        kwargs['show_classifiers'] = (self.action != 'list') or self.request.query_params.get('show_classifiers', None)
        kwargs['read_only_value_type'] = (self.action != 'create')
        return super(GenericAttributeTypeViewSet, self).get_serializer(*args, **kwargs)

    @property
    def target_model_content_type(self):
        return ContentType.objects.get_for_model(self.target_model)

    def perform_create(self, serializer):
        serializer.save(content_type=self.target_model_content_type)
