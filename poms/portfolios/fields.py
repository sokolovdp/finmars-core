from __future__ import unicode_literals

from poms.api.fields import FilteredPrimaryKeyRelatedField
from poms.portfolios.models import PortfolioClassifier, Portfolio
from poms.users.filters import OwnerByMasterUserFilter


class PortfolioClassifierField(FilteredPrimaryKeyRelatedField):
    queryset = PortfolioClassifier.objects
    filter_backends = [OwnerByMasterUserFilter]


class PortfolioField(FilteredPrimaryKeyRelatedField):
    queryset = Portfolio.objects
    filter_backends = [OwnerByMasterUserFilter]
