from __future__ import unicode_literals

import django_filters
from rest_framework.filters import FilterSet

from poms.common.filters import CharFilter, ModelWithPermissionMultipleChoiceFilter, NoOpFilter
from poms.obj_perms.filters import ObjectPermissionMemberFilter, ObjectPermissionGroupFilter, \
    ObjectPermissionPermissionFilter
from poms.obj_perms.views import AbstractWithObjectPermissionViewSet
from poms.strategies.models import Strategy1Group, Strategy1Subgroup, Strategy1, Strategy2Group, Strategy2Subgroup, \
    Strategy2, Strategy3Group, Strategy3Subgroup, Strategy3
from poms.strategies.serializers import Strategy1GroupSerializer, Strategy1Serializer, Strategy2GroupSerializer, \
    Strategy2SubgroupSerializer, Strategy2Serializer, Strategy1SubgroupSerializer, Strategy3GroupSerializer, \
    Strategy3SubgroupSerializer, Strategy3Serializer, Strategy1GroupBulkObjectPermissionSerializer, \
    Strategy1SubgroupBulkObjectPermissionSerializer, Strategy1BulkObjectPermissionSerializer, \
    Strategy2GroupBulkObjectPermissionSerializer, Strategy2SubgroupBulkObjectPermissionSerializer, \
    Strategy2BulkObjectPermissionSerializer, Strategy3GroupBulkObjectPermissionSerializer, \
    Strategy3SubgroupBulkObjectPermissionSerializer, Strategy3BulkObjectPermissionSerializer
from poms.tags.filters import TagFilterBackend, TagFilter
from poms.users.filters import OwnerByMasterUserFilter


class Strategy1GroupFilterSet(FilterSet):
    id = NoOpFilter()
    is_deleted = django_filters.BooleanFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    tag = TagFilter(model=Strategy1Group)
    member = ObjectPermissionMemberFilter(object_permission_model=Strategy1Group)
    member_group = ObjectPermissionGroupFilter(object_permission_model=Strategy1Group)
    permission = ObjectPermissionPermissionFilter(object_permission_model=Strategy1Group)

    class Meta:
        model = Strategy1Group
        fields = []


class Strategy1GroupViewSet(AbstractWithObjectPermissionViewSet):
    queryset = Strategy1Group.objects.prefetch_related('master_user')
    serializer_class = Strategy1GroupSerializer
    bulk_objects_permissions_serializer_class = Strategy1GroupBulkObjectPermissionSerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        TagFilterBackend,
    ]
    filter_class = Strategy1GroupFilterSet
    ordering_fields = [
        'user_code', 'name', 'short_name'
    ]
    search_fields = [
        'user_code', 'name', 'short_name',
    ]
    has_feature_is_deleted = True


class Strategy1SubgroupFilterSet(FilterSet):
    id = NoOpFilter()
    is_deleted = django_filters.BooleanFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    group = ModelWithPermissionMultipleChoiceFilter(model=Strategy1Group)
    tag = TagFilter(model=Strategy1Subgroup)
    member = ObjectPermissionMemberFilter(object_permission_model=Strategy1Subgroup)
    member_group = ObjectPermissionGroupFilter(object_permission_model=Strategy1Subgroup)
    permission = ObjectPermissionPermissionFilter(object_permission_model=Strategy1Subgroup)

    class Meta:
        model = Strategy1Subgroup
        fields = []


class Strategy1SubgroupViewSet(AbstractWithObjectPermissionViewSet):
    queryset = Strategy1Subgroup.objects.prefetch_related('master_user', 'group')
    prefetch_permissions_for = ['group']
    serializer_class = Strategy1SubgroupSerializer
    bulk_objects_permissions_serializer_class = Strategy1SubgroupBulkObjectPermissionSerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        TagFilterBackend,
    ]
    filter_class = Strategy1SubgroupFilterSet
    ordering_fields = [
        'user_code', 'name', 'short_name',
        'group__user_code', 'group__name', 'group__short_name',
    ]
    search_fields = [
        'user_code', 'name', 'short_name',
    ]
    has_feature_is_deleted = True


class Strategy1FilterSet(FilterSet):
    id = NoOpFilter()
    is_deleted = django_filters.BooleanFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    subgroup__group = ModelWithPermissionMultipleChoiceFilter(model=Strategy1Group)
    subgroup = ModelWithPermissionMultipleChoiceFilter(model=Strategy1Subgroup)
    tag = TagFilter(model=Strategy1)
    member = ObjectPermissionMemberFilter(object_permission_model=Strategy1)
    member_group = ObjectPermissionGroupFilter(object_permission_model=Strategy1)
    permission = ObjectPermissionPermissionFilter(object_permission_model=Strategy1)

    class Meta:
        model = Strategy1
        fields = []


class Strategy1ViewSet(AbstractWithObjectPermissionViewSet):
    queryset = Strategy1.objects.prefetch_related('master_user', 'subgroup', 'subgroup__group')
    prefetch_permissions_for = ['subgroup', 'subgroup__group']
    serializer_class = Strategy1Serializer
    bulk_objects_permissions_serializer_class = Strategy1BulkObjectPermissionSerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        TagFilterBackend,
    ]
    filter_class = Strategy1FilterSet
    ordering_fields = [
        'user_code', 'name', 'short_name',
        'subgroup__user_code', 'subgroup__name', 'subgroup__short_name',
        'subgroup__group__user_code', 'subgroup__group__name', 'subgroup__group__short_name',
    ]
    search_fields = [
        'user_code', 'name', 'short_name',
    ]
    has_feature_is_deleted = True


