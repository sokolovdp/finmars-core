from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter

from poms.obj_perms.views import AbstractWithObjectPermissionViewSet
from poms.users.filters import OwnerByMasterUserFilter


class AbstractAttributeTypeViewSet(AbstractWithObjectPermissionViewSet):
    filter_backends = [
        OwnerByMasterUserFilter,
        # ObjectPermissionBackend,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    # permission_classes = PomsViewSetBase.permission_classes + \
    #                      [ObjectPermissionBase]

    ordering_fields = ['user_code', 'name', 'short_name', 'order', ]
    search_fields = ['user_code', 'name', 'short_name']

    def get_queryset(self):
        qs = super(AbstractAttributeTypeViewSet, self).get_queryset()
        return qs.prefetch_related('options')

    def get_serializer(self, *args, **kwargs):
        # hide_classifiers = (self.action == 'list')
        # read_only_value_type = (self.action != 'create')
        kwargs['hide_classifiers'] = (self.action == 'list')
        kwargs['read_only_value_type'] = (self.action != 'create')
        # kwargs['show_object_permissions'] = (self.action != 'list')
        return super(AbstractAttributeTypeViewSet, self).get_serializer(*args, **kwargs)
