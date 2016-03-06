from __future__ import unicode_literals

from django.db.models import Q
from rest_framework.filters import BaseFilterBackend


class IsOwnerFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(user=request.user)


class IsOwnerByMasterUserFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(master_user__user=request.user)


class IsOwnerByMasterUserOrSystemFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(Q(master_user__user=request.user) | Q(master_user__isnull=True))
