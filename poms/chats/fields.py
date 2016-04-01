from poms.api.fields import FilteredPrimaryKeyRelatedField
from poms.chats.models import Thread
from poms.users.filters import OwnerByMasterUserFilter


class ThreadField(FilteredPrimaryKeyRelatedField):
    queryset = Thread.objects
    filter_backends = [OwnerByMasterUserFilter]

