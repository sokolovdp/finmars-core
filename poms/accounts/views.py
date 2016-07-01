from __future__ import unicode_literals

from rest_framework.filters import FilterSet, DjangoFilterBackend, OrderingFilter, SearchFilter

from poms.accounts.models import Account, AccountType, AccountAttributeType
from poms.accounts.serializers import AccountSerializer, AccountTypeSerializer, AccountAttributeTypeSerializer
from poms.common.filters import CharFilter, ModelWithPermissionMultipleChoiceFilter
from poms.obj_attrs.filters import AttributePrefetchFilter
from poms.obj_attrs.views import AttributeTypeViewSetBase
from poms.obj_perms.views import AbstractViewSetWithObjectPermission
from poms.portfolios.models import Portfolio
from poms.tags.filters import TagFilterBackend, TagFilter
from poms.users.filters import OwnerByMasterUserFilter


class AccountTypeFilterSet(FilterSet):
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    tag = TagFilter(model=AccountType)

    class Meta:
        model = AccountType
        fields = ['user_code', 'name', 'short_name', 'tags']


class AccountTypeViewSet(AbstractViewSetWithObjectPermission):
    queryset = AccountType.objects
    serializer_class = AccountTypeSerializer
    filter_backends = [
        OwnerByMasterUserFilter,
        # ObjectPermissionBackend,
        TagFilterBackend,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    filter_class = AccountTypeFilterSet
    # permission_classes = PomsViewSetBase.permission_classes + [
    #     ObjectPermissionBase,
    # ]
    ordering_fields = ['user_code', 'name', 'short_name', ]
    search_fields = ['user_code', 'name', 'short_name', ]

    # def get_serializer(self, *args, **kwargs):
    #     kwargs['show_object_permissions'] = (self.action != 'list')
    #     return super(AccountTypeViewSet, self).get_serializer(*args, **kwargs)


class AccountAttributeTypeFilterSet(FilterSet):
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()

    class Meta:
        model = AccountAttributeType
        fields = ['user_code', 'name', 'short_name']


class AccountAttributeTypeViewSet(AttributeTypeViewSetBase):
    queryset = AccountAttributeType.objects.prefetch_related('classifiers')
    serializer_class = AccountAttributeTypeSerializer
    # filter_backends = [
    #     OwnerByMasterUserFilter,
    #     # ObjectPermissionBackend,
    #     DjangoFilterBackend,
    #     OrderingFilter,
    #     SearchFilter,
    # ]
    filter_class = AccountAttributeTypeFilterSet
    # permission_classes = PomsViewSetBase.permission_classes + [
    #     ObjectPermissionBase,
    # ]
    # ordering_fields = ['user_code', 'name', 'short_name', ]
    # search_fields = ['user_code', 'name', 'short_name', ]

    # def get_serializer(self, *args, **kwargs):
    #     kwargs['show_object_permissions'] = (self.action != 'list')
    #     return super(AccountAttributeTypeViewSet, self).get_serializer(*args, **kwargs)


class AccountFilterSet(FilterSet):
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()
    portfolio = ModelWithPermissionMultipleChoiceFilter(model=Portfolio, name='portfolios')
    type = ModelWithPermissionMultipleChoiceFilter(model=AccountType)
    tag = TagFilter(model=Account)

    class Meta:
        model = Account
        fields = ['user_code', 'name', 'short_name', 'type', 'portfolio', 'tag']


class AccountViewSet(AbstractViewSetWithObjectPermission):
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
    filter_backends = [
        OwnerByMasterUserFilter,
        # ObjectPermissionBackend,
        TagFilterBackend,
        AttributePrefetchFilter,
        DjangoFilterBackend,
        OrderingFilter,
        # OrderingWithAttributesFilter,
        SearchFilter,
    ]
    filter_class = AccountFilterSet
    # permission_classes = PomsViewSetBase.permission_classes + [
    #     ObjectPermissionBase
    # ]
    ordering_fields = [
        'user_code', 'name', 'short_name',
        'type__user_code', 'type__name', 'type__short_name',
    ]
    search_fields = [
        'user_code', 'name', 'short_name',
        'type__user_code', 'type__name', 'type__short_name',
    ]

    def get_serializer(self, *args, **kwargs):
        kwargs['show_object_permissions'] = (self.action != 'list')
        return super(AccountViewSet, self).get_serializer(*args, **kwargs)
