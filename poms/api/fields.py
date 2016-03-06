from __future__ import unicode_literals

from rest_framework.compat import unicode_to_repr


class CurrentMasterUserDefault(object):
    def set_context(self, serializer_field):
        user = serializer_field.context['request'].user
        if hasattr(user, 'master_user'):
            self.master_user = user.master_user
        elif hasattr(user, 'employee'):
            self.master_user = user.employee.master_user
        else:
            self.master_user = None

    def __call__(self):
        return self.master_user

    def __repr__(self):
        return unicode_to_repr('%s()' % self.__class__.__name__)
