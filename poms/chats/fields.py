from poms.chats.models import Thread, ThreadGroup
from poms.common.fields import PrimaryKeyRelatedFilteredField
from poms.obj_perms.fields import PrimaryKeyRelatedFilteredWithObjectPermissionField
from poms.users.filters import OwnerByMasterUserFilter


class ThreadGroupField(PrimaryKeyRelatedFilteredField):
    queryset = ThreadGroup.objects
    filter_backends = [
        OwnerByMasterUserFilter,
    ]


class ThreadField(PrimaryKeyRelatedFilteredWithObjectPermissionField):
    queryset = Thread.objects
    filter_backends = [
        OwnerByMasterUserFilter,
    ]
