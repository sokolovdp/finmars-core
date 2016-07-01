from __future__ import unicode_literals

from poms.common.fields import PrimaryKeyRelatedFilteredField
from poms.currencies.models import Currency
from poms.users.filters import OwnerByMasterUserFilter


class CurrencyField(PrimaryKeyRelatedFilteredField):
    queryset = Currency.objects
    filter_backends = (
        OwnerByMasterUserFilter,
    )
