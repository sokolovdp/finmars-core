from __future__ import unicode_literals

from rest_framework.filters import FilterSet

from poms.accounts.models import Account, AccountType, AccountAttributeType, AccountClassifier
from poms.accounts.serializers import AccountSerializer, AccountTypeSerializer, AccountAttributeTypeSerializer, \
    AccountClassifierNodeSerializer
from poms.common.filters import CharFilter, ModelWithPermissionMultipleChoiceFilter, IsDefaultFilter, \
    ModelMultipleChoiceFilter
from poms.obj_attrs.views import AbstractAttributeTypeViewSet, AbstractClassifierViewSet
from poms.obj_perms.views import AbstractWithObjectPermissionViewSet
from poms.portfolios.models import Portfolio
from poms.tags.filters import TagFilterBackend, TagFilter
from poms.users.filters import OwnerByMasterUserFilter
from poms.users.models import Member, Group


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
    queryset = AccountType.objects.prefetch_related('master_user')
    serializer_class = AccountTypeSerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        TagFilterBackend,
    ]
    filter_class = AccountTypeFilterSet
    ordering_fields = [
        'user_code', 'name', 'short_name',
        'tags__user_code',
    ]
    search_fields = [
        'user_code', 'name', 'short_name',
    ]


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


class AccountClassifierFilterSet(FilterSet):
    name = CharFilter()
    attribute_type = ModelWithPermissionMultipleChoiceFilter(model=AccountAttributeType)

    # parent = ModelWithPermissionMultipleChoiceFilter(model=AccountClassifier, master_user_path='attribute_type__master_user')

    class Meta:
        model = AccountClassifier
        fields = ['name', 'level', 'attribute_type', ]


class AccountClassifierViewSet(AbstractClassifierViewSet):
    queryset = AccountClassifier.objects
    serializer_class = AccountClassifierNodeSerializer
    filter_class = AccountClassifierFilterSet


class AccountFilterSet(FilterSet):
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    is_default = IsDefaultFilter(source='account')
    portfolio = ModelWithPermissionMultipleChoiceFilter(model=Portfolio, name='portfolios')
    type = ModelWithPermissionMultipleChoiceFilter(model=AccountType)
    tag = TagFilter(model=Account)
    user_object_permissions__member = ModelMultipleChoiceFilter(model=Member, field_name='username')
    group_object_permissions__group = ModelMultipleChoiceFilter(model=Group, field_name='name')

    class Meta:
        model = Account
        fields = ['user_code', 'name', 'short_name', 'is_valid_for_all_portfolios', 'is_default', 'type', 'portfolio',
                  'tag', 'user_object_permissions__member', 'group_object_permissions__group', ]


class AccountViewSet(AbstractWithObjectPermissionViewSet):
    queryset = Account.objects.prefetch_related(
        'master_user', 'type', 'portfolios', 'attributes', 'attributes__attribute_type'
    )
    prefetch_permissions_for = ('type', 'portfolios', 'attributes__attribute_type')
    serializer_class = AccountSerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        TagFilterBackend,
    ]
    filter_class = AccountFilterSet
    ordering_fields = [
        'user_code', 'name', 'short_name', 'is_valid_for_all_portfolios',
        'type__user_code', 'type__name', 'type__short_name',
    ]
    search_fields = [
        'user_code', 'name', 'short_name',
    ]
