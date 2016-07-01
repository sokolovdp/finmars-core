from __future__ import unicode_literals

from poms.common.fields import FilteredPrimaryKeyRelatedField
from poms.obj_attrs.filters import AttributeClassifierBaseField
from poms.obj_perms.fields import PrimaryKeyRelatedFilteredWithObjectPermissionField
from poms.obj_perms.filters import ObjectPermissionBackend
from poms.portfolios.models import PortfolioClassifier, Portfolio, PortfolioAttributeType
from poms.users.filters import OwnerByMasterUserFilter


class PortfolioClassifierField(AttributeClassifierBaseField):
    queryset = PortfolioClassifier.objects


class PortfolioAttributeTypeField(FilteredPrimaryKeyRelatedField):
    queryset = PortfolioAttributeType.objects
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionBackend,
    ]


# class PortfolioField(FilteredPrimaryKeyRelatedField):
#     queryset = Portfolio.objects
#     filter_backends = [
#         OwnerByMasterUserFilter,
#         FieldObjectPermissionBackend,
#     ]
class PortfolioField(PrimaryKeyRelatedFilteredWithObjectPermissionField):
    queryset = Portfolio.objects
    filter_backends = [
        OwnerByMasterUserFilter,
    ]
