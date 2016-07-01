from poms.chats.models import Thread, ThreadStatus
from poms.common.fields import PrimaryKeyRelatedFilteredField
from poms.obj_perms.fields import PrimaryKeyRelatedFilteredWithObjectPermissionField
from poms.users.filters import OwnerByMasterUserFilter


class ThreadStatusField(PrimaryKeyRelatedFilteredField):
    queryset = ThreadStatus.objects
    filter_backends = [OwnerByMasterUserFilter]


# class ThreadField(FilteredPrimaryKeyRelatedField):
#     queryset = Thread.objects
#     filter_backends = [
#         OwnerByMasterUserFilter,
#         FieldObjectPermissionBackend,
#     ]
class ThreadField(PrimaryKeyRelatedFilteredWithObjectPermissionField):
    queryset = Thread.objects
    filter_backends = [
        OwnerByMasterUserFilter,
    ]
