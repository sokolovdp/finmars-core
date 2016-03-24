from __future__ import unicode_literals

from poms.api.fields import FilteredPrimaryKeyRelatedField
from poms.currencies.models import Currency
from poms.users.filters import OwnerByMasterUserFilter


class CurrencyField(FilteredPrimaryKeyRelatedField):
    queryset = Currency.objects
    filter_backends = [OwnerByMasterUserFilter]
