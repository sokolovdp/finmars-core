from __future__ import unicode_literals

from poms.common.fields import FilteredPrimaryKeyRelatedField
from poms.obj_attrs.filters import AttributeClassifierBaseField
from poms.obj_perms.filters import FieldObjectPermissionBackend
from poms.portfolios.models import PortfolioClassifier, Portfolio, PortfolioAttributeType
from poms.users.filters import OwnerByMasterUserFilter


class PortfolioClassifierField(AttributeClassifierBaseField):
    queryset = PortfolioClassifier.objects


# class PortfolioClassifierRootField(FilteredPrimaryKeyRelatedField):
#     queryset = PortfolioClassifier.objects.filter(parent__isnull=True)
#     filter_backends = [OwnerByMasterUserFilter]


class PortfolioAttributeTypeField(FilteredPrimaryKeyRelatedField):
    queryset = PortfolioAttributeType.objects
    filter_backends = [
        OwnerByMasterUserFilter,
        FieldObjectPermissionBackend,
    ]


class PortfolioField(FilteredPrimaryKeyRelatedField):
    queryset = Portfolio.objects
    filter_backends = [
        OwnerByMasterUserFilter,
        FieldObjectPermissionBackend,
    ]
