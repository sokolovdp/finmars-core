from rest_framework.filters import BaseFilterBackend

from poms.common.fields import FilteredPrimaryKeyRelatedField


class AttributePrefetchFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset.prefetch_related(
            'attributes',
            'attributes__attribute_type',
            # 'attributes__attribute_type__user_object_permissions',
            # 'attributes__attribute_type__user_object_permissions__permission',
            'attributes__attribute_type__group_object_permissions',
            'attributes__attribute_type__group_object_permissions__permission',
        )


class AttributeOwnerByTypeFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        master_user = request.user.master_user
        return queryset.filter(attribute_type__master_user=master_user)


class AttributeClassifierBaseField(FilteredPrimaryKeyRelatedField):
    filter_backends = [AttributeOwnerByTypeFilter]
