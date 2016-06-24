import django_filters
from rest_framework.filters import BaseFilterBackend, FilterSet


class ClassifierFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        parent_id = request.query_params.get('parent', None)
        if parent_id:
            parent = queryset.get(id=parent_id)
            return parent.get_family()
        else:
            return queryset.filter(parent__isnull=True)


class ClassifierRootFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(parent__isnull=True)


class ClassifierPrefetchFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset.prefetch_related('parent', 'children')


class ClassifierFilterSetBase(FilterSet):
    user_code = django_filters.CharFilter(lookup_expr='icontains')
    name = django_filters.CharFilter(lookup_expr='icontains')
    short_name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        # fields = ['parent', 'user_code', 'name', 'short_name']
        fields = ['user_code', 'name', 'short_name']

    def parent_filter(self, qs, value):
        return qs
