from poms.chats.models import Thread, ThreadStatus
from poms.common.fields import FilteredPrimaryKeyRelatedField
from poms.obj_perms.filters import ObjectPermissionFilter, ObjectPermissionPrefetchFilter
from poms.users.filters import OwnerByMasterUserFilter


class ThreadField(FilteredPrimaryKeyRelatedField):
    queryset = Thread.objects
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionPrefetchFilter,
        ObjectPermissionFilter,
    ]


class ThreadStatusField(FilteredPrimaryKeyRelatedField):
    queryset = ThreadStatus.objects
    filter_backends = [OwnerByMasterUserFilter]
