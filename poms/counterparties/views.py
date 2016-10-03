from __future__ import unicode_literals

import django_filters
from django.db.models import Prefetch
from rest_framework.filters import FilterSet

from poms.common.filters import CharFilter, NoOpFilter, ModelExtWithPermissionMultipleChoiceFilter
from poms.counterparties.models import Counterparty, Responsible, CounterpartyAttributeType, ResponsibleAttributeType, \
    CounterpartyGroup, ResponsibleGroup, CounterpartyClassifier, ResponsibleClassifier, CounterpartyAttribute, \
    ResponsibleAttribute
from poms.counterparties.serializers import CounterpartySerializer, ResponsibleSerializer, \
    CounterpartyAttributeTypeSerializer, \
    ResponsibleAttributeTypeSerializer, CounterpartyGroupSerializer, ResponsibleGroupSerializer, \
    CounterpartyClassifierNodeSerializer, ResponsibleClassifierNodeSerializer
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
    public_name = CharFilter()
    value_type = AttributeTypeValueTypeFilter()
    member = ObjectPermissionMemberFilter(object_permission_model=CounterpartyAttributeType)
    member_group = ObjectPermissionGroupFilter(object_permission_model=CounterpartyAttributeType)
    permission = ObjectPermissionPermissionFilter(object_permission_model=CounterpartyAttributeType)

    class Meta:
        model = CounterpartyAttributeType
        fields = []


class CounterpartyAttributeTypeViewSet(AbstractAttributeTypeViewSet):
    queryset = CounterpartyAttributeType.objects.select_related('master_user').prefetch_related('classifiers')
    serializer_class = CounterpartyAttributeTypeSerializer
    # bulk_objects_permissions_serializer_class = CounterpartyAttributeTypeBulkObjectPermissionSerializer
    filter_class = CounterpartyAttributeTypeFilterSet


class CounterpartyClassifierFilterSet(FilterSet):
    id = NoOpFilter()
    name = CharFilter()
    level = django_filters.NumberFilter()
    attribute_type = ModelExtWithPermissionMultipleChoiceFilter(model=CounterpartyAttributeType)

    class Meta:
        model = CounterpartyClassifier
        fields = []


class CounterpartyClassifierViewSet(AbstractClassifierViewSet):
    queryset = CounterpartyClassifier.objects.select_related('attribute_type')
    serializer_class = CounterpartyClassifierNodeSerializer
    filter_class = CounterpartyClassifierFilterSet


class CounterpartyGroupFilterSet(FilterSet):
    id = NoOpFilter()
    is_deleted = django_filters.BooleanFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    public_name = CharFilter()
    tag = TagFilter(model=CounterpartyGroup)
    member = ObjectPermissionMemberFilter(object_permission_model=CounterpartyGroup)
    member_group = ObjectPermissionGroupFilter(object_permission_model=CounterpartyGroup)
    permission = ObjectPermissionPermissionFilter(object_permission_model=CounterpartyGroup)

    class Meta:
        model = CounterpartyGroup
        fields = []


class CounterpartyGroupViewSet(AbstractWithObjectPermissionViewSet):
    queryset = CounterpartyGroup.objects.select_related('master_user')
    serializer_class = CounterpartyGroupSerializer
    # bulk_objects_permissions_serializer_class = CounterpartyGroupBulkObjectPermissionSerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        TagFilterBackend,
    ]
    filter_class = CounterpartyGroupFilterSet
    ordering_fields = [
        'user_code', 'name', 'short_name', 'public_name',
    ]
    # search_fields = [
    #     'user_code', 'name', 'short_name'
    # ]
    # has_feature_is_deleted = True


class CounterpartyFilterSet(FilterSet):
    id = NoOpFilter()
    is_deleted = django_filters.BooleanFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    is_valid_for_all_portfolios = django_filters.BooleanFilter()
    group = ModelExtWithPermissionMultipleChoiceFilter(model=CounterpartyGroup)
    portfolio = ModelExtWithPermissionMultipleChoiceFilter(model=Portfolio, name='portfolios')
    tag = TagFilter(model=Counterparty)
    member = ObjectPermissionMemberFilter(object_permission_model=Counterparty)
    member_group = ObjectPermissionGroupFilter(object_permission_model=Counterparty)
    permission = ObjectPermissionPermissionFilter(object_permission_model=Counterparty)

    class Meta:
        model = Counterparty
        fields = []


