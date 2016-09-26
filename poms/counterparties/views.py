from __future__ import unicode_literals

import django_filters
from rest_framework.filters import FilterSet

from poms.common.filters import CharFilter, ModelWithPermissionMultipleChoiceFilter, NoOpFilter
from poms.common.views import AbstractModelViewSet
from poms.counterparties.models import Counterparty, Responsible, CounterpartyAttributeType, ResponsibleAttributeType, \
    CounterpartyGroup, ResponsibleGroup, CounterpartyClassifier, ResponsibleClassifier
from poms.counterparties.serializers import CounterpartySerializer, ResponsibleSerializer, \
    CounterpartyAttributeTypeSerializer, \
    ResponsibleAttributeTypeSerializer, CounterpartyGroupSerializer, ResponsibleGroupSerializer, \
    CounterpartyClassifierNodeSerializer, ResponsibleClassifierNodeSerializer, \
    CounterpartyAttributeTypeBulkObjectPermissionSerializer, CounterpartyGroupBulkObjectPermissionSerializer, \
    CounterpartyBulkObjectPermissionSerializer, ResponsibleAttributeTypeBulkObjectPermissionSerializer, \
    ResponsibleGroupBulkObjectPermissionSerializer, ResponsibleBulkObjectPermissionSerializer
from poms.obj_attrs.filters import AttributeTypeValueTypeFilter
from poms.obj_attrs.views import AbstractAttributeTypeViewSet, AbstractClassifierViewSet
from poms.obj_perms.filters import ObjectPermissionMemberFilter, ObjectPermissionGroupFilter, \
    ObjectPermissionPermissionFilter
from poms.obj_perms.views import AbstractWithObjectPermissionViewSet
from poms.portfolios.models import Portfolio
from poms.tags.filters import TagFilterBackend, TagFilter
from poms.users.filters import OwnerByMasterUserFilter


class CounterpartyAttributeTypeFilterSet(FilterSet):
    id = NoOpFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    value_type = AttributeTypeValueTypeFilter()
    member = ObjectPermissionMemberFilter(object_permission_model=CounterpartyAttributeType)
    member_group = ObjectPermissionGroupFilter(object_permission_model=CounterpartyAttributeType)
    permission = ObjectPermissionPermissionFilter(object_permission_model=CounterpartyAttributeType)

    class Meta:
        model = CounterpartyAttributeType
        fields = []


class CounterpartyAttributeTypeViewSet(AbstractAttributeTypeViewSet):
    queryset = CounterpartyAttributeType.objects.prefetch_related('classifiers')
    serializer_class = CounterpartyAttributeTypeSerializer
    bulk_objects_permissions_serializer_class = CounterpartyAttributeTypeBulkObjectPermissionSerializer
    filter_class = CounterpartyAttributeTypeFilterSet


class CounterpartyClassifierFilterSet(FilterSet):
    id = NoOpFilter()
    name = CharFilter()
    level = django_filters.NumberFilter()
    attribute_type = ModelWithPermissionMultipleChoiceFilter(model=CounterpartyAttributeType)

    class Meta:
        model = CounterpartyClassifier
        fields = []


class CounterpartyClassifierViewSet(AbstractClassifierViewSet):
    queryset = CounterpartyClassifier.objects
    serializer_class = CounterpartyClassifierNodeSerializer
    filter_class = CounterpartyClassifierFilterSet


class CounterpartyGroupFilterSet(FilterSet):
    id = NoOpFilter()
    is_deleted = django_filters.BooleanFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    # is_default = IsDefaultFilter(source='counterparty_group')
    tag = TagFilter(model=CounterpartyGroup)
    member = ObjectPermissionMemberFilter(object_permission_model=CounterpartyGroup)
    member_group = ObjectPermissionGroupFilter(object_permission_model=CounterpartyGroup)
    permission = ObjectPermissionPermissionFilter(object_permission_model=CounterpartyGroup)

    class Meta:
        model = CounterpartyGroup
        fields = []


class CounterpartyGroupViewSet(AbstractWithObjectPermissionViewSet):
    queryset = CounterpartyGroup.objects.prefetch_related('master_user')
    serializer_class = CounterpartyGroupSerializer
    bulk_objects_permissions_serializer_class = CounterpartyGroupBulkObjectPermissionSerializer
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        TagFilterBackend,
    ]
    filter_class = CounterpartyGroupFilterSet
    ordering_fields = [
        'user_code', 'name', 'short_name'
    ]
    search_fields = [
        'user_code', 'name', 'short_name'
    ]
    # has_feature_is_deleted = True


class CounterpartyFilterSet(FilterSet):
    id = NoOpFilter()
    is_deleted = django_filters.BooleanFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    is_valid_for_all_portfolios = django_filters.BooleanFilter()
    group = ModelWithPermissionMultipleChoiceFilter(model=CounterpartyGroup)
    portfolio = ModelWithPermissionMultipleChoiceFilter(model=Portfolio, name='portfolios')
    tag = TagFilter(model=Counterparty)
    member = ObjectPermissionMemberFilter(object_permission_model=Counterparty)
    member_group = ObjectPermissionGroupFilter(object_permission_model=Counterparty)
    permission = ObjectPermissionPermissionFilter(object_permission_model=Counterparty)

    class Meta:
        model = Counterparty
        fields = []


