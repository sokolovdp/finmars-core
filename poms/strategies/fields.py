from __future__ import unicode_literals

from poms.common.fields import FilteredPrimaryKeyRelatedField
from poms.strategies.models import Strategy, Strategy1, Strategy2, Strategy3
from poms.users.filters import OwnerByMasterUserFilter


class StrategyField(FilteredPrimaryKeyRelatedField):
    queryset = Strategy.objects
    filter_backends = [OwnerByMasterUserFilter]


class StrategyRootField(FilteredPrimaryKeyRelatedField):
    queryset = Strategy.objects.filter(parent__isnull=True)
    filter_backends = [OwnerByMasterUserFilter]


class Strategy1Field(FilteredPrimaryKeyRelatedField):
    queryset = Strategy1.objects
    filter_backends = [OwnerByMasterUserFilter]


class Strategy1RootField(FilteredPrimaryKeyRelatedField):
    queryset = Strategy1.objects.filter(parent__isnull=True)
    filter_backends = [OwnerByMasterUserFilter]


class Strategy2Field(FilteredPrimaryKeyRelatedField):
    queryset = Strategy2.objects
    filter_backends = [OwnerByMasterUserFilter]


class Strategy2RootField(FilteredPrimaryKeyRelatedField):
    queryset = Strategy2.objects.filter(parent__isnull=True)
    filter_backends = [OwnerByMasterUserFilter]


class Strategy3Field(FilteredPrimaryKeyRelatedField):
    queryset = Strategy3.objects
    filter_backends = [OwnerByMasterUserFilter]


class Strategy3RootField(FilteredPrimaryKeyRelatedField):
    queryset = Strategy3.objects.filter(parent__isnull=True)
    filter_backends = [OwnerByMasterUserFilter]
