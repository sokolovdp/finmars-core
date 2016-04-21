from __future__ import unicode_literals

from poms.api.fields import FilteredPrimaryKeyRelatedField
from poms.common.filters import ClassifierRootFilter
from poms.counterparties.models import CounterpartyClassifier, Counterparty, Responsible, ResponsibleClassifier, \
    CounterpartyAttributeType
from poms.users.filters import OwnerByMasterUserFilter


class CounterpartyAttributeTypeField(FilteredPrimaryKeyRelatedField):
    queryset = CounterpartyAttributeType.objects
    filter_backends = [OwnerByMasterUserFilter]


class CounterpartyClassifierField(FilteredPrimaryKeyRelatedField):
    queryset = CounterpartyClassifier.objects
    filter_backends = [OwnerByMasterUserFilter]


class CounterpartyClassifierRootField(FilteredPrimaryKeyRelatedField):
    queryset = CounterpartyClassifier.objects
    filter_backends = [OwnerByMasterUserFilter, ClassifierRootFilter]


class CounterpartyField(FilteredPrimaryKeyRelatedField):
    queryset = Counterparty.objects
    filter_backends = [OwnerByMasterUserFilter]


class ResponsibleAttributeTypeField(FilteredPrimaryKeyRelatedField):
    queryset = CounterpartyAttributeType.objects
    filter_backends = [OwnerByMasterUserFilter]


class ResponsibleClassifierField(FilteredPrimaryKeyRelatedField):
    queryset = ResponsibleClassifier.objects
    filter_backends = [OwnerByMasterUserFilter]


class ResponsibleClassifierRootField(FilteredPrimaryKeyRelatedField):
    queryset = ResponsibleClassifier.objects
    filter_backends = [OwnerByMasterUserFilter, ClassifierRootFilter]


class ResponsibleField(FilteredPrimaryKeyRelatedField):
    queryset = Responsible.objects
    filter_backends = [OwnerByMasterUserFilter]
