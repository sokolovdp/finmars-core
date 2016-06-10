from __future__ import unicode_literals

from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter, FilterSet

from poms.common.filters import OrderingWithAttributesFilter
from poms.common.views import PomsViewSetBase
from poms.obj_attrs.filters import AttributePrefetchFilter
from poms.obj_attrs.views import AttributeTypeViewSetBase
from poms.obj_perms.filters import ObjectPermissionPrefetchFilter, ObjectPermissionFilter, AllFakeFilter
from poms.obj_perms.permissions import ObjectPermissionBase
from poms.portfolios.models import Portfolio, PortfolioAttributeType
from poms.portfolios.serializers import PortfolioSerializer, \
    PortfolioAttributeTypeSerializer
from poms.tags.filters import TagFakeFilter, TagFilterBackend
from poms.users.filters import OwnerByMasterUserFilter


# class PortfolioClassifierFilterSet(ClassifierFilterSetBase):
#     class Meta(ClassifierFilterSetBase.Meta):
#         model = PortfolioClassifier
#
#
# class PortfolioClassifierViewSet(ClassifierViewSetBase):
#     queryset = PortfolioClassifier.objects.all()
#     serializer_class = PortfolioClassifierSerializer
#     filter_class = PortfolioClassifierFilterSet
#
#
# class PortfolioClassifierNodeViewSet(ClassifierNodeViewSetBase):
#     queryset = PortfolioClassifier.objects.all()
#     serializer_class = PortfolioClassifierNodeSerializer
#     filter_class = PortfolioClassifierFilterSet


class PortfolioAttributeTypeFilterSet(FilterSet):
    class Meta:
        model = PortfolioAttributeType
        fields = ['user_code', 'name', 'short_name']


class PortfolioAttributeTypeViewSet(AttributeTypeViewSetBase):
    queryset = PortfolioAttributeType.objects.prefetch_related('classifiers')
    serializer_class = PortfolioAttributeTypeSerializer
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionPrefetchFilter,
        ObjectPermissionFilter,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    filter_class = PortfolioAttributeTypeFilterSet
    permission_classes = PomsViewSetBase.permission_classes + [
        ObjectPermissionBase,
    ]
    ordering_fields = ['user_code', 'name', 'short_name', ]
    search_fields = ['user_code', 'name', 'short_name', ]


class PortfolioFilterSet(FilterSet):
    all = AllFakeFilter()
    tags = TagFakeFilter()

    class Meta:
        model = Portfolio
        fields = ['user_code', 'name', 'short_name', 'all', 'tags']

    @staticmethod
    def tags_filter(queryset, value):
        return queryset


class PortfolioViewSet(PomsViewSetBase):
    queryset = Portfolio.objects
    serializer_class = PortfolioSerializer
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionPrefetchFilter,
        ObjectPermissionFilter,
        TagFilterBackend,
        AttributePrefetchFilter,
        DjangoFilterBackend,
        # OrderingFilter,
        OrderingWithAttributesFilter,
        SearchFilter,
    ]
    filter_class = PortfolioFilterSet
    permission_classes = PomsViewSetBase.permission_classes + [
        ObjectPermissionBase
    ]
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']
