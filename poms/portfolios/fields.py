from __future__ import unicode_literals

from poms.common.fields import PrimaryKeyRelatedFilteredField
from poms.obj_attrs.filters import AttributeClassifierBaseField
from poms.obj_perms.fields import PrimaryKeyRelatedFilteredWithObjectPermissionField
from poms.obj_perms.filters import ObjectPermissionBackend
from poms.portfolios.models import PortfolioClassifier, Portfolio, PortfolioAttributeType
from poms.users.filters import OwnerByMasterUserFilter


class PortfolioClassifierField(AttributeClassifierBaseField):
    queryset = PortfolioClassifier.objects


class PortfolioAttributeTypeField(PrimaryKeyRelatedFilteredField):
    queryset = PortfolioAttributeType.objects
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionBackend,
    ]


class PortfolioDefault(object):
    def set_context(self, serializer_field):
        request = serializer_field.context['request']
        self._master_user = request.user.master_user

    def __call__(self):
        return self._master_user.portfolio


class PortfolioField(PrimaryKeyRelatedFilteredWithObjectPermissionField):
    queryset = Portfolio.objects
    filter_backends = [
        OwnerByMasterUserFilter,
    ]
