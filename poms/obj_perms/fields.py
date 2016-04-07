from __future__ import unicode_literals

import six
from rest_framework import serializers

from poms.audit import history
from poms.users.utils import get_member


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

        member = get_member(self.context['request'])

        perms = set()
        for uop in value.user_object_permissions.all():
            if uop.member_id == member.id:
                perms.add(uop.permission.codename)
        for gop in value.group_object_permissions.all():
            if gop.group in member.groups.all():
                perms.add(gop.permission.codename)

        return perms


class ObjectPermissionField(serializers.Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(ObjectPermissionField, self).__init__(**kwargs)

    def bind(self, field_name, parent):
        super(ObjectPermissionField, self).bind(field_name, parent)

    def to_representation(self, value):
        if history.is_historical_proxy(value):
            return []

        users = {}
        groups = {}
        for uop in value.user_object_permissions.all():
            try:
                user_perms = users[uop.member_id]
            except KeyError:
                users[uop.member_id] = user_perms = {
                    'id': uop.member_id,
                    'permissions': set(),
                }
            user_perms['permissions'].add(uop.permission.codename)
        for gop in value.group_object_permissions.all():
            try:
                group_perms = groups[gop.group_id]
            except KeyError:
                groups[gop.group_id] = group_perms = {
                    'id': gop.group_id,
                    'permissions': set(),
                }
            group_perms['permissions'].add(gop.permission.codename)

        return {
            'users': [v for v in six.itervalues(users)],
            'groups': [v for v in six.itervalues(groups)],
        }
