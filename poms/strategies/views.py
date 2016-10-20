from __future__ import unicode_literals

import django_filters
from rest_framework.filters import FilterSet

from poms.common.filters import CharFilter, ModelExtWithPermissionMultipleChoiceFilter, NoOpFilter
from poms.obj_perms.filters import ObjectPermissionMemberFilter, ObjectPermissionGroupFilter, \
    ObjectPermissionPermissionFilter
from poms.obj_perms.utils import get_permissions_prefetch_lookups
from poms.obj_perms.views import AbstractWithObjectPermissionViewSet
from poms.strategies.models import Strategy1Group, Strategy1Subgroup, Strategy1, Strategy2Group, Strategy2Subgroup, \
    Strategy2, Strategy3Group, Strategy3Subgroup, Strategy3
from poms.strategies.serializers import Strategy1GroupSerializer, Strategy1Serializer, Strategy2GroupSerializer, \
    Strategy2SubgroupSerializer, Strategy2Serializer, Strategy1SubgroupSerializer, Strategy3GroupSerializer, \
    Strategy3SubgroupSerializer, Strategy3Serializer
from poms.tags.filters import TagFilter
from poms.tags.models import Tag
from poms.tags.utils import get_tag_prefetch
from poms.users.filters import OwnerByMasterUserFilter


class Strategy1GroupFilterSet(FilterSet):
    id = NoOpFilter()
    is_deleted = django_filters.BooleanFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    public_name = CharFilter()
    tag = TagFilter(model=Strategy1Group)
    member = ObjectPermissionMemberFilter(object_permission_model=Strategy1Group)
    member_group = ObjectPermissionGroupFilter(object_permission_model=Strategy1Group)
    permission = ObjectPermissionPermissionFilter(object_permission_model=Strategy1Group)

    class Meta:
        model = Strategy1Group
        fields = []


class Strategy1GroupViewSet(AbstractWithObjectPermissionViewSet):
    queryset = Strategy1Group.objects.select_related(
        'master_user'
    ).prefetch_related(
        get_tag_prefetch(),
        *get_permissions_prefetch_lookups(
            (None, Strategy1Group),
        )
    )
    serializer_class = Strategy1GroupSerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]
    filter_class = Strategy1GroupFilterSet
    ordering_fields = [
        'user_code', 'name', 'short_name', 'public_name',
    ]


class Strategy1SubgroupFilterSet(FilterSet):
    id = NoOpFilter()
    is_deleted = django_filters.BooleanFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    public_name = CharFilter()
    group = ModelExtWithPermissionMultipleChoiceFilter(model=Strategy1Group)
    tag = TagFilter(model=Strategy1Subgroup)
    member = ObjectPermissionMemberFilter(object_permission_model=Strategy1Subgroup)
    member_group = ObjectPermissionGroupFilter(object_permission_model=Strategy1Subgroup)
    permission = ObjectPermissionPermissionFilter(object_permission_model=Strategy1Subgroup)

    class Meta:
        model = Strategy1Subgroup
        fields = []


class Strategy1SubgroupViewSet(AbstractWithObjectPermissionViewSet):
    queryset = Strategy1Subgroup.objects.select_related(
        'master_user', 'group'
    ).prefetch_related(
        get_tag_prefetch(),
        *get_permissions_prefetch_lookups(
            (None, Strategy1Subgroup),
            ('group', Strategy1Group),
        )
    )
    # prefetch_permissions_for = [
    #     'group'
    # ]
    serializer_class = Strategy1SubgroupSerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]
    filter_class = Strategy1SubgroupFilterSet
    ordering_fields = [
        'user_code', 'name', 'short_name', 'public_name',
        'group', 'group__user_code', 'group__name', 'group__short_name', 'group__public_name',
    ]


class Strategy1FilterSet(FilterSet):
    id = NoOpFilter()
    is_deleted = django_filters.BooleanFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    public_name = CharFilter()
    subgroup__group = ModelExtWithPermissionMultipleChoiceFilter(model=Strategy1Group)
    subgroup = ModelExtWithPermissionMultipleChoiceFilter(model=Strategy1Subgroup)
    tag = TagFilter(model=Strategy1)
    member = ObjectPermissionMemberFilter(object_permission_model=Strategy1)
    member_group = ObjectPermissionGroupFilter(object_permission_model=Strategy1)
    permission = ObjectPermissionPermissionFilter(object_permission_model=Strategy1)

    class Meta:
        model = Strategy1
        fields = []


class Strategy1ViewSet(AbstractWithObjectPermissionViewSet):
    queryset = Strategy1.objects.select_related(
        'master_user', 'subgroup', 'subgroup__group'
    ).prefetch_related(
        get_tag_prefetch(),
        *get_permissions_prefetch_lookups(
            (None, Strategy1),
            ('subgroup', Strategy1Subgroup),
            ('subgroup__group', Strategy1Group),
        )
    )
    # prefetch_permissions_for = [
    #     'subgroup', 'subgroup__group'
    # ]
    serializer_class = Strategy1Serializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]
    filter_class = Strategy1FilterSet
    ordering_fields = [
        'user_code', 'name', 'short_name', 'public_name',
        'subgroup__group', 'subgroup__group__user_code', 'subgroup__group__name', 'subgroup__group__short_name',
        'subgroup__group__public_name',
        'subgroup', 'subgroup__user_code', 'subgroup__name', 'subgroup__short_name', 'subgroup__public_name',
    ]


# 2


