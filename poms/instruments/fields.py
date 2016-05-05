from __future__ import unicode_literals

from poms.common.fields import FilteredPrimaryKeyRelatedField
from poms.instruments.models import InstrumentClassifier, Instrument, InstrumentAttributeType, InstrumentType
from poms.users.filters import OwnerByMasterUserFilter


class InstrumentClassifierField(FilteredPrimaryKeyRelatedField):
    queryset = InstrumentClassifier.objects
    filter_backends = [OwnerByMasterUserFilter]


class InstrumentClassifierRootField(FilteredPrimaryKeyRelatedField):
    queryset = InstrumentClassifier.objects.filter(parent__isnull=True)
    filter_backends = [OwnerByMasterUserFilter]


class InstrumentAttributeTypeField(FilteredPrimaryKeyRelatedField):
    queryset = InstrumentAttributeType.objects
    filter_backends = [OwnerByMasterUserFilter]


class InstrumentTypeField(FilteredPrimaryKeyRelatedField):
    queryset = InstrumentType.objects
    filter_backends = [OwnerByMasterUserFilter]


class InstrumentField(FilteredPrimaryKeyRelatedField):
    queryset = Instrument.objects
    filter_backends = [OwnerByMasterUserFilter]
