import django_filters
from django.utils.translation import ugettext_lazy as _
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


class ClassifierFilterSetBase(FilterSet):
    parent = django_filters.MethodFilter(name='parent', label=_('Parent'))

    class Meta:
        fields = ['parent', 'user_code', 'name', 'short_name']

    def parent_filter(self, qs, value):
        return qs
