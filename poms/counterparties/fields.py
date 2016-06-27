from __future__ import unicode_literals

from poms.common.fields import FilteredPrimaryKeyRelatedField
from poms.counterparties.models import CounterpartyClassifier, Counterparty, Responsible, ResponsibleClassifier, \
    CounterpartyAttributeType, ResponsibleAttributeType
from poms.obj_attrs.filters import AttributeClassifierBaseField
from poms.obj_perms.filters import FieldObjectPermissionBackend
from poms.users.filters import OwnerByMasterUserFilter


class CounterpartyAttributeTypeField(FilteredPrimaryKeyRelatedField):
    queryset = CounterpartyAttributeType.objects
    filter_backends = [
        OwnerByMasterUserFilter,
        FieldObjectPermissionBackend,
    ]


class CounterpartyClassifierField(AttributeClassifierBaseField):
    queryset = CounterpartyClassifier.objects


# class CounterpartyClassifierRootField(FilteredPrimaryKeyRelatedField):
#     queryset = CounterpartyClassifier.objects
#     filter_backends = [OwnerByMasterUserFilter, ClassifierRootFilter]


class CounterpartyField(FilteredPrimaryKeyRelatedField):
    queryset = Counterparty.objects
    filter_backends = [
        OwnerByMasterUserFilter,
        FieldObjectPermissionBackend,
    ]


class ResponsibleAttributeTypeField(FilteredPrimaryKeyRelatedField):
    queryset = ResponsibleAttributeType.objects
    filter_backends = [
        OwnerByMasterUserFilter,
        FieldObjectPermissionBackend,
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
        FieldObjectPermissionBackend,
    ]
