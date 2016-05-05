from __future__ import unicode_literals

import django_filters
from rest_framework.filters import FilterSet, DjangoFilterBackend, OrderingFilter, SearchFilter

from poms.accounts.models import Account, AccountType, AccountClassifier, AccountAttributeType
from poms.accounts.serializers import AccountSerializer, AccountTypeSerializer, AccountClassifierSerializer, \
    AccountAttributeTypeSerializer, AccountClassifierNodeSerializer
from poms.common.filters import ClassifierFilterSetBase, OrderingWithAttributesFilter
from poms.common.views import ClassifierViewSetBase, PomsViewSetBase, ClassifierNodeViewSetBase
from poms.obj_attrs.filters import AttributePrefetchFilter
from poms.obj_attrs.views import AttributeTypeViewSetBase
from poms.obj_perms.filters import ObjectPermissionPrefetchFilter, ObjectPermissionFilter
from poms.obj_perms.permissions import ObjectPermissionBase
from poms.tags.filters import TagPrefetchFilter, ByTagNameFilter
from poms.users.filters import OwnerByMasterUserFilter


class AccountClassifierFilterSet(ClassifierFilterSetBase):
    class Meta(ClassifierFilterSetBase.Meta):
        model = AccountClassifier


class AccountClassifierViewSet(ClassifierViewSetBase):
    queryset = AccountClassifier.objects.all()
    filter_backends = ClassifierViewSetBase.filter_backends + [
        ObjectPermissionPrefetchFilter,
    ]
    serializer_class = AccountClassifierSerializer
    filter_class = AccountClassifierFilterSet


class AccountClassifierNodeViewSet(ClassifierNodeViewSetBase):
    queryset = AccountClassifier.objects.all()
    filter_backends = ClassifierNodeViewSetBase.filter_backends + [
        ObjectPermissionPrefetchFilter,
    ]
    serializer_class = AccountClassifierNodeSerializer
    filter_class = AccountClassifierFilterSet


class AccountTypeFilterSet(FilterSet):
    tags = django_filters.MethodFilter(action='tags_filter')

    class Meta:
        model = AccountType
        fields = ['tags']

    @staticmethod
    def tags_filter(queryset, value):
        return queryset


class AccountTypeViewSet(PomsViewSetBase):
    queryset = AccountType.objects
    serializer_class = AccountTypeSerializer
    filter_backends = [
        OwnerByMasterUserFilter,
        TagPrefetchFilter,
        ByTagNameFilter,
        ObjectPermissionPrefetchFilter,
        ObjectPermissionFilter,
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


class AccountAttributeTypeViewSet(AttributeTypeViewSetBase):
    queryset = AccountAttributeType.objects.all()
    serializer_class = AccountAttributeTypeSerializer


class AccountFilterSet(FilterSet):
    tags = django_filters.MethodFilter(action='tags_filter')

    class Meta:
        model = Account
        fields = ['tags']

    @staticmethod
    def tags_filter(queryset, value):
        return queryset


class AccountViewSet(PomsViewSetBase):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    filter_backends = [
        OwnerByMasterUserFilter,
        AttributePrefetchFilter,
        TagPrefetchFilter,
        ByTagNameFilter,
        ObjectPermissionPrefetchFilter,
        ObjectPermissionFilter,
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
