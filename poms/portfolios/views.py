from __future__ import unicode_literals

from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter

from poms.common.filters import ClassifierFilterSetBase
from poms.common.views import ClassifierViewSetBase, PomsViewSetBase
from poms.obj_attrs.filters import AttributePrefetchFilter
from poms.obj_attrs.views import AttributeTypeViewSetBase
from poms.portfolios.models import PortfolioClassifier, Portfolio, PortfolioAttributeType
from poms.portfolios.serializers import PortfolioClassifierSerializer, PortfolioSerializer, \
    PortfolioAttributeTypeSerializer
from poms.tags.filters import TagPrefetchFilter
from poms.users.filters import OwnerByMasterUserFilter


class PortfolioClassifierFilterSet(ClassifierFilterSetBase):
    class Meta(ClassifierFilterSetBase.Meta):
        model = PortfolioClassifier


class PortfolioClassifierViewSet(ClassifierViewSetBase):
    queryset = PortfolioClassifier.objects.all()
    serializer_class = PortfolioClassifierSerializer
    filter_class = PortfolioClassifierFilterSet


class PortfolioAttributeTypeViewSet(AttributeTypeViewSetBase):
    queryset = PortfolioAttributeType.objects.all()
    serializer_class = PortfolioAttributeTypeSerializer


class PortfolioViewSet(PomsViewSetBase):
    queryset = Portfolio.objects.all()
    serializer_class = PortfolioSerializer
    filter_backends = [OwnerByMasterUserFilter, AttributePrefetchFilter, TagPrefetchFilter,
                       DjangoFilterBackend, OrderingFilter, SearchFilter, ]
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']
