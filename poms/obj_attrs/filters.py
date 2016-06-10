from rest_framework.filters import BaseFilterBackend

from poms.common.fields import FilteredPrimaryKeyRelatedField
from poms.obj_perms.filters import FieldObjectPermissionBackend


class AttributePrefetchFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset.prefetch_related(
            'attributes',
            'attributes__attribute_type',
            'attributes__attribute_type__user_object_permissions',
            'attributes__attribute_type__user_object_permissions__permission',
            'attributes__attribute_type__group_object_permissions',
            'attributes__attribute_type__group_object_permissions__permission',
        )


class OwnerByAttributeTypeFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        master_user = request.user.master_user
        queryset = queryset.filter(attribute_type__master_user=master_user)
        return queryset


class ClassifierPermissionBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        attribute_type_model = queryset.model._meta.get_field('attribute_type').related_model
        attribute_type_qs = attribute_type_model.objects.all()
        attribute_type_qs = FieldObjectPermissionBackend().filter_queryset(request, attribute_type_qs, view)
        queryset = queryset.filter(attribute_type__in=attribute_type_qs)
        return queryset


class AttributeClassifierBaseField(FilteredPrimaryKeyRelatedField):
    filter_backends = [
        OwnerByAttributeTypeFilter,
        ClassifierPermissionBackend,
    ]
