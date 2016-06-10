from poms.chats.models import Thread, ThreadStatus
from poms.common.fields import FilteredPrimaryKeyRelatedField
from poms.obj_perms.filters import FieldObjectPermissionBackend
from poms.users.filters import OwnerByMasterUserFilter


class ThreadField(FilteredPrimaryKeyRelatedField):
    queryset = Thread.objects
    filter_backends = [
        OwnerByMasterUserFilter,
        FieldObjectPermissionBackend,
    ]


class ThreadStatusField(FilteredPrimaryKeyRelatedField):
    queryset = ThreadStatus.objects
    filter_backends = [OwnerByMasterUserFilter]