# 2


class Strategy2GroupFilterSet(Strategy1GroupFilterSet):
    tag = TagFilter(model=Strategy2Group)
    member = ObjectPermissionMemberFilter(object_permission_model=Strategy2Group)
    member_group = ObjectPermissionGroupFilter(object_permission_model=Strategy2Group)
    permission = ObjectPermissionPermissionFilter(object_permission_model=Strategy2Group)

    class Meta(Strategy1GroupFilterSet.Meta):
        model = Strategy2Group


class Strategy2GroupViewSet(Strategy1GroupViewSet):
    queryset = Strategy2Group.objects.prefetch_related('master_user')
    serializer_class = Strategy2GroupSerializer
    bulk_objects_permissions_serializer_class = Strategy2GroupBulkObjectPermissionSerializer
    filter_class = Strategy2GroupFilterSet


class Strategy2SubgroupFilterSet(Strategy1SubgroupFilterSet):
    tag = TagFilter(model=Strategy2Subgroup)
    group = ModelWithPermissionMultipleChoiceFilter(model=Strategy2Group)
    member = ObjectPermissionMemberFilter(object_permission_model=Strategy2Subgroup)
    member_group = ObjectPermissionGroupFilter(object_permission_model=Strategy2Subgroup)
    permission = ObjectPermissionPermissionFilter(object_permission_model=Strategy2Subgroup)

    class Meta(Strategy1SubgroupFilterSet.Meta):
        model = Strategy2Subgroup


class Strategy2SubgroupViewSet(Strategy1SubgroupViewSet):
    queryset = Strategy2Subgroup.objects.prefetch_related('master_user', 'group')
    serializer_class = Strategy2SubgroupSerializer
    bulk_objects_permissions_serializer_class = Strategy2SubgroupBulkObjectPermissionSerializer
    filter_class = Strategy2SubgroupFilterSet


class Strategy2FilterSet(Strategy1FilterSet):
    tag = TagFilter(model=Strategy2)
    subgroup__group = ModelWithPermissionMultipleChoiceFilter(model=Strategy2Group)
    subgroup = ModelWithPermissionMultipleChoiceFilter(model=Strategy2Subgroup)
    member = ObjectPermissionMemberFilter(object_permission_model=Strategy2)
    member_group = ObjectPermissionGroupFilter(object_permission_model=Strategy2)
    permission = ObjectPermissionPermissionFilter(object_permission_model=Strategy2)

    class Meta:
        model = Strategy2


class Strategy2ViewSet(Strategy1ViewSet):
    queryset = Strategy2.objects.prefetch_related('master_user', 'subgroup', 'subgroup__group')
    serializer_class = Strategy2Serializer
    bulk_objects_permissions_serializer_class = Strategy2BulkObjectPermissionSerializer
    filter_class = Strategy2FilterSet


# 3


class Strategy3GroupFilterSet(Strategy1GroupFilterSet):
    tag = TagFilter(model=Strategy3Group)
    member = ObjectPermissionMemberFilter(object_permission_model=Strategy3Group)
    member_group = ObjectPermissionGroupFilter(object_permission_model=Strategy3Group)
    permission = ObjectPermissionPermissionFilter(object_permission_model=Strategy3Group)

    class Meta(Strategy1GroupFilterSet.Meta):
        model = Strategy3Group


class Strategy3GroupViewSet(Strategy1GroupViewSet):
    queryset = Strategy3Group.objects.prefetch_related('master_user')
    serializer_class = Strategy3GroupSerializer
    bulk_objects_permissions_serializer_class = Strategy3GroupBulkObjectPermissionSerializer
    filter_class = Strategy3GroupFilterSet


class Strategy3SubgroupFilterSet(Strategy1SubgroupFilterSet):
    tag = TagFilter(model=Strategy3Subgroup)
    group = ModelWithPermissionMultipleChoiceFilter(model=Strategy3Group)
    member = ObjectPermissionMemberFilter(object_permission_model=Strategy3Subgroup)
    member_group = ObjectPermissionGroupFilter(object_permission_model=Strategy3Subgroup)
    permission = ObjectPermissionPermissionFilter(object_permission_model=Strategy3Subgroup)

    class Meta(Strategy1SubgroupFilterSet.Meta):
        model = Strategy3Subgroup


class Strategy3SubgroupViewSet(Strategy1SubgroupViewSet):
    queryset = Strategy3Subgroup.objects.prefetch_related('master_user', 'group')
    serializer_class = Strategy3SubgroupSerializer
    bulk_objects_permissions_serializer_class = Strategy3SubgroupBulkObjectPermissionSerializer
    filter_class = Strategy3SubgroupFilterSet


class Strategy3FilterSet(Strategy1FilterSet):
    tag = TagFilter(model=Strategy3)
    subgroup__group = ModelWithPermissionMultipleChoiceFilter(model=Strategy3Group)
    subgroup = ModelWithPermissionMultipleChoiceFilter(model=Strategy3Subgroup)
    member = ObjectPermissionMemberFilter(object_permission_model=Strategy3)
    member_group = ObjectPermissionGroupFilter(object_permission_model=Strategy3)
    permission = ObjectPermissionPermissionFilter(object_permission_model=Strategy3)

    class Meta:
        model = Strategy3


class Strategy3ViewSet(Strategy1ViewSet):
    queryset = Strategy3.objects.prefetch_related('master_user', 'subgroup', 'subgroup__group')
    serializer_class = Strategy3Serializer
    bulk_objects_permissions_serializer_class = Strategy3BulkObjectPermissionSerializer
    filter_class = Strategy3FilterSet
