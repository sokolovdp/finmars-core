from __future__ import unicode_literals

from rest_framework.filters import FilterSet

from poms.common.filters import CharFilter, ModelWithPermissionMultipleChoiceFilter, IsDefaultFilter
from poms.counterparties.models import Counterparty, Responsible, CounterpartyAttributeType, ResponsibleAttributeType
from poms.counterparties.serializers import CounterpartySerializer, ResponsibleSerializer, \
    CounterpartyAttributeTypeSerializer, \
    ResponsibleAttributeTypeSerializer
from poms.obj_attrs.filters import AttributePrefetchFilter
from poms.obj_attrs.views import AbstractAttributeTypeViewSet
from poms.obj_perms.views import AbstractWithObjectPermissionViewSet
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


class CounterpartyAttributeTypeViewSet(AbstractAttributeTypeViewSet):
    queryset = CounterpartyAttributeType.objects.prefetch_related('classifiers')
    serializer_class = CounterpartyAttributeTypeSerializer
    filter_class = CounterpartyAttributeTypeFilterSet


class CounterpartyFilterSet(FilterSet):
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    is_default = IsDefaultFilter(source='counterparty')
    portfolio = ModelWithPermissionMultipleChoiceFilter(model=Portfolio, name='portfolios')
    tag = TagFilter(model=Counterparty)

    class Meta:
        model = Counterparty
        fields = ['user_code', 'name', 'short_name', 'is_default', 'tag', 'portfolio']


class CounterpartyViewSet(AbstractWithObjectPermissionViewSet):
    queryset = Counterparty.objects.select_related('master_user').prefetch_related(
        'portfolios'
    )
    prefetch_permissions_for = ('portfolios',)
    serializer_class = CounterpartySerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        TagFilterBackend,
        AttributePrefetchFilter,
    ]
    filter_class = CounterpartyFilterSet
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']


# Responsible ----


class ResponsibleAttributeTypeFilterSet(FilterSet):
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()

    class Meta:
        model = ResponsibleAttributeType
        fields = ['user_code', 'name', 'short_name']


class ResponsibleAttributeTypeViewSet(AbstractAttributeTypeViewSet):
    queryset = ResponsibleAttributeType.objects.prefetch_related('classifiers')
    serializer_class = ResponsibleAttributeTypeSerializer
    filter_class = ResponsibleAttributeTypeFilterSet


class ResponsibleFilterSet(FilterSet):
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    is_default = IsDefaultFilter(source='account_type')
    portfolio = ModelWithPermissionMultipleChoiceFilter(model=Portfolio, name='portfolios')
    tag = TagFilter(model=Responsible)

    class Meta:
        model = Responsible
        fields = ['user_code', 'name', 'short_name', 'is_default', 'portfolio', 'tag']


class ResponsibleViewSet(AbstractWithObjectPermissionViewSet):
    queryset = Responsible.objects.select_related('master_user').prefetch_related(
        'portfolios'
    )
    prefetch_permissions_for = ('portfolios',)
    serializer_class = ResponsibleSerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        TagFilterBackend,
        AttributePrefetchFilter,
    ]
    filter_class = ResponsibleFilterSet
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']