class CounterpartyViewSet(AbstractWithObjectPermissionViewSet):
    queryset = Counterparty.objects.select_related(
        'master_user', 'group',
    ).prefetch_related(
        'portfolios',
        Prefetch('attributes', queryset=CounterpartyAttribute.objects.select_related('attribute_type', 'classifier')),
    )
    prefetch_permissions_for = (
        ('group', CounterpartyGroup),
        ('portfolios', Portfolio),
        ('attributes__attribute_type', CounterpartyAttributeType)
    )
    serializer_class = CounterpartySerializer
    # bulk_objects_permissions_serializer_class = CounterpartyBulkObjectPermissionSerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        TagFilterBackend,
    ]
    filter_class = CounterpartyFilterSet
    ordering_fields = [
        'user_code', 'name', 'short_name', 'public_name',
        'group', 'group__user_code', 'group__name', 'group__short_name', 'group__public_name',
    ]
    # search_fields = [
    #     'user_code', 'name', 'short_name',
    # ]
    # has_feature_is_deleted = True


# Responsible ----


class ResponsibleAttributeTypeFilterSet(FilterSet):
    id = NoOpFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    public_name = CharFilter()
    value_type = AttributeTypeValueTypeFilter()
    member = ObjectPermissionMemberFilter(object_permission_model=ResponsibleAttributeType)
    member_group = ObjectPermissionGroupFilter(object_permission_model=ResponsibleAttributeType)
    permission = ObjectPermissionPermissionFilter(object_permission_model=ResponsibleAttributeType)

    class Meta:
        model = ResponsibleAttributeType
        fields = []


class ResponsibleAttributeTypeViewSet(AbstractAttributeTypeViewSet):
    queryset = ResponsibleAttributeType.objects.select_related('master_user').prefetch_related('classifiers')
    serializer_class = ResponsibleAttributeTypeSerializer
    # bulk_objects_permissions_serializer_class = ResponsibleAttributeTypeBulkObjectPermissionSerializer
    filter_class = ResponsibleAttributeTypeFilterSet


class ResponsibleClassifierFilterSet(FilterSet):
    id = NoOpFilter()
    name = CharFilter()
    level = django_filters.NumberFilter()
    attribute_type = ModelExtWithPermissionMultipleChoiceFilter(model=ResponsibleAttributeType)

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
    queryset = ResponsibleGroup.objects.select_related('master_user')
    serializer_class = ResponsibleGroupSerializer
    # bulk_objects_permissions_serializer_class = ResponsibleGroupBulkObjectPermissionSerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        TagFilterBackend,
    ]
    filter_class = ResponsibleGroupFilterSet
    ordering_fields = [
        'user_code', 'name', 'short_name', 'public_name',
    ]
    # search_fields = [
    #     'user_code', 'name', 'short_name'
    # ]
    # has_feature_is_deleted = True


class ResponsibleFilterSet(FilterSet):
    id = NoOpFilter()
    is_deleted = django_filters.BooleanFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    public_name = CharFilter()
    is_valid_for_all_portfolios = django_filters.BooleanFilter()
    group = ModelExtWithPermissionMultipleChoiceFilter(model=CounterpartyGroup)
    portfolio = ModelExtWithPermissionMultipleChoiceFilter(model=Portfolio, name='portfolios')
    tag = TagFilter(model=Responsible)
    member = ObjectPermissionMemberFilter(object_permission_model=Responsible)
    member_group = ObjectPermissionGroupFilter(object_permission_model=Responsible)
    permission = ObjectPermissionPermissionFilter(object_permission_model=Responsible)

    class Meta:
        model = Responsible
        fields = []


class ResponsibleViewSet(AbstractWithObjectPermissionViewSet):
    queryset = Responsible.objects.select_related(
        'master_user', 'group',
    ).prefetch_related(
        'portfolios',
        Prefetch('attributes', queryset=ResponsibleAttribute.objects.select_related('attribute_type', 'classifier')),
    )
    prefetch_permissions_for = (
        ('group', ResponsibleGroup),
        ('portfolios', Portfolio),
        ('attributes__attribute_type', ResponsibleAttributeType)
    )
    serializer_class = ResponsibleSerializer
    # bulk_objects_permissions_serializer_class = ResponsibleBulkObjectPermissionSerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        TagFilterBackend,
    ]
    filter_class = ResponsibleFilterSet
    ordering_fields = [
        'user_code', 'name', 'short_name', 'public_name',
        'group', 'group__user_code', 'group__name', 'group__short_name', 'group__public_name',
    ]
    # search_fields = [
    #     'user_code', 'name', 'short_name'
    # ]
    # has_feature_is_deleted = True
