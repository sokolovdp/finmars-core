from __future__ import unicode_literals

from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter, FilterSet

from poms.common.filters import CharFilter
from poms.common.views import PomsViewSetBase
from poms.obj_perms.filters import ObjectPermissionBackend
from poms.obj_perms.permissions import ObjectPermissionBase
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


class TagViewSet(PomsViewSetBase):
    queryset = Tag.objects.prefetch_related(
        'content_types',
        'account_types',
        'account_types__user_object_permissions', 'account_types__user_object_permissions__permission',
        'account_types__group_object_permissions', 'account_types__group_object_permissions__permission',
        'accounts',
        'accounts__user_object_permissions', 'accounts__user_object_permissions__permission',
        'accounts__group_object_permissions', 'accounts__group_object_permissions__permission',
        'currencies',
        'currencies__user_object_permissions', 'currencies__user_object_permissions__permission',
        'currencies__group_object_permissions', 'currencies__group_object_permissions__permission',
        'instrument_types',
        'instrument_types__user_object_permissions', 'instrument_types__user_object_permissions__permission',
        'instrument_types__group_object_permissions', 'instrument_types__group_object_permissions__permission',
        'instruments',
        'instruments__user_object_permissions', 'instruments__user_object_permissions__permission',
        'instruments__group_object_permissions', 'instruments__group_object_permissions__permission',
        'counterparties',
        'counterparties__user_object_permissions', 'counterparties__user_object_permissions__permission',
        'counterparties__group_object_permissions', 'counterparties__group_object_permissions__permission',
        'responsibles',
        'responsibles__user_object_permissions', 'responsibles__user_object_permissions__permission',
        'responsibles__group_object_permissions', 'responsibles__group_object_permissions__permission',
        'strategies1',
        'strategies1__user_object_permissions', 'strategies1__user_object_permissions__permission',
        'strategies1__group_object_permissions', 'strategies1__group_object_permissions__permission',
        'strategies2',
        'strategies2__user_object_permissions', 'strategies2__user_object_permissions__permission',
        'strategies2__group_object_permissions', 'strategies2__group_object_permissions__permission',
        'strategies3',
        'strategies3__user_object_permissions', 'strategies3__user_object_permissions__permission',
        'strategies3__group_object_permissions', 'strategies3__group_object_permissions__permission',
        'portfolios',
        'portfolios__user_object_permissions', 'portfolios__user_object_permissions__permission',
        'portfolios__group_object_permissions', 'portfolios__group_object_permissions__permission',
        'transaction_types',
        'transaction_types__user_object_permissions', 'transaction_types__user_object_permissions__permission',
        'transaction_types__group_object_permissions', 'transaction_types__group_object_permissions__permission',
    )
    serializer_class = TagSerializer
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionBackend,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    filter_class = TagFilterSet
    permission_classes = PomsViewSetBase.permission_classes + [
        ObjectPermissionBase
    ]
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']

    def get_serializer(self, *args, **kwargs):
        kwargs['show_object_permissions'] = (self.action != 'list')
        return super(TagViewSet, self).get_serializer(*args, **kwargs)
