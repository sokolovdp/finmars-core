from __future__ import unicode_literals

from rest_framework.compat import unicode_to_repr
from rest_framework.relations import PrimaryKeyRelatedField


class CurrentMasterUserDefault(object):
    def set_context(self, serializer_field):
        user = serializer_field.context['request'].user
        # if hasattr(user, 'master_user'):
        #     self.master_user = user.master_user
        # elif hasattr(user, 'employee'):
        #     self.master_user = user.employee.master_user
        # else:
        #     self.master_user = None
        self.master_user = user.profile.master_user

    def __call__(self):
        return self.master_user

    def __repr__(self):
        return unicode_to_repr('%s()' % self.__class__.__name__)


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
            for backend in list(self.filter_backends):
                queryset = backend().filter_queryset(request, queryset, None)
        return queryset