class Strategy2GroupFilterSet(Strategy1GroupFilterSet):
    tag = TagFilter(model=Strategy2Group)
    member = ObjectPermissionMemberFilter(object_permission_model=Strategy2Group)
    member_group = ObjectPermissionGroupFilter(object_permission_model=Strategy2Group)
    permission = ObjectPermissionPermissionFilter(object_permission_model=Strategy2Group)

    class Meta(Strategy1GroupFilterSet.Meta):
        model = Strategy2Group


class Strategy2GroupViewSet(Strategy1GroupViewSet):
    queryset = Strategy2Group.objects.select_related(
        'master_user'
    ).prefetch_related(
        get_tag_prefetch(),
        *get_permissions_prefetch_lookups(
            (None, Strategy2Group),
        )
    )
    serializer_class = Strategy2GroupSerializer
    filter_class = Strategy2GroupFilterSet


class Strategy2SubgroupFilterSet(Strategy1SubgroupFilterSet):
    tag = TagFilter(model=Strategy2Subgroup)
    group = ModelExtWithPermissionMultipleChoiceFilter(model=Strategy2Group)
    member = ObjectPermissionMemberFilter(object_permission_model=Strategy2Subgroup)
    member_group = ObjectPermissionGroupFilter(object_permission_model=Strategy2Subgroup)
    permission = ObjectPermissionPermissionFilter(object_permission_model=Strategy2Subgroup)

    class Meta(Strategy1SubgroupFilterSet.Meta):
        model = Strategy2Subgroup


class Strategy2SubgroupViewSet(Strategy1SubgroupViewSet):
    queryset = Strategy2Subgroup.objects.select_related('master_user', 'group').prefetch_related(
        get_tag_prefetch(),
        *get_permissions_prefetch_lookups(
            (None, Strategy2Subgroup),
            ('group', Strategy2Group),
        )
    )
    serializer_class = Strategy2SubgroupSerializer
    filter_class = Strategy2SubgroupFilterSet


class Strategy2FilterSet(Strategy1FilterSet):
    tag = TagFilter(model=Strategy2)
    subgroup__group = ModelExtWithPermissionMultipleChoiceFilter(model=Strategy2Group)
    subgroup = ModelExtWithPermissionMultipleChoiceFilter(model=Strategy2Subgroup)
    member = ObjectPermissionMemberFilter(object_permission_model=Strategy2)
    member_group = ObjectPermissionGroupFilter(object_permission_model=Strategy2)
    permission = ObjectPermissionPermissionFilter(object_permission_model=Strategy2)

    class Meta:
        model = Strategy2


class Strategy2ViewSet(Strategy1ViewSet):
    queryset = Strategy2.objects.select_related(
        'master_user', 'subgroup', 'subgroup__group'
    ).prefetch_related(
        get_tag_prefetch(),
        *get_permissions_prefetch_lookups(
            (None, Strategy2),
            ('subgroup', Strategy2Subgroup),
            ('subgroup__group', Strategy2Group),
        )
    )
    serializer_class = Strategy2Serializer
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
    queryset = Strategy3Group.objects.prefetch_related('master_user').prefetch_related(
        get_tag_prefetch(),
        *get_permissions_prefetch_lookups(
            (None, Strategy3Group),
        )
    )
    serializer_class = Strategy3GroupSerializer
    filter_class = Strategy3GroupFilterSet


class Strategy3SubgroupFilterSet(Strategy1SubgroupFilterSet):
    tag = TagFilter(model=Strategy3Subgroup)
    group = ModelExtWithPermissionMultipleChoiceFilter(model=Strategy3Group)
    member = ObjectPermissionMemberFilter(object_permission_model=Strategy3Subgroup)
    member_group = ObjectPermissionGroupFilter(object_permission_model=Strategy3Subgroup)
    permission = ObjectPermissionPermissionFilter(object_permission_model=Strategy3Subgroup)

    class Meta(Strategy1SubgroupFilterSet.Meta):
        model = Strategy3Subgroup


class Strategy3SubgroupViewSet(Strategy1SubgroupViewSet):
    queryset = Strategy3Subgroup.objects.select_related(
        'master_user', 'group'
    ).prefetch_related(
        get_tag_prefetch(),
        *get_permissions_prefetch_lookups(
            (None, Strategy3Subgroup),
            ('group', Strategy3Group),
        )
    )
    serializer_class = Strategy3SubgroupSerializer
    filter_class = Strategy3SubgroupFilterSet


class Strategy3FilterSet(Strategy1FilterSet):
    tag = TagFilter(model=Strategy3)
    subgroup__group = ModelExtWithPermissionMultipleChoiceFilter(model=Strategy3Group)
    subgroup = ModelExtWithPermissionMultipleChoiceFilter(model=Strategy3Subgroup)
    member = ObjectPermissionMemberFilter(object_permission_model=Strategy3)
    member_group = ObjectPermissionGroupFilter(object_permission_model=Strategy3)
    permission = ObjectPermissionPermissionFilter(object_permission_model=Strategy3)

    class Meta:
        model = Strategy3


class Strategy3ViewSet(Strategy1ViewSet):
    queryset = Strategy3.objects.select_related(
        'master_user', 'subgroup', 'subgroup__group'
    ).prefetch_related(
        get_tag_prefetch(),
        *get_permissions_prefetch_lookups(
            (None, Strategy3),
            ('subgroup', Strategy3Subgroup),
            ('subgroup__group', Strategy3Group),
        )
    )
    serializer_class = Strategy3Serializer
    filter_class = Strategy3FilterSet
