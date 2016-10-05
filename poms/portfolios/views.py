from __future__ import unicode_literals

import django_filters
from django.db.models import Prefetch
from rest_framework.filters import FilterSet

from poms.accounts.models import Account
from poms.common.filters import CharFilter, ModelExtWithPermissionMultipleChoiceFilter, NoOpFilter
from poms.counterparties.models import Responsible, Counterparty
from poms.obj_attrs.filters import AttributeTypeValueTypeFilter
from poms.obj_attrs.views import AbstractAttributeTypeViewSet, AbstractClassifierViewSet
from poms.obj_perms.filters import ObjectPermissionMemberFilter, ObjectPermissionGroupFilter, \
    ObjectPermissionPermissionFilter
from poms.obj_perms.utils import get_permissions_prefetch_lookups
from poms.obj_perms.views import AbstractWithObjectPermissionViewSet
from poms.portfolios.models import Portfolio, PortfolioAttributeType, PortfolioClassifier, PortfolioAttribute
from poms.portfolios.serializers import PortfolioSerializer, PortfolioAttributeTypeSerializer, \
    PortfolioClassifierNodeSerializer
from poms.tags.filters import TagFilter
from poms.tags.models import Tag
from poms.transactions.models import TransactionType
from poms.users.filters import OwnerByMasterUserFilter


class PortfolioAttributeTypeFilterSet(FilterSet):
    id = NoOpFilter()
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    public_name = CharFilter()
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
    filter_class = PortfolioAttributeTypeFilterSet


class PortfolioClassifierFilterSet(FilterSet):
    id = NoOpFilter()
    name = CharFilter()
    level = django_filters.NumberFilter()
    attribute_type = ModelExtWithPermissionMultipleChoiceFilter(model=PortfolioAttributeType)

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
    public_name = CharFilter()
    account = ModelExtWithPermissionMultipleChoiceFilter(model=Account, name='accounts')
    responsible = ModelExtWithPermissionMultipleChoiceFilter(model=Responsible, name='responsibles')
    counterparty = ModelExtWithPermissionMultipleChoiceFilter(model=Counterparty, name='counterparties')
    transaction_type = ModelExtWithPermissionMultipleChoiceFilter(model=TransactionType, name='transaction_types')
    tag = TagFilter(model=Portfolio)
    member = ObjectPermissionMemberFilter(object_permission_model=Portfolio)
    member_group = ObjectPermissionGroupFilter(object_permission_model=Portfolio)
    permission = ObjectPermissionPermissionFilter(object_permission_model=Portfolio)

    class Meta:
        model = Portfolio
        fields = []


class PortfolioViewSet(AbstractWithObjectPermissionViewSet):
    queryset = Portfolio.objects.select_related(
        'master_user',
    ).prefetch_related(
        'accounts', 'responsibles', 'counterparties', 'transaction_types', 'tags',
        Prefetch('attributes', queryset=PortfolioAttribute.objects.select_related('attribute_type', 'classifier')),
        *get_permissions_prefetch_lookups(
            (None, Portfolio),
            ('tags', Tag),
            ('counterparties', Counterparty),
            ('transaction_types', TransactionType),
            ('accounts', Account),
            ('responsibles', Responsible),
            ('attributes__attribute_type', PortfolioAttributeType)
        )
    )
    # prefetch_permissions_for = (
    #     ('counterparties', Counterparty),
    #     ('transaction_types', TransactionType),
    #     ('accounts', Account),
    #     ('responsibles', Responsible),
    #     ('attributes__attribute_type', PortfolioAttributeType)
    # )
    serializer_class = PortfolioSerializer
    filter_backends = AbstractWithObjectPermissionViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]
    filter_class = PortfolioFilterSet
    ordering_fields = [
        'user_code', 'name', 'short_name', 'public_name',
    ]