class CounterpartyViewSet(AbstractWithObjectPermissionViewSet):
    queryset = Counterparty.objects.prefetch_related(
        'master_user', 'group', 'portfolios', 'attributes', 'attributes__attribute_type'
    )
    prefetch_permissions_for = ('group', 'portfolios', 'attributes__attribute_type')
    serializer_class = CounterpartySerializer
    bulk_objects_permissions_serializer_class = CounterpartyBulkObjectPermissionSerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        TagFilterBackend,
    ]
    filter_class = CounterpartyFilterSet
    ordering_fields = [
        'user_code', 'name', 'short_name',
        'group__user_code', 'group__name', 'group__short_name',
    ]
    search_fields = [
        'user_code', 'name', 'short_name',
    ]
    # has_feature_is_deleted = True


# Responsible ----


class ResponsibleAttributeTypeFilterSet(FilterSet):
    id = NoOpFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    value_type = AttributeTypeValueTypeFilter()
    member = ObjectPermissionMemberFilter(object_permission_model=ResponsibleAttributeType)
    member_group = ObjectPermissionGroupFilter(object_permission_model=ResponsibleAttributeType)
    permission = ObjectPermissionPermissionFilter(object_permission_model=ResponsibleAttributeType)

    class Meta:
        model = ResponsibleAttributeType
        fields = []


class ResponsibleAttributeTypeViewSet(AbstractAttributeTypeViewSet):
    queryset = ResponsibleAttributeType.objects.prefetch_related('classifiers')
    serializer_class = ResponsibleAttributeTypeSerializer
    bulk_objects_permissions_serializer_class = ResponsibleAttributeTypeBulkObjectPermissionSerializer
    filter_class = ResponsibleAttributeTypeFilterSet


class ResponsibleClassifierFilterSet(FilterSet):
    id = NoOpFilter()
    name = CharFilter()
    level = django_filters.NumberFilter()
    attribute_type = ModelWithPermissionMultipleChoiceFilter(model=ResponsibleAttributeType)

    class Meta:
        model = ResponsibleClassifier
        fields = []


class ResponsibleClassifierViewSet(AbstractClassifierViewSet):
    queryset = ResponsibleClassifier.objects
    serializer_class = ResponsibleClassifierNodeSerializer
    filter_class = ResponsibleClassifierFilterSet


class ResponsibleGroupFilterSet(FilterSet):
    id = NoOpFilter()
    is_deleted = django_filters.BooleanFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    tag = TagFilter(model=ResponsibleGroup)
    member = ObjectPermissionMemberFilter(object_permission_model=ResponsibleGroup)
    member_group = ObjectPermissionGroupFilter(object_permission_model=ResponsibleGroup)
    permission = ObjectPermissionPermissionFilter(object_permission_model=ResponsibleGroup)

    class Meta:
        model = ResponsibleGroup
        fields = []


class ResponsibleGroupViewSet(AbstractWithObjectPermissionViewSet):
    queryset = ResponsibleGroup.objects.prefetch_related('master_user')
    serializer_class = ResponsibleGroupSerializer
    bulk_objects_permissions_serializer_class = ResponsibleGroupBulkObjectPermissionSerializer
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        TagFilterBackend,
    ]
    filter_class = ResponsibleGroupFilterSet
    ordering_fields = [
        'user_code', 'name', 'short_name'
    ]
    search_fields = [
        'user_code', 'name', 'short_name'
    ]
    # has_feature_is_deleted = True


class ResponsibleFilterSet(FilterSet):
    id = NoOpFilter()
    is_deleted = django_filters.BooleanFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    is_valid_for_all_portfolios = django_filters.BooleanFilter()
    group = ModelWithPermissionMultipleChoiceFilter(model=CounterpartyGroup)
    portfolio = ModelWithPermissionMultipleChoiceFilter(model=Portfolio, name='portfolios')
    tag = TagFilter(model=Responsible)
    member = ObjectPermissionMemberFilter(object_permission_model=Responsible)
    member_group = ObjectPermissionGroupFilter(object_permission_model=Responsible)
    permission = ObjectPermissionPermissionFilter(object_permission_model=Responsible)

    class Meta:
        model = Responsible
        fields = []


class ResponsibleViewSet(AbstractWithObjectPermissionViewSet):
    queryset = Responsible.objects.prefetch_related(
        'master_user', 'group', 'portfolios', 'attributes', 'attributes__attribute_type'
    )
    prefetch_permissions_for = ('group', 'portfolios', 'attributes__attribute_type')
    serializer_class = ResponsibleSerializer
    bulk_objects_permissions_serializer_class = ResponsibleBulkObjectPermissionSerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        TagFilterBackend,
    ]
    filter_class = ResponsibleFilterSet
    ordering_fields = [
        'user_code', 'name', 'short_name',
        'group__user_code', 'group__name', 'group__short_name',
    ]
    search_fields = [
        'user_code', 'name', 'short_name'
    ]
    # has_feature_is_deleted = True
