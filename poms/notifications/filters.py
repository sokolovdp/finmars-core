from __future__ import unicode_literals

from rest_framework.filters import BaseFilterBackend


class OwnerByRecipientFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        queryset = queryset.filter(recipient=request.user)
        if request.GET.get('all') in ['1', 'true', 'yes']:
            return queryset
        else:
            return queryset.filter(read_date__isnull=True)
