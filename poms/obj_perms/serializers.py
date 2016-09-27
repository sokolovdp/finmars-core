from __future__ import unicode_literals

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from poms.common.serializers import ReadonlyModelSerializer
from poms.obj_perms.fields import PermissionField, GrantedPermissionField
from poms.obj_perms.utils import has_view_perms, get_all_perms, assign_perms2, has_manage_perm
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


class BulkObjectPermission(object):
    def __init__(self, content_objects=None, user_object_permissions=None, group_object_permissions=None, success=None):
        self.content_objects = content_objects or []
        self.user_object_permissions = user_object_permissions or []
        self.group_object_permissions = group_object_permissions or []
        self.success = success or {}


class AbstractBulkObjectPermissionSerializer(serializers.Serializer):
    user_object_permissions = UserObjectPermissionSerializer(many=True, required=False, allow_null=True)
    group_object_permissions = GroupObjectPermissionSerializer(many=True, required=False, allow_null=True)
    success = serializers.ReadOnlyField()

    def create(self, validated_data):
        ret = BulkObjectPermission(**validated_data)

        member = self.context['request'].user.member
        for content_object in ret.content_objects:
            if has_manage_perm(member, content_object):
                ret.success[content_object.id] = True
                assign_perms2(content_object, user_perms=ret.user_object_permissions,
                              group_perms=ret.group_object_permissions)
            else:
                ret.success[content_object.id] = False

        return ret

    def update(self, instance, validated_data):
        raise PermissionDenied()


class ModelWithObjectPermissionSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        show_object_permissions = kwargs.pop('show_object_permissions', False)
        super(ModelWithObjectPermissionSerializer, self).__init__(*args, **kwargs)

        self.fields['display_name'] = serializers.SerializerMethodField()
        self.fields['granted_permissions'] = GrantedPermissionField()

        # member = self.context['request'].user.member
        # if member.is_superuser and show_object_permissions:
        # if show_object_permissions:
        #     self.fields['user_object_permissions'] = UserObjectPermissionSerializer(
        #         many=True, required=False, allow_null=True)
        #     self.fields['group_object_permissions'] = GroupObjectPermissionSerializer(
        #         many=True, required=False, allow_null=True)
        self.fields['user_object_permissions'] = UserObjectPermissionSerializer(
            many=True, required=False, allow_null=True)
        self.fields['group_object_permissions'] = GroupObjectPermissionSerializer(
            many=True, required=False, allow_null=True)

    def get_display_name(self, instance):
        member = self.context['request'].user.member
        if has_view_perms(member, instance):
            return getattr(instance, 'name', None)
        else:
            return getattr(instance, 'public_name', None)

    # def to_representation(self, instance):
    #     member = self.context['request'].user.member
    #     if not has_view_perms(member, instance):
    #         ret = OrderedDict()
    #         fields = self._readable_fields
    #         for field in fields:
    #             if field.field_name not in ['url', 'id', 'public_name', 'granted_permissions']:
    #                 continue
    #             try:
    #                 attribute = field.get_attribute(instance)
    #             except SkipField:
    #                 continue
    #             if attribute is None:
    #                 ret[field.field_name] = None
    #             else:
    #                 ret[field.field_name] = field.to_representation(attribute)
    #         return ret
    #     return super(ModelWithObjectPermissionSerializer, self).to_representation(instance)
    def to_representation(self, instance):
        ret = super(ModelWithObjectPermissionSerializer, self).to_representation(instance)
        member = self.context['request'].user.member
        if not has_view_perms(member, instance):
            for k in [ret.keys()]:
                if k not in ['url', 'id', 'public_name', 'display_name', 'granted_permissions']:
                    ret.pop(k)
        if not has_manage_perm(member, instance):
            for k in [ret.keys()]:
                if k in ['user_object_permissions', 'group_object_permissions']:
                    ret.pop(k)
        return ret

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
        member = self.context['request'].user.member
        member_perms = [{'member': member, 'permission': p,} for p in get_all_perms(instance)]

        if created:
            if user_object_permissions:
                user_object_permissions = [uop for uop in user_object_permissions if uop['member'].id != member.id]
            else:
                user_object_permissions = []
            user_object_permissions += member_perms
            assign_perms2(instance, user_perms=user_object_permissions, group_perms=group_object_permissions)
        else:
            if has_manage_perm(member, instance):
                assign_perms2(instance, user_perms=user_object_permissions, group_perms=group_object_permissions)


class ReadonlyModelWithObjectPermissionSerializer(ReadonlyModelSerializer):
    def __init__(self, *args, **kwargs):
        fields = kwargs.get('fields', None)
        if fields is None:
            fields = ['id', 'user_code', 'name', 'short_name', 'public_name']
            kwargs['fields'] = fields
        super(ReadonlyModelWithObjectPermissionSerializer, self).__init__(*args, **kwargs)

        self.fields['display_name'] = serializers.SerializerMethodField()
        self.fields['granted_permissions'] = GrantedPermissionField()

    def get_display_name(self, instance):
        member = self.context['request'].user.member
        if has_view_perms(member, instance):
            return getattr(instance, 'name', None)
        else:
            return getattr(instance, 'public_name', None)

    def to_representation(self, instance):
        ret = super(ReadonlyModelWithObjectPermissionSerializer, self).to_representation(instance)
        member = self.context['request'].user.member
        if not has_view_perms(member, instance):
            for k in [ret.keys()]:
                if k not in ['id', 'public_name', 'display_name', 'granted_permissions']:
                    ret.pop(k)
        return ret
