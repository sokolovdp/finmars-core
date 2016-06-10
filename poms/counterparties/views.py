from __future__ import unicode_literals

from rest_framework.filters import DjangoFilterBackend, SearchFilter, FilterSet, OrderingFilter

from poms.common.filters import OrderingWithAttributesFilter
from poms.common.views import PomsViewSetBase
from poms.counterparties.models import Counterparty, Responsible, CounterpartyAttributeType, ResponsibleAttributeType
from poms.counterparties.serializers import CounterpartySerializer, ResponsibleSerializer, \
    CounterpartyAttributeTypeSerializer, \
    ResponsibleAttributeTypeSerializer
from poms.obj_attrs.filters import AttributePrefetchFilter
from poms.obj_attrs.views import AttributeTypeViewSetBase
from poms.obj_perms.filters import AllFakeFilter, \
    ObjectPermissionBackend
from poms.obj_perms.permissions import ObjectPermissionBase
from poms.tags.filters import TagFakeFilter, TagFilterBackend
from poms.users.filters import OwnerByMasterUserFilter


class CounterpartyAttributeTypeFilterSet(FilterSet):
    class Meta:
        model = CounterpartyAttributeType
        fields = ['user_code', 'name', 'short_name']


class CounterpartyAttributeTypeViewSet(AttributeTypeViewSetBase):
    queryset = CounterpartyAttributeType.objects.prefetch_related('classifiers')
    serializer_class = CounterpartyAttributeTypeSerializer
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionBackend,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    filter_class = CounterpartyAttributeTypeFilterSet
    permission_classes = PomsViewSetBase.permission_classes + [
        ObjectPermissionBase,
    ]
    ordering_fields = ['user_code', 'name', 'short_name', ]
    search_fields = ['user_code', 'name', 'short_name', ]


class CounterpartyFilterSet(FilterSet):
    all = AllFakeFilter()
    tags = TagFakeFilter()

    class Meta:
        model = Counterparty
        fields = ['user_code', 'name', 'short_name', 'all', 'tags']


class CounterpartyViewSet(PomsViewSetBase):
    queryset = Counterparty.objects
    serializer_class = CounterpartySerializer
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionBackend,
        TagFilterBackend,
        AttributePrefetchFilter,
        DjangoFilterBackend,
        # OrderingFilter,
        OrderingWithAttributesFilter,
        SearchFilter,
    ]
    filter_class = CounterpartyFilterSet
    permission_classes = PomsViewSetBase.permission_classes + [
        ObjectPermissionBase
    ]
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']


class ResponsibleAttributeTypeFilterSet(FilterSet):
    class Meta:
        model = ResponsibleAttributeType
        fields = ['user_code', 'name', 'short_name']


class ResponsibleAttributeTypeViewSet(AttributeTypeViewSetBase):
    queryset = ResponsibleAttributeType.objects.prefetch_related('classifiers')
    serializer_class = ResponsibleAttributeTypeSerializer
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionBackend,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    filter_class = ResponsibleAttributeTypeFilterSet
    permission_classes = PomsViewSetBase.permission_classes + [
        ObjectPermissionBase,
    ]
    ordering_fields = ['user_code', 'name', 'short_name', ]
    search_fields = ['user_code', 'name', 'short_name', ]


class ResponsibleFilterSet(FilterSet):
    all = AllFakeFilter()
    tags = TagFakeFilter()

    class Meta:
        model = Responsible
        fields = ['user_code', 'name', 'short_name', 'all', 'tags']


class ResponsibleViewSet(PomsViewSetBase):
    queryset = Responsible.objects
    serializer_class = ResponsibleSerializer
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionBackend,
        TagFilterBackend,
        AttributePrefetchFilter,
        DjangoFilterBackend,
        # OrderingFilter,
        OrderingWithAttributesFilter,
        SearchFilter,
    ]
    filter_class = ResponsibleFilterSet
    permission_classes = PomsViewSetBase.permission_classes + [
        ObjectPermissionBase
    ]
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']
