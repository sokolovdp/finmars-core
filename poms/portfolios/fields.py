from __future__ import unicode_literals

from poms.common.fields import FilteredPrimaryKeyRelatedField
from poms.obj_perms.filters import ObjectPermissionPrefetchFilter, ObjectPermissionFilter
from poms.portfolios.models import PortfolioClassifier, Portfolio, PortfolioAttributeType
from poms.users.filters import OwnerByMasterUserFilter


class PortfolioClassifierField(FilteredPrimaryKeyRelatedField):
    queryset = PortfolioClassifier.objects
    filter_backends = [OwnerByMasterUserFilter]


class PortfolioClassifierRootField(FilteredPrimaryKeyRelatedField):
    queryset = PortfolioClassifier.objects.filter(parent__isnull=True)
    filter_backends = [OwnerByMasterUserFilter]


class PortfolioAttributeTypeField(FilteredPrimaryKeyRelatedField):
    queryset = PortfolioAttributeType.objects
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionPrefetchFilter,
        ObjectPermissionFilter,
    ]


class PortfolioField(FilteredPrimaryKeyRelatedField):
    queryset = Portfolio.objects
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionPrefetchFilter,
        ObjectPermissionFilter,
    ]
