from __future__ import unicode_literals

from poms.api.fields import FilteredPrimaryKeyRelatedField
from poms.counterparties.models import CounterpartyClassifier, Counterparty, Responsible
from poms.users.filters import OwnerByMasterUserFilter


class CounterpartyClassifierField(FilteredPrimaryKeyRelatedField):
    queryset = CounterpartyClassifier.objects
    filter_backends = [OwnerByMasterUserFilter]


class CounterpartyField(FilteredPrimaryKeyRelatedField):
    queryset = Counterparty.objects
    filter_backends = [OwnerByMasterUserFilter]


class ResponsibleField(FilteredPrimaryKeyRelatedField):
    queryset = Responsible.objects
    filter_backends = [OwnerByMasterUserFilter]
