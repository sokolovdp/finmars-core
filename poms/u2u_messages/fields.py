from poms.api.fields import FilteredPrimaryKeyRelatedField
from poms.u2u_messages.models import Channel
from poms.users.filters import OwnerByMasterUserFilter


class ChannelField(FilteredPrimaryKeyRelatedField):
    queryset = Channel.objects
    filter_backends = [OwnerByMasterUserFilter]

