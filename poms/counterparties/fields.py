from __future__ import unicode_literals

from poms.common.fields import PrimaryKeyRelatedFilteredField
from poms.counterparties.models import CounterpartyClassifier, Counterparty, Responsible, ResponsibleClassifier, \
    CounterpartyAttributeType, ResponsibleAttributeType
from poms.obj_attrs.filters import AttributeClassifierBaseField
from poms.obj_perms.fields import PrimaryKeyRelatedFilteredWithObjectPermissionField
from poms.obj_perms.filters import ObjectPermissionBackend
from poms.users.filters import OwnerByMasterUserFilter


class CounterpartyAttributeTypeField(PrimaryKeyRelatedFilteredField):
    queryset = CounterpartyAttributeType.objects
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionBackend,
    ]


class CounterpartyClassifierField(AttributeClassifierBaseField):
    queryset = CounterpartyClassifier.objects


# class CounterpartyField(FilteredPrimaryKeyRelatedField):
#     queryset = Counterparty.objects
#     filter_backends = [
#         OwnerByMasterUserFilter,
#         FieldObjectPermissionBackend,
#     ]
class CounterpartyField(PrimaryKeyRelatedFilteredWithObjectPermissionField):
    queryset = Counterparty.objects
    filter_backends = [
        OwnerByMasterUserFilter,
    ]


class ResponsibleAttributeTypeField(PrimaryKeyRelatedFilteredField):
    queryset = ResponsibleAttributeType.objects
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionBackend,
    ]


class ResponsibleClassifierField(AttributeClassifierBaseField):
    queryset = ResponsibleClassifier.objects
    # filter_backends = [OwnerByMasterUserFilter]


# class ResponsibleField(FilteredPrimaryKeyRelatedField):
#     queryset = Responsible.objects
#     filter_backends = [
#         OwnerByMasterUserFilter,
#         FieldObjectPermissionBackend,
#     ]
class ResponsibleField(PrimaryKeyRelatedFilteredWithObjectPermissionField):
    queryset = Responsible.objects
    filter_backends = [
        OwnerByMasterUserFilter,
    ]
