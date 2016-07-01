from __future__ import unicode_literals

from rest_framework.filters import DjangoFilterBackend, SearchFilter, FilterSet, OrderingFilter

from poms.common.filters import CharFilter, ModelWithPermissionMultipleChoiceFilter
from poms.common.views import PomsViewSetBase
from poms.counterparties.models import Counterparty, Responsible, CounterpartyAttributeType, ResponsibleAttributeType
from poms.counterparties.serializers import CounterpartySerializer, ResponsibleSerializer, \
    CounterpartyAttributeTypeSerializer, \
    ResponsibleAttributeTypeSerializer
from poms.obj_attrs.filters import AttributePrefetchFilter
from poms.obj_attrs.views import AttributeTypeViewSetBase
from poms.obj_perms.filters import ObjectPermissionBackend
from poms.obj_perms.permissions import ObjectPermissionBase
from poms.portfolios.models import Portfolio
from poms.tags.filters import TagFilterBackend, TagFilter
from poms.users.filters import OwnerByMasterUserFilter


class CounterpartyAttributeTypeFilterSet(FilterSet):
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()

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

    def get_serializer(self, *args, **kwargs):
        kwargs['show_object_permissions'] = (self.action != 'list')
        return super(CounterpartyAttributeTypeViewSet, self).get_serializer(*args, **kwargs)


class CounterpartyFilterSet(FilterSet):
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    portfolio = ModelWithPermissionMultipleChoiceFilter(model=Portfolio, name='portfolios')
    tag = TagFilter(model=Counterparty)

    class Meta:
        model = Counterparty
        fields = ['user_code', 'name', 'short_name', 'tag', 'portfolio']


class CounterpartyViewSet(PomsViewSetBase):
    queryset = Counterparty.objects.prefetch_related(
        'portfolios',
        'portfolios__user_object_permissions', 'portfolios__user_object_permissions__permission',
        'portfolios__group_object_permissions', 'portfolios__group_object_permissions__permission',
    )
    serializer_class = CounterpartySerializer
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionBackend,
        TagFilterBackend,
        AttributePrefetchFilter,
        DjangoFilterBackend,
        OrderingFilter,
        # OrderingWithAttributesFilter,
        SearchFilter,
    ]
    filter_class = CounterpartyFilterSet
    permission_classes = PomsViewSetBase.permission_classes + [
        ObjectPermissionBase
    ]
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']

    def get_serializer(self, *args, **kwargs):
        kwargs['show_object_permissions'] = (self.action != 'list')
        return super(CounterpartyViewSet, self).get_serializer(*args, **kwargs)


class ResponsibleAttributeTypeFilterSet(FilterSet):
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()

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

    def get_serializer(self, *args, **kwargs):
        kwargs['show_object_permissions'] = (self.action != 'list')
        return super(ResponsibleAttributeTypeViewSet, self).get_serializer(*args, **kwargs)


class ResponsibleFilterSet(FilterSet):
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    portfolio = ModelWithPermissionMultipleChoiceFilter(model=Portfolio, name='portfolios')
    tag = TagFilter(model=Responsible)

    class Meta:
        model = Responsible
        fields = ['user_code', 'name', 'short_name', 'portfolio', 'tag']


class ResponsibleViewSet(PomsViewSetBase):
    queryset = Responsible.objects.prefetch_related(
        'portfolios',
        'portfolios__user_object_permissions', 'portfolios__user_object_permissions__permission',
        'portfolios__group_object_permissions', 'portfolios__group_object_permissions__permission',
    )
    serializer_class = ResponsibleSerializer
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionBackend,
        TagFilterBackend,
        AttributePrefetchFilter,
        DjangoFilterBackend,
        OrderingFilter,
        # OrderingWithAttributesFilter,
        SearchFilter,
    ]
    filter_class = ResponsibleFilterSet
    permission_classes = PomsViewSetBase.permission_classes + [
        ObjectPermissionBase
    ]
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']

    def get_serializer(self, *args, **kwargs):
        kwargs['show_object_permissions'] = (self.action != 'list')
        return super(ResponsibleViewSet, self).get_serializer(*args, **kwargs)
