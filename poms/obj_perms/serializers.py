from __future__ import unicode_literals

from rest_framework import serializers

from poms.obj_perms.fields import PermissionField
from poms.obj_perms.utils import assign_perms_to_new_obj
from poms.users.fields import MemberField, GroupField
from poms.users.utils import get_member


class UserObjectPermissionSerializer(serializers.Serializer):
    member = MemberField()
    permission = PermissionField()

    class Meta:
        fields = ['id', 'member', 'permission']


class GroupObjectPermissionSerializer(serializers.Serializer):
    group = GroupField()
    permission = PermissionField()

    class Meta:
        fields = ['id', 'member', 'permission']


class ModelWithPermissionSerializer(serializers.ModelSerializer):
    owner_perms = ['change_%(model_name)s', 'delete_%(model_name)s', ]

    # owner_perms = ['change_%(model_name)s', 'delete_%(model_name)s', 'view_%(model_name)s', 'manage_%(model_name)s',]

    def get_owner_permissions(self, model_cls):
        kwargs = {
            'app_label': model_cls._meta.app_label,
            'model_name': model_cls._meta.model_name
        }
        return {perm % kwargs for perm in self.owner_perms}

    def create(self, validated_data):
        instance = super(ModelWithPermissionSerializer, self).create(validated_data)

        member = get_member(self.context['request'])
        perms = self.get_owner_permissions(instance)
        assign_perms_to_new_obj(obj=instance, owner=member, owner_perms=perms)

        return instance
