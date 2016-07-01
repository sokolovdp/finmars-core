from __future__ import unicode_literals

from poms.obj_perms.fields import PrimaryKeyRelatedFilteredWithObjectPermissionField
from poms.strategies.models import Strategy1, Strategy2, Strategy3
from poms.users.filters import OwnerByMasterUserFilter


# class Strategy1Field(FilteredPrimaryKeyRelatedField):
#     queryset = Strategy1.objects
#     filter_backends = [
#         OwnerByMasterUserFilter,
#         FieldObjectPermissionBackend,
#     ]
class Strategy1Field(PrimaryKeyRelatedFilteredWithObjectPermissionField):
    queryset = Strategy1.objects
    filter_backends = [
        OwnerByMasterUserFilter,
    ]


# class Strategy2Field(FilteredPrimaryKeyRelatedField):
#     queryset = Strategy2.objects
#     filter_backends = [
#         OwnerByMasterUserFilter,
#         FieldObjectPermissionBackend,
#     ]
class Strategy2Field(PrimaryKeyRelatedFilteredWithObjectPermissionField):
    queryset = Strategy2.objects
    filter_backends = [
        OwnerByMasterUserFilter,
    ]


# class Strategy3Field(FilteredPrimaryKeyRelatedField):
#     queryset = Strategy3.objects
#     filter_backends = [
#         OwnerByMasterUserFilter,
#         FieldObjectPermissionBackend,
#     ]
class Strategy3Field(PrimaryKeyRelatedFilteredWithObjectPermissionField):
    queryset = Strategy3.objects
    filter_backends = [
        OwnerByMasterUserFilter,
    ]
