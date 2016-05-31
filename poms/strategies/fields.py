from __future__ import unicode_literals

from poms.common.fields import FilteredPrimaryKeyRelatedField
from poms.obj_perms.filters import ObjectPermissionPrefetchFilter, ObjectPermissionFilter
from poms.strategies.models import Strategy1, Strategy2, Strategy3
from poms.users.filters import OwnerByMasterUserFilter


# class StrategyField(FilteredPrimaryKeyRelatedField):
#     queryset = Strategy.objects
#     filter_backends = [
#         OwnerByMasterUserFilter,
#         ObjectPermissionPrefetchFilter,
#         ObjectPermissionFilter,
#     ]


# class StrategyRootField(FilteredPrimaryKeyRelatedField):
#     queryset = Strategy.objects.filter(parent__isnull=True)
#     filter_backends = [
#         OwnerByMasterUserFilter,
#         ObjectPermissionPrefetchFilter,
#         ObjectPermissionFilter,
#     ]


class Strategy1Field(FilteredPrimaryKeyRelatedField):
    queryset = Strategy1.objects
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionPrefetchFilter,
        ObjectPermissionFilter,
    ]


# class Strategy1RootField(FilteredPrimaryKeyRelatedField):
#     queryset = Strategy1.objects.filter(parent__isnull=True)
#     filter_backends = [
#         OwnerByMasterUserFilter,
#         ObjectPermissionPrefetchFilter,
#         ObjectPermissionFilter,
#     ]


class Strategy2Field(FilteredPrimaryKeyRelatedField):
    queryset = Strategy2.objects
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionPrefetchFilter,
        ObjectPermissionFilter,
    ]


# class Strategy2RootField(FilteredPrimaryKeyRelatedField):
#     queryset = Strategy2.objects.filter(parent__isnull=True)
#     filter_backends = [
#         OwnerByMasterUserFilter,
#         ObjectPermissionPrefetchFilter,
#         ObjectPermissionFilter,
#     ]


class Strategy3Field(FilteredPrimaryKeyRelatedField):
    queryset = Strategy3.objects
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionPrefetchFilter,
        ObjectPermissionFilter,
    ]


# class Strategy3RootField(FilteredPrimaryKeyRelatedField):
#     queryset = Strategy3.objects.filter(parent__isnull=True)
#     filter_backends = [
#         OwnerByMasterUserFilter,
#         ObjectPermissionPrefetchFilter,
#         ObjectPermissionFilter,
#     ]
