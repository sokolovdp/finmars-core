from __future__ import unicode_literals

from rest_framework.fields import CharField
from rest_framework.relations import PrimaryKeyRelatedField, SlugRelatedField
from rest_framework.validators import UniqueTogetherValidator


class FilteredPrimaryKeyRelatedField(PrimaryKeyRelatedField):
    filter_backends = None

    def __init__(self, filter_backends=None, **kwargs):
        if filter_backends:
            self.filter_backends = filter_backends
        super(FilteredPrimaryKeyRelatedField, self).__init__(**kwargs)

    def get_queryset(self):
        queryset = super(FilteredPrimaryKeyRelatedField, self).get_queryset()
        queryset = self.filter_queryset(queryset)
        return queryset

    def filter_queryset(self, queryset):
        if self.filter_backends:
            request = self.context['request']
            for backend in self.filter_backends:
                queryset = backend().filter_queryset(request, queryset, None)
        return queryset


class FilteredSlugRelatedField(SlugRelatedField):
    filter_backends = None

    def __init__(self, filter_backends=None, **kwargs):
        if filter_backends:
            self.filter_backends = filter_backends
        super(FilteredSlugRelatedField, self).__init__(**kwargs)

    def get_queryset(self):
        queryset = super(FilteredSlugRelatedField, self).get_queryset()
        queryset = self.filter_queryset(queryset)
        return queryset

    def filter_queryset(self, queryset):
        if self.filter_backends:
            request = self.context['request']
            for backend in self.filter_backends:
                queryset = backend().filter_queryset(request, queryset, None)
        return queryset


class UserCodeField(CharField):
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 25
        kwargs['allow_blank'] = True
        kwargs['validators'] = [
            UniqueTogetherValidator()
        ]
        super(UserCodeField, self).__init__(**kwargs)
