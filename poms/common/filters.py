from collections import OrderedDict

from rest_framework.filters import BaseFilterBackend, FilterSet, OrderingFilter

from poms.obj_attrs.utils import get_attr_type_model, get_attr_model


class OrderingWithAttributesFilter(OrderingFilter):
    def __init__(self):
        super(OrderingWithAttributesFilter, self).__init__()
        self._attr_types = None

    def get_valid_fields(self, queryset, view):
        valid_fields = super(OrderingWithAttributesFilter, self).get_valid_fields(queryset, view)

        attr_types = self.get_attr_types(queryset, view.request)
        attr_fields = [('attr_%s' % a.pk, a.name) for a in attr_types if a.value_type != a.CLASSIFIER]

        return valid_fields + attr_fields

    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)
        if ordering:
            attr_model = get_attr_model(queryset.model)
            queryset = self.add_extra_fields(queryset, attr_model, self.get_attr_types(queryset, request), ordering)
            return queryset.order_by(*ordering)
        return queryset

    def get_attr_types(self, queryset, request):
        if self._attr_types is not None:
            return self._attr_types
        attr_type_model = get_attr_type_model(queryset.model)
        master_user = request.user.master_user
        self._attr_types = list(attr_type_model.objects.filter(master_user=master_user).order_by('name', 'pk'))
        return self._attr_types

    def add_extra_fields(self, queryset, attr_model, attr_types, ordering):
        d = OrderedDict()
        for attr_type in attr_types:
            key = 'attr_%s' % attr_type.id
            if key in ordering and attr_type.value_type != attr_type.CLASSIFIER:
                value_attr = attr_type.get_value_atr()
                d[key] = \
                    'select __attr.%(attr_value)s ' \
                    'from %(attr_tbl)s __attr ' \
                    'where __attr.content_object_id=%(obj_tbl)s.id and __attr.attribute_type_id=%(attr_type_id)s' % {
                        'obj_tbl': queryset.model._meta.db_table,
                        'attr_tbl': attr_model._meta.db_table,
                        'attr_type_id': attr_type.id,
                        'attr_value': value_attr,
                    }
        if d:
            return queryset.extra(select=d)
        else:
            return queryset


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
    # parent = django_filters.MethodFilter(name='parent', label=_('Parent'))

    class Meta:
        # fields = ['parent', 'user_code', 'name', 'short_name']
        fields = ['user_code', 'name', 'short_name']

    def parent_filter(self, qs, value):
        return qs
