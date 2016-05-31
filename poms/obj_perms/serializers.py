from __future__ import unicode_literals

from collections import OrderedDict

from rest_framework import serializers

from poms.obj_perms.fields import PermissionField, GrantedPermissionField
from poms.obj_perms.utils import assign_perms_from_list, get_default_owner_permissions
from poms.users.fields import MemberField, GroupField


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


class ModelWithObjectPermissionSerializer(serializers.ModelSerializer):
    def get_fields(self):
        fields = super(ModelWithObjectPermissionSerializer, self).get_fields()
        fields.update(self.get_permissions_fields() or {})
        return fields

    def get_permissions_fields(self):
        fields = OrderedDict()
        fields['granted_permissions'] = GrantedPermissionField()

        member = self.context['request'].user.member
        if member.is_superuser:
            # additional permission fields "check" is not required
            fields['user_object_permissions'] = UserObjectPermissionSerializer(
                many=True, required=False, allow_null=True)
            fields['group_object_permissions'] = GroupObjectPermissionSerializer(
                many=True, required=False, allow_null=True)

        return fields

    def create(self, validated_data):
        user_object_permissions = validated_data.pop('user_object_permissions', None)
        group_object_permissions = validated_data.pop('group_object_permissions', None)
        instance = super(ModelWithObjectPermissionSerializer, self).create(validated_data)
        self.save_object_permission(instance,
                                    user_object_permissions=user_object_permissions,
                                    group_object_permissions=group_object_permissions,
                                    created=True)
        return instance

    def update(self, instance, validated_data):
        user_object_permissions = validated_data.pop('user_object_permissions', None)
        group_object_permissions = validated_data.pop('group_object_permissions', None)
        instance = super(ModelWithObjectPermissionSerializer, self).update(instance, validated_data)
        self.save_object_permission(instance,
                                    user_object_permissions=user_object_permissions,
                                    group_object_permissions=group_object_permissions,
                                    created=False)
        return instance

    def save_object_permission(self, instance, user_object_permissions=None, group_object_permissions=None,
                               created=False):
        if created:
            member = self.context['request'].user.member
            user_object_permissions = user_object_permissions or []
            user_object_permissions += [{'member': member, 'permission': p}
                                        for p in get_default_owner_permissions(instance)]
            assign_perms_from_list(instance,
                                   user_object_permissions=user_object_permissions,
                                   group_object_permissions=group_object_permissions)

        else:
            assign_perms_from_list(instance,
                                   user_object_permissions=user_object_permissions,
                                   group_object_permissions=group_object_permissions)
