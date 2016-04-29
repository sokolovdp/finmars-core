from __future__ import unicode_literals

from rest_framework.filters import FilterSet, DjangoFilterBackend, OrderingFilter, SearchFilter

from poms.accounts.models import Account, AccountType, AccountClassifier, AccountAttributeType
from poms.accounts.serializers import AccountSerializer, AccountTypeSerializer, AccountClassifierSerializer, \
    AccountAttributeTypeSerializer, AccountClassifierNodeSerializer
from poms.common.filters import ClassifierFilterSetBase
from poms.common.views import ClassifierViewSetBase, PomsViewSetBase, ClassifierNodeViewSetBase
from poms.obj_attrs.filters import AttributePrefetchFilter
from poms.obj_attrs.views import AttributeTypeViewSetBase
from poms.obj_perms.filters import ObjectPermissionPrefetchFilter, ObjectPermissionFilter
from poms.obj_perms.permissions import ObjectPermissionBase
from poms.tags.filters import TagPrefetchFilter
from poms.users.filters import OwnerByMasterUserFilter


class AccountClassifierFilterSet(ClassifierFilterSetBase):
    class Meta(ClassifierFilterSetBase.Meta):
        model = AccountClassifier


class AccountClassifierViewSet(ClassifierViewSetBase):
    queryset = AccountClassifier.objects.all()
    filter_backends = [ObjectPermissionPrefetchFilter] + ClassifierViewSetBase.filter_backends
    serializer_class = AccountClassifierSerializer
    filter_class = AccountClassifierFilterSet


class AccountClassifierNodeViewSet(ClassifierNodeViewSetBase):
    queryset = AccountClassifier.objects.all()
    filter_backends = [ObjectPermissionPrefetchFilter] + ClassifierNodeViewSetBase.filter_backends
    serializer_class = AccountClassifierNodeSerializer
    filter_class = AccountClassifierFilterSet


class AccountTypeViewSet(PomsViewSetBase):
    queryset = AccountType.objects
    serializer_class = AccountTypeSerializer
    filter_backends = [OwnerByMasterUserFilter, TagPrefetchFilter,
                       ObjectPermissionPrefetchFilter,
                       ObjectPermissionFilter,
                       DjangoFilterBackend, OrderingFilter, SearchFilter]
    permission_classes = PomsViewSetBase.permission_classes + \
                         [ObjectPermissionBase]
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']


class AccountAttributeTypeViewSet(AttributeTypeViewSetBase):
    queryset = AccountAttributeType.objects.all()
    serializer_class = AccountAttributeTypeSerializer
    # permission_classes = PomsViewSetBase.permission_classes + \
    #                      [ObjectPermissionBase]


class AccountFilterSet(FilterSet):
    class Meta:
        model = Account
        fields = []


class AccountViewSet(PomsViewSetBase):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    filter_backends = [OwnerByMasterUserFilter, AttributePrefetchFilter, TagPrefetchFilter,
                       ObjectPermissionPrefetchFilter,
                       ObjectPermissionFilter,
                       DjangoFilterBackend, OrderingFilter, SearchFilter, ]
    permission_classes = PomsViewSetBase.permission_classes + \
                         [ObjectPermissionBase]
    filter_class = AccountFilterSet
    ordering_fields = ['user_code', 'name', 'short_name']
    search_fields = ['user_code', 'name', 'short_name']
