from __future__ import unicode_literals

from rest_framework.filters import FilterSet, DjangoFilterBackend, OrderingFilter, SearchFilter

from poms.accounts.models import Account, AccountType, AccountAttributeType
from poms.accounts.serializers import AccountSerializer, AccountTypeSerializer, AccountAttributeTypeSerializer
from poms.common.filters import OrderingWithAttributesFilter
from poms.common.views import PomsViewSetBase
from poms.obj_attrs.filters import AttributePrefetchFilter
from poms.obj_attrs.views import AttributeTypeViewSetBase
from poms.obj_perms.filters import AllFakeFilter, ObjectPermissionBackend
from poms.obj_perms.permissions import ObjectPermissionBase
from poms.tags.filters import TagFakeFilter, TagFilterBackend
from poms.users.filters import OwnerByMasterUserFilter


class AccountTypeFilterSet(FilterSet):
    all = AllFakeFilter()
    tags = TagFakeFilter()

    class Meta:
        model = AccountType
        fields = ['user_code', 'name', 'short_name', 'all', 'tags']

    @staticmethod
    def tags_filter(queryset, value):
        return queryset


class AccountTypeViewSet(PomsViewSetBase):
    queryset = AccountType.objects
    serializer_class = AccountTypeSerializer
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionBackend,
        TagFilterBackend,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    filter_class = AccountTypeFilterSet
    permission_classes = PomsViewSetBase.permission_classes + [
        ObjectPermissionBase,
    ]
    ordering_fields = ['user_code', 'name', 'short_name', ]
    search_fields = ['user_code', 'name', 'short_name', ]


class AccountAttributeTypeFilterSet(FilterSet):
    class Meta:
        model = AccountAttributeType
        fields = ['user_code', 'name', 'short_name']


class AccountAttributeTypeViewSet(AttributeTypeViewSetBase):
    queryset = AccountAttributeType.objects.prefetch_related('classifiers')
    serializer_class = AccountAttributeTypeSerializer
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionBackend,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    filter_class = AccountAttributeTypeFilterSet
    permission_classes = PomsViewSetBase.permission_classes + [
        ObjectPermissionBase,
    ]
    ordering_fields = ['user_code', 'name', 'short_name', ]
    search_fields = ['user_code', 'name', 'short_name', ]


class AccountFilterSet(FilterSet):
    all = AllFakeFilter()
    tags = TagFakeFilter()

    class Meta:
        model = Account
        fields = ['user_code', 'name', 'short_name', 'all', 'tags']


class AccountViewSet(PomsViewSetBase):
    queryset = Account.objects
    serializer_class = AccountSerializer
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionBackend,
        TagFilterBackend,
        AttributePrefetchFilter,
        DjangoFilterBackend,
        # OrderingFilter,
        OrderingWithAttributesFilter,
        SearchFilter,
    ]
    filter_class = AccountFilterSet
    permission_classes = PomsViewSetBase.permission_classes + [
        ObjectPermissionBase
    ]
    ordering_fields = ['user_code', 'name', 'short_name', ]
    search_fields = ['user_code', 'name', 'short_name', ]
