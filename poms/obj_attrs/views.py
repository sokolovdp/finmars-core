from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter

from poms.common.views import PomsViewSetBase
from poms.obj_perms.filters import ObjectPermissionBackend
from poms.obj_perms.permissions import ObjectPermissionBase
from poms.users.filters import OwnerByMasterUserFilter


class AttributeTypeViewSetBase(PomsViewSetBase):
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionBackend,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    permission_classes = PomsViewSetBase.permission_classes + \
                         [ObjectPermissionBase]

    ordering_fields = ['user_code', 'name', 'short_name', 'order', ]
    search_fields = ['user_code', 'name', 'short_name']

    def get_queryset(self):
        qs = super(AttributeTypeViewSetBase, self).get_queryset()
        return qs.prefetch_related('options')

    def get_serializer(self, *args, **kwargs):
        hide_classifiers = (self.action == 'list')
        read_only_value_type = (self.action != 'create')
        return super(AttributeTypeViewSetBase, self).get_serializer(*args, hide_classifiers=hide_classifiers,
                                                                    read_only_value_type=read_only_value_type, **kwargs)
