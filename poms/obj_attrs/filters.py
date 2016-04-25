from rest_framework.filters import BaseFilterBackend

from poms.obj_perms.utils import obj_perms_filter_objects


class AttributePrefetchFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset.prefetch_related('attributes', 'attributes__attribute_type')
