from __future__ import unicode_literals

import six
from rest_framework import serializers

from poms.obj_perms.fields import PermissionField, GrantedPermissionField
from poms.obj_perms.utils import has_view_perms, get_all_perms, assign_perms2
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
    def __init__(self, *args, **kwargs):
        show_object_permissions = kwargs.pop('show_object_permissions', False)
        super(ModelWithObjectPermissionSerializer, self).__init__(*args, **kwargs)

        self.fields['display_name'] = serializers.SerializerMethodField()
        self.fields['granted_permissions'] = GrantedPermissionField()

        member = self.context['request'].user.member
        if member.is_superuser and show_object_permissions:
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
            for k in list(six.iterkeys(ret)):
                if k not in ['url', 'id', 'public_name', 'display_name', 'granted_permissions']:
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
        # if created:
        #         member = self.context['request'].user.member
        #         user_object_permissions = user_object_permissions or []
        #         user_object_permissions += [{'member': member, 'permission': p}
        #                                     for p in get_default_owner_permissions(instance)]
        #         assign_perms_from_list(instance,
        #                                user_object_permissions=user_object_permissions,
        #                                group_object_permissions=group_object_permissions)
        #
        #     else:
        #         assign_perms_from_list(instance,
        #                                user_object_permissions=user_object_permissions,
        #                                group_object_permissions=group_object_permissions)
        member = self.context['request'].user.member
        member_perms = [{'member': member, 'permission': p,} for p in get_all_perms(instance)]
        if member.is_superuser:
            if user_object_permissions:
                user_object_permissions = [uop for uop in user_object_permissions if uop['member'].id != member.id]
            else:
                user_object_permissions = []
            user_object_permissions += member_perms
            assign_perms2(instance, user_perms=user_object_permissions, group_perms=group_object_permissions)
        else:
            assign_perms2(instance, user_perms=member_perms)
