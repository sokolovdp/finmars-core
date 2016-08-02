from __future__ import unicode_literals

from rest_framework.filters import FilterSet

from poms.common.filters import CharFilter
from poms.obj_perms.views import AbstractWithObjectPermissionViewSet
from poms.tags.models import Tag
from poms.tags.serializers import TagSerializer
from poms.users.filters import OwnerByMasterUserFilter


class TagFilterSet(FilterSet):
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()

    class Meta:
        model = Tag
        fields = ['user_code', 'name', 'short_name']


class TagViewSet(AbstractWithObjectPermissionViewSet):
    queryset = Tag.objects.prefetch_related(
        'content_types',
        'account_types',
        # 'account_types__user_object_permissions', 'account_types__user_object_permissions__permission',
        # 'account_types__group_object_permissions', 'account_types__group_object_permissions__permission',
        'accounts',
        # 'accounts__user_object_permissions', 'accounts__user_object_permissions__permission',
        # 'accounts__group_object_permissions', 'accounts__group_object_permissions__permission',
        'currencies',
        # 'currencies__user_object_permissions', 'currencies__user_object_permissions__permission',
        # 'currencies__group_object_permissions', 'currencies__group_object_permissions__permission',
        'instrument_types',
        # 'instrument_types__user_object_permissions', 'instrument_types__user_object_permissions__permission',
        # 'instrument_types__group_object_permissions', 'instrument_types__group_object_permissions__permission',
        'instruments',
        # 'instruments__user_object_permissions', 'instruments__user_object_permissions__permission',
        # 'instruments__group_object_permissions', 'instruments__group_object_permissions__permission',
        'counterparties',
        # 'counterparties__user_object_permissions', 'counterparties__user_object_permissions__permission',
        # 'counterparties__group_object_permissions', 'counterparties__group_object_permissions__permission',
        'responsibles',
        # 'responsibles__user_object_permissions', 'responsibles__user_object_permissions__permission',
        # 'responsibles__group_object_permissions', 'responsibles__group_object_permissions__permission',
        'strategies1',
        # 'strategies1__user_object_permissions', 'strategies1__user_object_permissions__permission',
        # 'strategies1__group_object_permissions', 'strategies1__group_object_permissions__permission',
        'strategies2',
        # 'strategies2__user_object_permissions', 'strategies2__user_object_permissions__permission',
        # 'strategies2__group_object_permissions', 'strategies2__group_object_permissions__permission',
        'strategies3',
        # 'strategies3__user_object_permissions', 'strategies3__user_object_permissions__permission',
        # 'strategies3__group_object_permissions', 'strategies3__group_object_permissions__permission',
        'portfolios',
        # 'portfolios__user_object_permissions', 'portfolios__user_object_permissions__permission',
        # 'portfolios__group_object_permissions', 'portfolios__group_object_permissions__permission',
        'transaction_types',
        # 'transaction_types__user_object_permissions', 'transaction_types__user_object_permissions__permission',
        # 'transaction_types__group_object_permissions', 'transaction_types__group_object_permissions__permission',
    )
    prefetch_permissions_for = (
        'account_types', 'accounts', 'currencies', 'instrument_types', 'instruments', 'counterparties', 'responsibles',
        'strategies1', 'strategies2', 'strategies3', 'portfolios', 'transaction_types',
    )
    serializer_class = TagSerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]
    filter_class = TagFilterSet
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']
