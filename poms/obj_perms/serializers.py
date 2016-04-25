from __future__ import unicode_literals

from rest_framework import serializers

from poms.obj_perms.fields import PermissionField
from poms.obj_perms.utils import get_granted_permissions, assign_perms_from_list, get_owner_default_permissions
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


# class ModelWithPermissionSerializer(serializers.ModelSerializer):
#     owner_perms = ['change_%(model_name)s', 'delete_%(model_name)s', ]
#
#     # owner_perms = ['change_%(model_name)s', 'delete_%(model_name)s', 'view_%(model_name)s', 'manage_%(model_name)s',]
#
#     def get_owner_permissions(self, model_cls):
#         kwargs = {
#             'app_label': model_cls._meta.app_label,
#             'model_name': model_cls._meta.model_name
#         }
#         return {perm % kwargs for perm in self.owner_perms}
#
#     def create(self, validated_data):
#         instance = super(ModelWithPermissionSerializer, self).create(validated_data)
#
#         request = self.context['request']
#         # member = get_member(request)
#         member = request.user.member
#
#         perms = self.get_owner_permissions(instance)
#         assign_perms_to_new_obj(obj=instance, owner=member, owner_perms=perms)
#
#         return instance


class GrantedPermissionField(serializers.ReadOnlyField):
    def get_attribute(self, instance):
        return instance

    def to_representation(self, value):
        request = self.context['request']
        # member = get_member(request)
        member = request.user.member
        return get_granted_permissions(member, value)


# class UserObjectPermissionListSerializer(serializers.ListSerializer):
#     def get_attribute(self, instance):
#         return instance.user_object_permissions
#
#
# class UserObjectPermissionSerializer2(serializers.Serializer):
#     member = MemberField()
#     permission = PermissionField()
#
#     class Meta:
#         fields = ['id', 'member', 'permission']
#         # list_serializer_class = UserObjectPermissionListSerializer
#
#
# class GroupObjectPermissionListSerializer(serializers.ListSerializer):
#     def get_attribute(self, instance):
#         return instance.group_object_permissions
#
#
# class GroupObjectPermissionSerializer2(serializers.Serializer):
#     group = GroupField()
#     permission = PermissionField()
#
#     class Meta:
#         fields = ['id', 'member', 'permission']
#         # list_serializer_class = GroupObjectPermissionListSerializer


class ObjectPermissionSerializer(serializers.Serializer):
    bypass1 = serializers.CharField(required=False, allow_null=True,
                                    help_text="without this field GUI falild on create or update :(")
    granted_permissions = GrantedPermissionField()
    user_object_permissions = UserObjectPermissionSerializer(many=True, required=False, allow_null=True)
    group_object_permissions = GroupObjectPermissionSerializer(many=True, required=False, allow_null=True)

    # class Meta:
    #     fields = [
    #         'granted_permissions',
    #         # 'user_object_permissions',
    #         # 'group_object_permissions'
    #     ]

    def get_attribute(self, instance):
        return instance


class ModelWithObjectPermissionSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        object_permission = validated_data.pop('object_permission', None)
        instance = super(ModelWithObjectPermissionSerializer, self).create(validated_data)
        if object_permission:
            self.save_object_permission(instance, object_permission, True)
        return instance

    def update(self, instance, validated_data):
        object_permission = validated_data.pop('object_permission', None)
        instance = super(ModelWithObjectPermissionSerializer, self).update(instance, validated_data)
        if object_permission:
            self.save_object_permission(instance, object_permission, False)
        return instance

    def save_object_permission(self, instance, object_permission, created):
        if created:
            user_object_permissions = object_permission.get('user_object_permissions', [])
            group_object_permissions = object_permission.get('group_object_permissions', None)

            member = self.context['request'].user.member
            user_object_permissions += [{'member': member, 'permission': p}
                                        for p in get_owner_default_permissions(instance)]

            assign_perms_from_list(instance,
                                   user_object_permissions=user_object_permissions,
                                   group_object_permissions=group_object_permissions)

        else:
            user_object_permissions = object_permission.get('user_object_permissions', None)
            group_object_permissions = object_permission.get('group_object_permissions', None)
            assign_perms_from_list(instance, user_object_permissions=user_object_permissions,
                                   group_object_permissions=group_object_permissions)
