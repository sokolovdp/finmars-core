from __future__ import unicode_literals

from poms.api.fields import FilteredPrimaryKeyRelatedField
from poms.instruments.models import InstrumentClassifier, Instrument
from poms.users.filters import OwnerByMasterUserFilter


class InstrumentClassifierField(FilteredPrimaryKeyRelatedField):
    queryset = InstrumentClassifier.objects
    filter_backends = [OwnerByMasterUserFilter]


class InstrumentField(FilteredPrimaryKeyRelatedField):
    queryset = Instrument.objects
    filter_backends = [OwnerByMasterUserFilter]
