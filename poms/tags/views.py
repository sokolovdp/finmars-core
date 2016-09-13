from __future__ import unicode_literals

from rest_framework.filters import FilterSet

from poms.common.filters import CharFilter
from poms.obj_perms.filters import ObjectPermissionMemberFilter, ObjectPermissionGroupFilter, \
    ObjectPermissionPermissionFilter
from poms.obj_perms.views import AbstractWithObjectPermissionViewSet
from poms.tags.filters import TagContentTypeFilter
from poms.tags.models import Tag
from poms.tags.serializers import TagSerializer, TagBulkObjectPermissionSerializer
from poms.users.filters import OwnerByMasterUserFilter


class TagFilterSet(FilterSet):
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    content_type = TagContentTypeFilter(name='content_types')
    member = ObjectPermissionMemberFilter(object_permission_model=Tag)
    member_group = ObjectPermissionGroupFilter(object_permission_model=Tag)
    permission = ObjectPermissionPermissionFilter(object_permission_model=Tag)

    class Meta:
        model = Tag
        fields = [
            'user_code', 'name', 'short_name', 'content_type', 'member', 'member_group', 'permission',
        ]


class TagViewSet(AbstractWithObjectPermissionViewSet):
    queryset = Tag.objects.prefetch_related(
        'content_types', 'account_types', 'accounts', 'currencies', 'instrument_types', 'instruments', 'counterparties',
        'responsibles',
        'strategy1_groups', 'strategy1_subgroups', 'strategies1',
        'strategy2_groups', 'strategy2_subgroups', 'strategies2',
        'strategy3_groups', 'strategy3_subgroups', 'strategies3',
        'portfolios', 'transaction_types',
    )
    prefetch_permissions_for = (
        'account_types', 'accounts', 'currencies', 'instrument_types', 'instruments', 'counterparties', 'responsibles',
        'strategy1_groups', 'strategy1_subgroups', 'strategies1',
        'strategy2_groups', 'strategy2_subgroups', 'strategies2',
        'strategy3_groups', 'strategy3_subgroups', 'strategies3',
        'portfolios', 'transaction_types',
    )
    serializer_class = TagSerializer
    bulk_objects_permissions_serializer_class = TagBulkObjectPermissionSerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]
    filter_class = TagFilterSet
    ordering_fields = [
        'user_code', 'name', 'short_name'
    ]
    search_fields = [
        'user_code', 'name', 'short_name'
    ]
