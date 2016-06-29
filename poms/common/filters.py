from functools import partial

import django_filters
from rest_framework.filters import BaseFilterBackend, FilterSet

from poms.common.middleware import get_request
from poms.obj_perms.utils import obj_perms_filter_objects_for_view


# class ClassifierFilter(BaseFilterBackend):
#     def filter_queryset(self, request, queryset, view):
#         parent_id = request.query_params.get('parent', None)
#         if parent_id:
#             parent = queryset.get(id=parent_id)
#             return parent.get_family()
#         else:
#             return queryset.filter(parent__isnull=True)


def _model_choices(model, field_name='name'):
    master_user = get_request().user.master_user
    qs = model.objects.filter(master_user=master_user).order_by(field_name)
    for t in qs:
        yield t.id, getattr(t, field_name)


def _model_with_perms_choices(model, field_name='name'):
    master_user = get_request().user.master_user
    member = get_request().user.member
    qs = model.objects.filter(master_user=master_user).order_by(field_name)
    for t in obj_perms_filter_objects_for_view(member, qs, prefetch=False):
        yield t.id, getattr(t, field_name)


class ModelMultipleChoiceFilter(django_filters.MultipleChoiceFilter):
    model = None
    field_name = 'name'

    def __init__(self, *args, **kwargs):
        self.model = kwargs.pop('model', self.model)
        self.field_name = kwargs.pop('field_name', self.field_name)
        kwargs['choices'] = partial(_model_choices, model=self.model, field_name=self.field_name)
        super(ModelMultipleChoiceFilter, self).__init__(*args, **kwargs)


class ModelWithPermissionMultipleChoiceFilter(django_filters.MultipleChoiceFilter):
    model = None
    field_name = 'name'

    def __init__(self, *args, **kwargs):
        self.model = kwargs.pop('model', self.model)
        self.field_name = kwargs.pop('field_name', self.field_name)
        kwargs['choices'] = partial(_model_with_perms_choices, model=self.model, field_name=self.field_name)
        super(ModelWithPermissionMultipleChoiceFilter, self).__init__(*args, **kwargs)


class CharFilter(django_filters.CharFilter):
    def __init__(self, *args, **kwargs):
        kwargs['lookup_expr'] = 'icontains'
        super(CharFilter, self).__init__(*args, **kwargs)


class ClassifierFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        # queryset = queryset.prefetch_related('parent', 'children')
        if view and view.action == 'list':
            return queryset.filter(parent__isnull=True)
        return queryset.prefetch_related('parent', 'children')


class ClassifierRootFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(parent__isnull=True)


class ClassifierPrefetchFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset.prefetch_related('parent', 'children')


class ClassifierFilterSetBase(FilterSet):
    user_code = CharFilter()
    name = CharFilter()
    short_name = CharFilter()

    class Meta:
        fields = ['user_code', 'name', 'short_name']

    def parent_filter(self, qs, value):
        return qs
