from __future__ import unicode_literals

from poms.api.fields import FilteredPrimaryKeyRelatedField
from poms.transactions.models import TransactionType, TransactionAttributeType
from poms.users.filters import OwnerByMasterUserFilter


class TransactionTypeField(FilteredPrimaryKeyRelatedField):
    queryset = TransactionType.objects
    filter_backends = [OwnerByMasterUserFilter]


class TransactionAttributeTypeField(FilteredPrimaryKeyRelatedField):
    queryset = TransactionAttributeType.objects
    filter_backends = [OwnerByMasterUserFilter]
