from __future__ import unicode_literals

import django_filters
from rest_framework.filters import FilterSet

from poms.accounts.models import Account, AccountType, AccountAttributeType, AccountClassifier
from poms.accounts.serializers import AccountSerializer, AccountTypeSerializer, AccountAttributeTypeSerializer, \
    AccountClassifierNodeSerializer
from poms.common.filters import CharFilter, ModelWithPermissionMultipleChoiceFilter, NoOpFilter
from poms.obj_attrs.filters import AttributeTypeValueTypeFilter
from poms.obj_attrs.views import AbstractAttributeTypeViewSet, AbstractClassifierViewSet
from poms.obj_perms.filters import ObjectPermissionMemberFilter, ObjectPermissionGroupFilter, \
    ObjectPermissionPermissionFilter
from poms.obj_perms.views import AbstractWithObjectPermissionViewSet
from poms.portfolios.models import Portfolio
from poms.tags.filters import TagFilterBackend, TagFilter
from poms.users.filters import OwnerByMasterUserFilter


class AccountTypeFilterSet(FilterSet):
    id = NoOpFilter()
    is_deleted = django_filters.BooleanFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    tag = TagFilter(model=AccountType)
    member = ObjectPermissionMemberFilter(object_permission_model=AccountType)
    member_group = ObjectPermissionGroupFilter(object_permission_model=AccountType)
    permission = ObjectPermissionPermissionFilter(object_permission_model=AccountType)

    class Meta:
        model = AccountType
        fields = []


class AccountTypeViewSet(AbstractWithObjectPermissionViewSet):
    queryset = AccountType.objects.prefetch_related('master_user')
    serializer_class = AccountTypeSerializer
    # bulk_objects_permissions_serializer_class = AccountTypeBulkObjectPermissionSerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        TagFilterBackend,
    ]
    filter_class = AccountTypeFilterSet
    ordering_fields = [
        'user_code', 'name', 'short_name',
    ]
    search_fields = [
        'user_code', 'name', 'short_name',
    ]
    # has_feature_is_deleted = True


class AccountAttributeTypeFilterSet(FilterSet):
    id = NoOpFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    value_type = AttributeTypeValueTypeFilter()
    member = ObjectPermissionMemberFilter(object_permission_model=AccountAttributeType)
    member_group = ObjectPermissionGroupFilter(object_permission_model=AccountAttributeType)
    permission = ObjectPermissionPermissionFilter(object_permission_model=AccountAttributeType)

    class Meta:
        model = AccountAttributeType
        fields = []


class AccountAttributeTypeViewSet(AbstractAttributeTypeViewSet):
    queryset = AccountAttributeType.objects.prefetch_related('classifiers')
    serializer_class = AccountAttributeTypeSerializer
    # bulk_objects_permissions_serializer_class = AccountAttributeTypeBulkObjectPermissionSerializer
    filter_class = AccountAttributeTypeFilterSet


class AccountClassifierFilterSet(FilterSet):
    id = NoOpFilter()
    name = CharFilter()
    level = django_filters.NumberFilter()
    attribute_type = ModelWithPermissionMultipleChoiceFilter(model=AccountAttributeType)

    class Meta:
        model = AccountClassifier
        fields = []


class AccountClassifierViewSet(AbstractClassifierViewSet):
    queryset = AccountClassifier.objects
    serializer_class = AccountClassifierNodeSerializer
    filter_class = AccountClassifierFilterSet


class AccountFilterSet(FilterSet):
    id = NoOpFilter()
    is_deleted = django_filters.BooleanFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    portfolio = ModelWithPermissionMultipleChoiceFilter(model=Portfolio, name='portfolios')
    type = ModelWithPermissionMultipleChoiceFilter(model=AccountType)
    tag = TagFilter(model=Account)
    member = ObjectPermissionMemberFilter(object_permission_model=Account)
    member_group = ObjectPermissionGroupFilter(object_permission_model=Account)
    permission = ObjectPermissionPermissionFilter(object_permission_model=Account)

    class Meta:
        model = Account
        fields = [
            'is_deleted', 'user_code', 'name', 'short_name', 'is_valid_for_all_portfolios', 'type',
            'portfolio', 'tag', 'member', 'member_group', 'permission',
        ]


class AccountViewSet(AbstractWithObjectPermissionViewSet):
    queryset = Account.objects.prefetch_related(
        'master_user', 'type', 'portfolios', 'attributes', 'attributes__attribute_type'
    )
    prefetch_permissions_for = ('type', 'portfolios', 'attributes__attribute_type')
    serializer_class = AccountSerializer
    # bulk_objects_permissions_serializer_class = AccountBulkObjectPermissionSerializer
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
    # has_feature_is_deleted = True
