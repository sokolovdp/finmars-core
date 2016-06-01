from __future__ import unicode_literals

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from poms.obj_perms.utils import get_granted_permissions


class PermissionField(serializers.SlugRelatedField):
    queryset = Permission.objects

    def __init__(self, **kwargs):
        kwargs['slug_field'] = 'codename'
        super(PermissionField, self).__init__(**kwargs)

    def get_queryset(self):
        content_type = ContentType.objects.get_for_model(self.root.Meta.model)
        qs = super(PermissionField, self).get_queryset()
        return qs.select_related('content_type').filter(content_type=content_type)


class GrantedPermissionField(serializers.ReadOnlyField):
    def get_attribute(self, instance):
        return instance

    def to_representation(self, value):
        request = self.context['request']
        member = request.user.member
        perms = get_granted_permissions(member, value)
        return list(perms) if perms else []
