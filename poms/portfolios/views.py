from __future__ import unicode_literals

import django_filters
from rest_framework.filters import FilterSet

from poms.accounts.models import Account
from poms.common.filters import CharFilter, ModelWithPermissionMultipleChoiceFilter, NoOpFilter
from poms.counterparties.models import Responsible, Counterparty
from poms.obj_attrs.filters import AttributeTypeValueTypeFilter
from poms.obj_attrs.views import AbstractAttributeTypeViewSet, AbstractClassifierViewSet
from poms.obj_perms.filters import ObjectPermissionMemberFilter, ObjectPermissionGroupFilter, \
    ObjectPermissionPermissionFilter
from poms.obj_perms.views import AbstractWithObjectPermissionViewSet
from poms.portfolios.models import Portfolio, PortfolioAttributeType, PortfolioClassifier
from poms.portfolios.serializers import PortfolioSerializer, PortfolioAttributeTypeSerializer, \
    PortfolioClassifierNodeSerializer, PortfolioAttributeTypeBulkObjectPermissionSerializer, \
    PortfolioBulkObjectPermissionSerializer
from poms.tags.filters import TagFilterBackend, TagFilter
from poms.transactions.models import TransactionType
from poms.users.filters import OwnerByMasterUserFilter


class PortfolioAttributeTypeFilterSet(FilterSet):
    id = NoOpFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    value_type = AttributeTypeValueTypeFilter()
    member = ObjectPermissionMemberFilter(object_permission_model=PortfolioAttributeType)
    member_group = ObjectPermissionGroupFilter(object_permission_model=PortfolioAttributeType)
    permission = ObjectPermissionPermissionFilter(object_permission_model=PortfolioAttributeType)

    class Meta:
        model = PortfolioAttributeType
        fields = []


class PortfolioAttributeTypeViewSet(AbstractAttributeTypeViewSet):
    queryset = PortfolioAttributeType.objects.prefetch_related('classifiers')
    serializer_class = PortfolioAttributeTypeSerializer
    bulk_objects_permissions_serializer_class = PortfolioAttributeTypeBulkObjectPermissionSerializer
    filter_class = PortfolioAttributeTypeFilterSet


class PortfolioClassifierFilterSet(FilterSet):
    id = NoOpFilter()
    name = CharFilter()
    level = django_filters.NumberFilter()
    attribute_type = ModelWithPermissionMultipleChoiceFilter(model=PortfolioAttributeType)

    class Meta:
        model = PortfolioClassifier
        fields = []


class PortfolioClassifierViewSet(AbstractClassifierViewSet):
    queryset = PortfolioClassifier.objects
    serializer_class = PortfolioClassifierNodeSerializer
    filter_class = PortfolioClassifierFilterSet


class PortfolioFilterSet(FilterSet):
    id = NoOpFilter()
    is_deleted = django_filters.BooleanFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    account = ModelWithPermissionMultipleChoiceFilter(model=Account, name='accounts')
    responsible = ModelWithPermissionMultipleChoiceFilter(model=Responsible, name='responsibles')
    counterparty = ModelWithPermissionMultipleChoiceFilter(model=Counterparty, name='counterparties')
    transaction_type = ModelWithPermissionMultipleChoiceFilter(model=TransactionType, name='transaction_types')
    tag = TagFilter(model=Portfolio)
    member = ObjectPermissionMemberFilter(object_permission_model=Portfolio)
    member_group = ObjectPermissionGroupFilter(object_permission_model=Portfolio)
    permission = ObjectPermissionPermissionFilter(object_permission_model=Portfolio)

    class Meta:
        model = Portfolio
        fields = []


class PortfolioViewSet(AbstractWithObjectPermissionViewSet):
    queryset = Portfolio.objects.prefetch_related(
        'master_user', 'accounts', 'responsibles', 'counterparties', 'transaction_types',
        'attributes', 'attributes__attribute_type'
    )
    prefetch_permissions_for = ('counterparties', 'transaction_types', 'accounts', 'responsibles',
                                'attributes__attribute_type',)
    serializer_class = PortfolioSerializer
    bulk_objects_permissions_serializer_class = PortfolioBulkObjectPermissionSerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        TagFilterBackend,
    ]
    filter_class = PortfolioFilterSet
    ordering_fields = [
        'user_code', 'name', 'short_name'
    ]
    search_fields = [
        'user_code', 'name', 'short_name'
    ]
    has_feature_is_deleted = True
