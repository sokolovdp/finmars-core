from __future__ import unicode_literals

from rest_framework import serializers

from poms.chats.fields import ThreadField, ThreadStatusField
from poms.chats.models import Thread, Message, DirectMessage, ThreadStatus
from poms.obj_perms.fields import GrantedPermissionField
from poms.obj_perms.serializers import UserObjectPermissionSerializer, GroupObjectPermissionSerializer
from poms.obj_perms.utils import assign_perms_to_new_obj
from poms.users.fields import MasterUserField, MemberField, HiddenMemberField, GroupField
from poms.users.utils import get_member


class ThreadStatusSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='chatthreadstatus-detail')
    master_user = MasterUserField()

    class Meta:
        model = ThreadStatus
        fields = ['url', 'id', 'master_user', 'name', 'is_closed']


class ThreadSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='chatthread-detail')
    master_user = MasterUserField()
    status = ThreadStatusField()
    granted_permissions = GrantedPermissionField()

    # user_object_permissions = UserObjectPermissionSerializer(many=True, read_only=True)
    # group_object_permissions = GroupObjectPermissionSerializer(many=True, read_only=True)

    members = MemberField(many=True, write_only=True)
    groups = GroupField(many=True, write_only=True)

    # permissions = PermissionField(many=True, write_only=True)

    class Meta:
        model = Thread
        fields = ['url', 'id', 'master_user', 'created', 'modified', 'subject', 'status',
                  'granted_permissions',
                  # 'user_object_permissions', 'group_object_permissions',
                  'members', 'groups']
        read_only_fields = ['created', 'modified']

    def create(self, validated_data):
        members = validated_data.pop('members', None)
        groups = validated_data.pop('groups', None)
        permissions = validated_data.pop('permissions', None)

        instance = super(ThreadSerializer, self).create(validated_data)

        member = get_member(self.context['request'])
        owner_permission_set = ['view_thread', 'change_thread', 'manage_thread', 'delete_thread']
        member_permission_set = ['view_thread']
        assign_perms_to_new_obj(obj=instance,
                                owner=member, owner_perms=owner_permission_set,
                                members=members, groups=groups,
                                perms=member_permission_set)

        return instance


class MessageSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='chatmessage-detail')
    thread = ThreadField()
    sender = HiddenMemberField()

    class Meta:
        model = Message
        fields = ['url', 'id', 'thread', 'sender', 'created', 'modified', 'text']
        read_only_fields = ['created', 'modified']


class DirectMessageSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='chatdirectmessage-detail')

    class Meta:
        model = DirectMessage
        fields = ['url', 'id', 'recipient', 'sender', 'created', 'modified', 'text']
        read_only_fields = ['created', 'modified']
