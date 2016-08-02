from poms.common.views import AbstractModelViewSet
from poms.obj_perms.filters import ObjectPermissionBackend
from poms.obj_perms.permissions import PomsObjectPermission
from poms.obj_perms.utils import obj_perms_prefetch


class AbstractWithObjectPermissionViewSet(AbstractModelViewSet):
    filter_backends = AbstractModelViewSet.filter_backends + [
        ObjectPermissionBackend,
    ]
    permission_classes = AbstractModelViewSet.permission_classes + [
        PomsObjectPermission,
    ]
    prefetch_permissions_for = []

    def filter_queryset(self, queryset):
        queryset = super(AbstractWithObjectPermissionViewSet, self).filter_queryset(queryset)
        # queryset = ObjectPermissionBackend().filter_queryset(self.request, queryset, self)
        if self.prefetch_permissions_for:
            queryset = obj_perms_prefetch(queryset, self.prefetch_permissions_for)
        return queryset

    # def get_permissions(self):
    #     return super(AbstractWithObjectPermissionViewSet, self).get_permissions() + [
    #         PomsObjectPermission()
    #     ]

    def get_serializer(self, *args, **kwargs):
        kwargs['show_object_permissions'] = (self.action != 'list')
        return super(AbstractWithObjectPermissionViewSet, self).get_serializer(*args, **kwargs)
