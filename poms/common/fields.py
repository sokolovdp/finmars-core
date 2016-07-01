from __future__ import unicode_literals

from django.utils import timezone
from rest_framework.fields import CharField, DateTimeField
from rest_framework.relations import PrimaryKeyRelatedField, SlugRelatedField


class PrimaryKeyRelatedFilteredField(PrimaryKeyRelatedField):
    filter_backends = None

    def __init__(self, filter_backends=None, **kwargs):
        if filter_backends:
            self.filter_backends = filter_backends
        super(PrimaryKeyRelatedFilteredField, self).__init__(**kwargs)

    def get_queryset(self):
        queryset = super(PrimaryKeyRelatedFilteredField, self).get_queryset()
        queryset = self.filter_queryset(queryset)
        return queryset

    def filter_queryset(self, queryset):
        if self.filter_backends:
            request = self.context['request']
            for backend in self.filter_backends:
                queryset = backend().filter_queryset(request, queryset, None)
        return queryset


class SlugRelatedFilteredField(SlugRelatedField):
    filter_backends = None

    def __init__(self, filter_backends=None, **kwargs):
        if filter_backends:
            self.filter_backends = filter_backends
        super(SlugRelatedFilteredField, self).__init__(**kwargs)

    def get_queryset(self):
        queryset = super(SlugRelatedFilteredField, self).get_queryset()
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
        kwargs['required'] = False
        kwargs['allow_null'] = True
        kwargs['allow_blank'] = True
        super(UserCodeField, self).__init__(**kwargs)


class DateTimeTzAwareField(DateTimeField):
    def to_representation(self, value):
        value = timezone.localtime(value)
        return super(DateTimeTzAwareField, self).to_representation(value)
