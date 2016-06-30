from __future__ import unicode_literals

from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter, FilterSet

from poms.accounts.models import Account
from poms.common.filters import CharFilter, ModelWithPermissionMultipleChoiceFilter
from poms.common.views import PomsViewSetBase
from poms.counterparties.models import Responsible, Counterparty
from poms.obj_attrs.filters import AttributePrefetchFilter
from poms.obj_attrs.views import AttributeTypeViewSetBase
from poms.obj_perms.filters import ObjectPermissionBackend
from poms.obj_perms.permissions import ObjectPermissionBase
from poms.portfolios.models import Portfolio, PortfolioAttributeType
from poms.portfolios.serializers import PortfolioSerializer, PortfolioAttributeTypeSerializer
from poms.tags.filters import TagFilterBackend, TagFilter
from poms.transactions.models import TransactionType
from poms.users.filters import OwnerByMasterUserFilter


class PortfolioAttributeTypeFilterSet(FilterSet):
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()

    class Meta:
        model = PortfolioAttributeType
        fields = ['user_code', 'name', 'short_name']


class PortfolioAttributeTypeViewSet(AttributeTypeViewSetBase):
    queryset = PortfolioAttributeType.objects.prefetch_related('classifiers')
    serializer_class = PortfolioAttributeTypeSerializer
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionBackend,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    filter_class = PortfolioAttributeTypeFilterSet
    permission_classes = PomsViewSetBase.permission_classes + [
        ObjectPermissionBase,
    ]
    ordering_fields = ['user_code', 'name', 'short_name', ]
    search_fields = ['user_code', 'name', 'short_name', ]


class PortfolioFilterSet(FilterSet):
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    account = ModelWithPermissionMultipleChoiceFilter(model=Account, name='accounts')
    responsible = ModelWithPermissionMultipleChoiceFilter(model=Responsible, name='responsibles')
    counterparty = ModelWithPermissionMultipleChoiceFilter(model=Counterparty, name='counterparties')
    transaction_type = ModelWithPermissionMultipleChoiceFilter(model=TransactionType, name='transaction_types')
    tag = TagFilter(model=Portfolio)

    class Meta:
        model = Portfolio
        fields = ['user_code', 'name', 'short_name', 'account', 'responsible', 'counterparty', 'transaction_type',
                  'tag', ]


class PortfolioViewSet(PomsViewSetBase):
    queryset = Portfolio.objects.prefetch_related(
        'accounts',
        'accounts__user_object_permissions', 'accounts__user_object_permissions__permission',
        'accounts__group_object_permissions', 'accounts__group_object_permissions__permission',
        'responsibles',
        'responsibles__user_object_permissions', 'responsibles__user_object_permissions__permission',
        'responsibles__group_object_permissions', 'responsibles__group_object_permissions__permission',
        'counterparties',
        'counterparties__user_object_permissions', 'counterparties__user_object_permissions__permission',
        'counterparties__group_object_permissions', 'counterparties__group_object_permissions__permission',
        'transaction_types',
        'transaction_types__user_object_permissions', 'transaction_types__user_object_permissions__permission',
        'transaction_types__group_object_permissions', 'transaction_types__group_object_permissions__permission',
    )
    serializer_class = PortfolioSerializer
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionBackend,
        TagFilterBackend,
        AttributePrefetchFilter,
        DjangoFilterBackend,
        OrderingFilter,
        # OrderingWithAttributesFilter,
        SearchFilter,
    ]
    filter_class = PortfolioFilterSet
    permission_classes = PomsViewSetBase.permission_classes + [
        ObjectPermissionBase
    ]
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']
