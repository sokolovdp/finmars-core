from __future__ import unicode_literals

from poms.common.fields import FilteredPrimaryKeyRelatedField
from poms.obj_perms.filters import ObjectPermissionPrefetchFilter, ObjectPermissionFilter
from poms.transactions.models import TransactionType, TransactionAttributeType
from poms.users.filters import OwnerByMasterUserFilter


class TransactionTypeField(FilteredPrimaryKeyRelatedField):
    queryset = TransactionType.objects
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionPrefetchFilter,
        ObjectPermissionFilter,
    ]


class TransactionAttributeTypeField(FilteredPrimaryKeyRelatedField):
    queryset = TransactionAttributeType.objects
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionPrefetchFilter,
        ObjectPermissionFilter,
    ]
