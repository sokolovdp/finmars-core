from __future__ import unicode_literals

from rest_framework.filters import FilterSet

from poms.accounts.models import Account, AccountType, AccountAttributeType
from poms.accounts.serializers import AccountSerializer, AccountTypeSerializer, AccountAttributeTypeSerializer
from poms.common.filters import CharFilter, ModelWithPermissionMultipleChoiceFilter, IsDefaultFilter
from poms.obj_attrs.filters import AttributePrefetchFilter
from poms.obj_attrs.views import AbstractAttributeTypeViewSet
from poms.obj_perms.views import AbstractWithObjectPermissionViewSet
from poms.portfolios.models import Portfolio
from poms.tags.filters import TagFilterBackend, TagFilter
from poms.users.filters import OwnerByMasterUserFilter


class AccountTypeFilterSet(FilterSet):
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    is_default = IsDefaultFilter(source='account_type')
    tag = TagFilter(model=AccountType)

    class Meta:
        model = AccountType
        fields = ['user_code', 'name', 'short_name', 'is_default', 'tags']


class AccountTypeViewSet(AbstractWithObjectPermissionViewSet):
    queryset = AccountType.objects
    serializer_class = AccountTypeSerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        TagFilterBackend,
    ]
    filter_class = AccountTypeFilterSet
    ordering_fields = ['user_code', 'name', 'short_name', ]
    search_fields = ['user_code', 'name', 'short_name', ]


class AccountAttributeTypeFilterSet(FilterSet):
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()

    class Meta:
        model = AccountAttributeType
        fields = ['user_code', 'name', 'short_name']


class AccountAttributeTypeViewSet(AbstractAttributeTypeViewSet):
    queryset = AccountAttributeType.objects.prefetch_related('classifiers')
    serializer_class = AccountAttributeTypeSerializer
    filter_class = AccountAttributeTypeFilterSet


class AccountFilterSet(FilterSet):
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    is_default = IsDefaultFilter(source='account')
    portfolio = ModelWithPermissionMultipleChoiceFilter(model=Portfolio, name='portfolios')
    type = ModelWithPermissionMultipleChoiceFilter(model=AccountType)
    tag = TagFilter(model=Account)

    class Meta:
        model = Account
        fields = ['user_code', 'name', 'short_name', 'is_default', 'type', 'portfolio', 'tag']


class AccountViewSet(AbstractWithObjectPermissionViewSet):
    queryset = Account.objects.prefetch_related(
        'type',
        # 'type__user_object_permissions', 'type__user_object_permissions__permission',
        # 'type__group_object_permissions', 'type__group_object_permissions__permission',
        'portfolios',
        # 'portfolios__user_object_permissions', 'portfolios__user_object_permissions__permission',
        # 'portfolios__group_object_permissions', 'portfolios__group_object_permissions__permission',
    )
    prefetch_permissions_for = ('type', 'portfolios',)
    serializer_class = AccountSerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        TagFilterBackend,
        AttributePrefetchFilter,
    ]
    filter_class = AccountFilterSet
    ordering_fields = [
        'user_code', 'name', 'short_name',
        'type__user_code', 'type__name', 'type__short_name',
    ]
    search_fields = [
        'user_code', 'name', 'short_name',
        'type__user_code', 'type__name', 'type__short_name',
    ]
