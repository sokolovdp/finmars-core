from __future__ import unicode_literals

from django.db.models import Q
from rest_framework.filters import BaseFilterBackend


class NotificationFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        queryset = queryset.filter(
            recipient=request.user
        ).filter(
            Q(recipient_member__isnull=True) | Q(recipient_member=request.user.member)
        )
        if request.GET.get('all') in ['1', 'true', 'yes']:
            return queryset
        else:
            return queryset.filter(read_date__isnull=True)
