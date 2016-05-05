from __future__ import unicode_literals

from poms.common.fields import FilteredPrimaryKeyRelatedField
from poms.strategies.models import Strategy
from poms.users.filters import OwnerByMasterUserFilter


class StrategyField(FilteredPrimaryKeyRelatedField):
    queryset = Strategy.objects
    filter_backends = [OwnerByMasterUserFilter]


class StrategyRootField(FilteredPrimaryKeyRelatedField):
    queryset = Strategy.objects.filter(parent__isnull=True)
    filter_backends = [OwnerByMasterUserFilter]
