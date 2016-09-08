from __future__ import unicode_literals

from rest_framework.filters import FilterSet

from poms.common.filters import CharFilter, ModelWithPermissionMultipleChoiceFilter
from poms.obj_perms.views import AbstractWithObjectPermissionViewSet
from poms.strategies.models import Strategy1Group, Strategy1Subgroup, Strategy1, Strategy2Group, Strategy2Subgroup, \
    Strategy2, Strategy3Group, Strategy3Subgroup, Strategy3
from poms.strategies.serializers import Strategy1GroupSerializer, Strategy1Serializer, Strategy2GroupSerializer, \
    Strategy2SubgroupSerializer, Strategy2Serializer, Strategy1SubgroupSerializer, Strategy3GroupSerializer, \
    Strategy3SubgroupSerializer, Strategy3Serializer
from poms.tags.filters import TagFilterBackend, TagFilter
from poms.users.filters import OwnerByMasterUserFilter


class Strategy1GroupFilterSet(FilterSet):
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    tag = TagFilter(model=Strategy1Group)

    class Meta:
        model = Strategy1Group
        fields = ['user_code', 'name', 'short_name', 'tag']


class Strategy1GroupViewSet(AbstractWithObjectPermissionViewSet):
    queryset = Strategy1Group.objects.select_related('master_user')
    serializer_class = Strategy1GroupSerializer
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


class Strategy1SubgroupFilterSet(FilterSet):
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    group = ModelWithPermissionMultipleChoiceFilter(model=Strategy1Group)
    tag = TagFilter(model=Strategy1Subgroup)

    class Meta:
        model = Strategy1Subgroup
        fields = ['user_code', 'name', 'short_name', 'group', 'tag']


class Strategy1SubgroupViewSet(AbstractWithObjectPermissionViewSet):
    queryset = Strategy1Subgroup.objects.select_related('master_user', 'group')
    prefetch_permissions_for = ['group']
    serializer_class = Strategy1SubgroupSerializer
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


class Strategy1FilterSet(FilterSet):
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    subgroup__group = ModelWithPermissionMultipleChoiceFilter(model=Strategy1Group)
    subgroup = ModelWithPermissionMultipleChoiceFilter(model=Strategy1Subgroup)
    tag = TagFilter(model=Strategy1)

    class Meta:
        model = Strategy1
        fields = ['user_code', 'name', 'short_name', 'subgroup__group', 'subgroup', 'tag']


class Strategy1ViewSet(AbstractWithObjectPermissionViewSet):
    queryset = Strategy1.objects.select_related('master_user', 'subgroup', 'subgroup__group')
    prefetch_permissions_for = ['subgroup', 'subgroup__group']
    serializer_class = Strategy1Serializer
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


# 2


class Strategy2GroupFilterSet(Strategy1GroupFilterSet):
    tag = TagFilter(model=Strategy2Group)

    class Meta(Strategy1GroupFilterSet.Meta):
        model = Strategy2Group
        fields = ['user_code', 'name', 'short_name', 'tag']


class Strategy2GroupViewSet(Strategy1GroupViewSet):
    queryset = Strategy2Group.objects.select_related('master_user')
    serializer_class = Strategy2GroupSerializer
    filter_class = Strategy2GroupFilterSet


class Strategy2SubgroupFilterSet(Strategy1SubgroupFilterSet):
    tag = TagFilter(model=Strategy2Subgroup)
    group = ModelWithPermissionMultipleChoiceFilter(model=Strategy2Group)

    class Meta(Strategy1SubgroupFilterSet.Meta):
        model = Strategy2Subgroup


class Strategy2SubgroupViewSet(Strategy1SubgroupViewSet):
    queryset = Strategy2Subgroup.objects.select_related('master_user', 'group')
    serializer_class = Strategy2SubgroupSerializer
    filter_class = Strategy2SubgroupFilterSet


class Strategy2FilterSet(Strategy1FilterSet):
    tag = TagFilter(model=Strategy2)
    subgroup__group = ModelWithPermissionMultipleChoiceFilter(model=Strategy2Group)
    subgroup = ModelWithPermissionMultipleChoiceFilter(model=Strategy2Subgroup)

    class Meta:
        model = Strategy2


class Strategy2ViewSet(Strategy1ViewSet):
    queryset = Strategy2.objects.select_related('master_user', 'subgroup', 'subgroup__group')
    serializer_class = Strategy2Serializer
    filter_class = Strategy2FilterSet


# 3


class Strategy3GroupFilterSet(Strategy1GroupFilterSet):
    tag = TagFilter(model=Strategy3Group)

    class Meta(Strategy1GroupFilterSet.Meta):
        model = Strategy3Group
        fields = ['user_code', 'name', 'short_name', 'tag']


class Strategy3GroupViewSet(Strategy1GroupViewSet):
    queryset = Strategy3Group.objects.select_related('master_user')
    serializer_class = Strategy3GroupSerializer
    filter_class = Strategy3GroupFilterSet


class Strategy3SubgroupFilterSet(Strategy1SubgroupFilterSet):
    tag = TagFilter(model=Strategy3Subgroup)
    group = ModelWithPermissionMultipleChoiceFilter(model=Strategy3Group)

    class Meta(Strategy1SubgroupFilterSet.Meta):
        model = Strategy3Subgroup


class Strategy3SubgroupViewSet(Strategy1SubgroupViewSet):
    queryset = Strategy3Subgroup.objects.select_related('master_user', 'group')
    serializer_class = Strategy3SubgroupSerializer
    filter_class = Strategy3SubgroupFilterSet


class Strategy3FilterSet(Strategy1FilterSet):
    tag = TagFilter(model=Strategy3)
    subgroup__group = ModelWithPermissionMultipleChoiceFilter(model=Strategy3Group)
    subgroup = ModelWithPermissionMultipleChoiceFilter(model=Strategy3Subgroup)

    class Meta:
        model = Strategy3


class Strategy3ViewSet(Strategy1ViewSet):
    queryset = Strategy3.objects.select_related('master_user', 'subgroup', 'subgroup__group')
    serializer_class = Strategy3Serializer
    filter_class = Strategy3FilterSet
