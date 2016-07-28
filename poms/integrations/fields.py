from __future__ import unicode_literals

from poms.common.fields import PrimaryKeyRelatedFilteredField
from poms.integrations.models import InstrumentMapping
from poms.users.filters import OwnerByMasterUserFilter


class InstrumentMappingField(PrimaryKeyRelatedFilteredField):
    queryset = InstrumentMapping.objects
    filter_backends = [OwnerByMasterUserFilter]
