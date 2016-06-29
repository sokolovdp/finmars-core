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
    queryset = Tag.objects.prefetch_related('content_types', 'account_types', 'accounts', 'currencies',
                                            'instrument_types', 'instruments', 'counterparties', 'responsibles',
                                            'strategies1', 'strategies2', 'strategies3', 'portfolios',
                                            'transaction_types')
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
