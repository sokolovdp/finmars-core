from rest_framework.filters import BaseFilterBackend

from poms.common.fields import PrimaryKeyRelatedFilteredField
from poms.obj_attrs.filters import OwnerByAttributeTypeFilter
from poms.obj_attrs.models import GenericAttributeType, GenericClassifier
from poms.obj_perms.filters import ObjectPermissionBackend
from poms.users.filters import OwnerByMasterUserFilter


class GenericAttributeTypeField(PrimaryKeyRelatedFilteredField):
    queryset = GenericAttributeType.objects
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionBackend,
    ]


class GenericClassifierPermissionBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        attribute_type_model = queryset.model._meta.get_field('attribute_type').related_model
        attribute_type_qs = attribute_type_model.objects.all()
        attribute_type_qs = ObjectPermissionBackend().filter_queryset(request, attribute_type_qs, view)
        queryset = queryset.filter(attribute_type__in=attribute_type_qs)
        return queryset


class GenericClassifierField(PrimaryKeyRelatedFilteredField):
    queryset = GenericClassifier.objects
    filter_backends = [
        OwnerByAttributeTypeFilter,
        GenericClassifierPermissionBackend,
    ]
