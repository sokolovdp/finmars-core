from poms.api.fields import FilteredPrimaryKeyRelatedField
from poms.chats.filters import ThreadObjectPermissionFilter
from poms.chats.models import Thread, ThreadStatus
from poms.users.filters import OwnerByMasterUserFilter


class ThreadField(FilteredPrimaryKeyRelatedField):
    queryset = Thread.objects
    filter_backends = [OwnerByMasterUserFilter, ThreadObjectPermissionFilter]


class ThreadStatusField(FilteredPrimaryKeyRelatedField):
    queryset = ThreadStatus.objects
    filter_backends = [OwnerByMasterUserFilter]
