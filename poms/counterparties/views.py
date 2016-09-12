from __future__ import unicode_literals

from rest_framework.filters import FilterSet

from poms.common.filters import CharFilter, ModelWithPermissionMultipleChoiceFilter, IsDefaultFilter
from poms.common.views import AbstractModelViewSet
from poms.counterparties.models import Counterparty, Responsible, CounterpartyAttributeType, ResponsibleAttributeType, \
    CounterpartyGroup, ResponsibleGroup, CounterpartyClassifier, ResponsibleClassifier
from poms.counterparties.serializers import CounterpartySerializer, ResponsibleSerializer, \
    CounterpartyAttributeTypeSerializer, \
    ResponsibleAttributeTypeSerializer, CounterpartyGroupSerializer, ResponsibleGroupSerializer, \
    CounterpartyClassifierNodeSerializer, ResponsibleClassifierNodeSerializer
from poms.obj_attrs.views import AbstractAttributeTypeViewSet, AbstractClassifierViewSet
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


class CounterpartyClassifierFilterSet(FilterSet):
    name = CharFilter()
    attribute_type = ModelWithPermissionMultipleChoiceFilter(model=CounterpartyAttributeType)

    # parent = ModelWithPermissionMultipleChoiceFilter(model=CounterpartyClassifier, master_user_path='attribute_type__master_user')

    class Meta:
        model = CounterpartyClassifier
        fields = ['name', 'level', 'attribute_type', ]


class CounterpartyClassifierViewSet(AbstractClassifierViewSet):
    queryset = CounterpartyClassifier.objects
    serializer_class = CounterpartyClassifierNodeSerializer
    filter_class = CounterpartyClassifierFilterSet


class CounterpartyGroupFilterSet(FilterSet):
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    is_default = IsDefaultFilter(source='counterparty_group')
    tag = TagFilter(model=CounterpartyGroup)

    class Meta:
        model = CounterpartyGroup
        fields = ['user_code', 'name', 'short_name', 'is_default', 'tag']


class CounterpartyGroupViewSet(AbstractModelViewSet):
    queryset = CounterpartyGroup.objects.select_related('master_user')
    serializer_class = CounterpartyGroupSerializer
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        TagFilterBackend,
    ]
    filter_class = CounterpartyGroupFilterSet
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']


class CounterpartyFilterSet(FilterSet):
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    is_default = IsDefaultFilter(source='counterparty')
    group = ModelWithPermissionMultipleChoiceFilter(model=CounterpartyGroup)
    portfolio = ModelWithPermissionMultipleChoiceFilter(model=Portfolio, name='portfolios')
    tag = TagFilter(model=Counterparty)

    class Meta:
        model = Counterparty
        fields = ['user_code', 'name', 'short_name', 'is_valid_for_all_portfolios', 'is_default',
                  'group', 'tag', 'portfolio']


class CounterpartyViewSet(AbstractWithObjectPermissionViewSet):
    queryset = Counterparty.objects.prefetch_related(
        'master_user', 'group', 'portfolios', 'attributes', 'attributes__attribute_type'
    )
    prefetch_permissions_for = ('group', 'portfolios', 'attributes__attribute_type')
    serializer_class = CounterpartySerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        TagFilterBackend,
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


class ResponsibleClassifierFilterSet(FilterSet):
    name = CharFilter()
    attribute_type = ModelWithPermissionMultipleChoiceFilter(model=ResponsibleAttributeType)

    class Meta:
        model = ResponsibleClassifier
        fields = ['name', 'level', 'attribute_type', ]


class ResponsibleClassifierViewSet(AbstractClassifierViewSet):
    queryset = ResponsibleClassifier.objects
    serializer_class = ResponsibleClassifierNodeSerializer
    filter_class = ResponsibleClassifierFilterSet


class ResponsibleGroupFilterSet(FilterSet):
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    is_default = IsDefaultFilter(source='responsible_group')
    tag = TagFilter(model=ResponsibleGroup)

    class Meta:
        model = ResponsibleGroup
        fields = ['user_code', 'name', 'short_name', 'is_default', 'tag']


class ResponsibleGroupViewSet(AbstractModelViewSet):
    queryset = ResponsibleGroup.objects.select_related('master_user')
    serializer_class = ResponsibleGroupSerializer
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        TagFilterBackend,
    ]
    filter_class = ResponsibleGroupFilterSet
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']


class ResponsibleFilterSet(FilterSet):
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    is_default = IsDefaultFilter(source='responsible')
    group = ModelWithPermissionMultipleChoiceFilter(model=CounterpartyGroup)
    portfolio = ModelWithPermissionMultipleChoiceFilter(model=Portfolio, name='portfolios')
    tag = TagFilter(model=Responsible)

    class Meta:
        model = Responsible
        fields = ['user_code', 'name', 'short_name', 'is_valid_for_all_portfolios', 'is_default',
                  'group', 'portfolio', 'tag']


class ResponsibleViewSet(AbstractWithObjectPermissionViewSet):
    queryset = Responsible.objects.prefetch_related(
        'master_user', 'group', 'portfolios', 'attributes', 'attributes__attribute_type'
    )
    prefetch_permissions_for = ('group', 'portfolios', 'attributes__attribute_type')
    serializer_class = ResponsibleSerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        TagFilterBackend,
    ]
    filter_class = ResponsibleFilterSet
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']
