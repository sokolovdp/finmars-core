from collections import OrderedDict

from django_filters import MultipleChoiceFilter
from rest_framework.filters import BaseFilterBackend, OrderingFilter

from poms.common.fields import PrimaryKeyRelatedFilteredField
from poms.obj_attrs.models import GenericAttributeType


class OwnerByAttributeTypeFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        master_user = request.user.master_user
        # queryset = queryset.filter(attribute_type__master_user=master_user)
        # attribute_type_model = queryset.model._meta.get_field('attribute_type').rel.to
        attribute_type_model = queryset.model._meta.get_field("attribute_type").remote_field.model
        attribute_type_queryset = attribute_type_model.objects.filter(master_user=master_user)

        return queryset.filter(attribute_type__in=attribute_type_queryset)


class ClassifierPermissionBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset


class AttributeClassifierBaseField(PrimaryKeyRelatedFilteredField):
    filter_backends = [
        OwnerByAttributeTypeFilter,
        ClassifierPermissionBackend,
    ]


class AttributeTypeValueTypeFilter(MultipleChoiceFilter):
    def __init__(self, *args, **kwargs):
        kwargs["choices"] = GenericAttributeType.VALUE_TYPES
        super().__init__(*args, **kwargs)


class OrderingWithAttributesFilter(OrderingFilter):
    def __init__(self):
        super().__init__()
        self._attr_types = None

    def get_valid_fields(self, queryset, view):
        valid_fields = super().get_valid_fields(queryset, view)

        attr_types = self.get_attr_types(queryset, view.request)
        attr_fields = [(f"attr_{a.pk}", a.name) for a in attr_types if a.value_type != a.CLASSIFIER]

        return valid_fields + attr_fields

    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)
        if ordering:
            attr_model = queryset.model
            queryset = self.add_extra_fields(queryset, attr_model, self.get_attr_types(queryset, request), ordering)
            return queryset.order_by(*ordering)
        return queryset

    def get_attr_types(self, queryset, request):
        if self._attr_types is not None:
            return self._attr_types
        attr_type_model = queryset.model
        attr_type_qs = attr_type_model.objects.filter(master_user=request.user.master_user).order_by("name", "pk")
        self._attr_types = list(attr_type_qs)
        return self._attr_types

    def add_extra_fields(self, queryset, attr_model, attr_types, ordering):
        d = OrderedDict()
        for attr_type in attr_types:
            key = f"attr_{attr_type.id}"
            if key in ordering and attr_type.value_type != attr_type.CLASSIFIER:
                value_attr = attr_type.get_value_atr()
                d[key] = (
                    f"select __attr.{value_attr} "
                    f"from {attr_model._meta.db_table} __attr "
                    f"where __attr.content_object_id={queryset.model._meta.db_table}.id "
                    f"and __attr.attribute_type_id={attr_type.id}"
                )
        if d:
            return queryset.extra(select=d)
        else:
            return queryset
