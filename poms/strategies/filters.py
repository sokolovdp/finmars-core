from rest_framework.filters import BaseFilterBackend


class StrategyFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        if view and view.action == 'list':
            return queryset.filter(parent__isnull=True)
        return queryset
