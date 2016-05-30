from __future__ import unicode_literals

from poms.common.fields import FilteredPrimaryKeyRelatedField
from poms.common.filters import ClassifierRootFilter
from poms.counterparties.models import CounterpartyClassifier, Counterparty, Responsible, ResponsibleClassifier, \
    CounterpartyAttributeType
from poms.obj_attrs.filters import AttributeClassifierBaseField
from poms.obj_perms.filters import ObjectPermissionPrefetchFilter, ObjectPermissionFilter
from poms.users.filters import OwnerByMasterUserFilter


class CounterpartyAttributeTypeField(FilteredPrimaryKeyRelatedField):
    queryset = CounterpartyAttributeType.objects
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionPrefetchFilter,
        ObjectPermissionFilter,
    ]


class CounterpartyClassifierField(AttributeClassifierBaseField):
    queryset = CounterpartyClassifier.objects
    # filter_backends = [OwnerByMasterUserFilter]


# class CounterpartyClassifierRootField(FilteredPrimaryKeyRelatedField):
#     queryset = CounterpartyClassifier.objects
#     filter_backends = [OwnerByMasterUserFilter, ClassifierRootFilter]


class CounterpartyField(FilteredPrimaryKeyRelatedField):
    queryset = Counterparty.objects
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionPrefetchFilter,
        ObjectPermissionFilter,
    ]


class ResponsibleAttributeTypeField(FilteredPrimaryKeyRelatedField):
    queryset = CounterpartyAttributeType.objects
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionPrefetchFilter,
        ObjectPermissionFilter,
    ]


class ResponsibleClassifierField(AttributeClassifierBaseField):
    queryset = ResponsibleClassifier.objects
    # filter_backends = [OwnerByMasterUserFilter]


# class ResponsibleClassifierRootField(FilteredPrimaryKeyRelatedField):
#     queryset = ResponsibleClassifier.objects
#     filter_backends = [OwnerByMasterUserFilter, ClassifierRootFilter]


class ResponsibleField(FilteredPrimaryKeyRelatedField):
    queryset = Responsible.objects
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionPrefetchFilter,
        ObjectPermissionFilter,
    ]
