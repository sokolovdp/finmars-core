from __future__ import unicode_literals

import django_filters
from django.db.models import Prefetch
from rest_framework.filters import FilterSet

from poms.accounts.models import Account, AccountType, AccountAttributeType, AccountClassifier, AccountAttribute
from poms.accounts.serializers import AccountSerializer, AccountTypeSerializer, AccountAttributeTypeSerializer, \
    AccountClassifierNodeSerializer, AccountAttributeType2Serializer
from poms.common.filters import CharFilter, NoOpFilter, ModelExtWithPermissionMultipleChoiceFilter
from poms.obj_attrs.filters import AttributeTypeValueTypeFilter
from poms.obj_attrs.views import AbstractAttributeTypeViewSet, AbstractClassifierViewSet, GenericAttributeTypeViewSet
from poms.obj_perms.filters import ObjectPermissionMemberFilter, ObjectPermissionGroupFilter, \
    ObjectPermissionPermissionFilter
from poms.obj_perms.utils import get_permissions_prefetch_lookups
from poms.obj_perms.views import AbstractWithObjectPermissionViewSet
from poms.portfolios.models import Portfolio
from poms.tags.filters import TagFilter
from poms.tags.models import Tag
from poms.users.filters import OwnerByMasterUserFilter


class AccountTypeFilterSet(FilterSet):
    id = NoOpFilter()
    is_deleted = django_filters.BooleanFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    public_name = CharFilter()
    show_transaction_details = django_filters.BooleanFilter()
    tag = TagFilter(model=AccountType)
    member = ObjectPermissionMemberFilter(object_permission_model=AccountType)
    member_group = ObjectPermissionGroupFilter(object_permission_model=AccountType)
    permission = ObjectPermissionPermissionFilter(object_permission_model=AccountType)

    class Meta:
        model = AccountType
        fields = []


class AccountTypeViewSet(AbstractWithObjectPermissionViewSet):
    queryset = AccountType.objects.select_related('master_user').prefetch_related(
        'tags',
        *get_permissions_prefetch_lookups(
            (None, AccountType),
            ('tags', Tag)
        )
    )
    serializer_class = AccountTypeSerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        # TagFilterBackend,
    ]
    filter_class = AccountTypeFilterSet
    ordering_fields = [
        'user_code', 'name', 'short_name', 'public_name', 'show_transaction_details'
    ]


class AccountAttributeTypeFilterSet(FilterSet):
    id = NoOpFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    public_name = CharFilter()
    value_type = AttributeTypeValueTypeFilter()
    member = ObjectPermissionMemberFilter(object_permission_model=AccountAttributeType)
    member_group = ObjectPermissionGroupFilter(object_permission_model=AccountAttributeType)
    permission = ObjectPermissionPermissionFilter(object_permission_model=AccountAttributeType)

    class Meta:
        model = AccountAttributeType
        fields = []


class AccountAttributeTypeViewSet(AbstractAttributeTypeViewSet):
    queryset = AccountAttributeType.objects.select_related(
        'master_user'
    ).prefetch_related(
        'classifiers',
        *get_permissions_prefetch_lookups(
            (None, AccountAttributeType)
        )
    )
    serializer_class = AccountAttributeTypeSerializer
    # bulk_objects_permissions_serializer_class = AccountAttributeTypeBulkObjectPermissionSerializer
    filter_class = AccountAttributeTypeFilterSet


class AccountAttributeType2ViewSet(GenericAttributeTypeViewSet):
    serializer_class = AccountAttributeType2Serializer


class AccountClassifierFilterSet(FilterSet):
    id = NoOpFilter()
    name = CharFilter()
    level = django_filters.NumberFilter()
    attribute_type = ModelExtWithPermissionMultipleChoiceFilter(model=AccountAttributeType)

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
    public_name = CharFilter()
    is_valid_for_all_portfolios = django_filters.BooleanFilter()
    type = ModelExtWithPermissionMultipleChoiceFilter(model=AccountType)
    portfolio = ModelExtWithPermissionMultipleChoiceFilter(model=Portfolio, name='portfolios')
    tag = TagFilter(model=Account)
    member = ObjectPermissionMemberFilter(object_permission_model=Account)
    member_group = ObjectPermissionGroupFilter(object_permission_model=Account)
    permission = ObjectPermissionPermissionFilter(object_permission_model=Account)

    class Meta:
        model = Account
        fields = []


class AccountViewSet(AbstractWithObjectPermissionViewSet):
    queryset = Account.objects.select_related(
        'master_user', 'type', 'type',
    ).prefetch_related(
        'portfolios', 'tags',
        Prefetch('attributes', queryset=AccountAttribute.objects.select_related(
            'attribute_type', 'classifier'
        ).prefetch_related(
            'attribute_type__options'
        )),
        *get_permissions_prefetch_lookups(
            (None, Account),
            ('type', AccountType),
            ('portfolios', Portfolio),
            ('attributes__attribute_type', AccountAttributeType),
            ('tags', Tag)
        )
    )
    # prefetch_permissions_for = (
    #     ('type', AccountType),
    #     ('portfolios', Portfolio),
    #     ('attributes__attribute_type', AccountAttributeType),
    # )
    serializer_class = AccountSerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        # TagFilterBackend,
    ]
    filter_class = AccountFilterSet
    ordering_fields = [
        'user_code', 'name', 'short_name', 'public_name', 'is_valid_for_all_portfolios',
        'type', 'type__user_code', 'type__name', 'type__short_name', 'type__public_name',
    ]
