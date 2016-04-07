from __future__ import unicode_literals

from rest_framework import serializers

from poms.audit import history


class GrantedPermissionField(serializers.Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(GrantedPermissionField, self).__init__(**kwargs)

    def bind(self, field_name, parent):
        super(GrantedPermissionField, self).bind(field_name, parent)

    def to_representation(self, value):
        if history.is_historical_proxy(value):
            return []
        user = self.context['request'].user
        return user.get_all_permissions(value)
