from __future__ import unicode_literals

from rest_framework import serializers

from poms.chats.fields import ThreadField, ThreadStatusField
from poms.chats.models import Thread, Message, DirectMessage, ThreadStatus
from poms.obj_perms.serializers import ObjectPermissionSerializer, ModelWithObjectPermissionSerializer
from poms.users.fields import MasterUserField, HiddenMemberField, UserField, HiddenUserField


class ThreadStatusSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='chatthreadstatus-detail')
    master_user = MasterUserField()

    class Meta:
        model = ThreadStatus
        fields = ['url', 'id', 'master_user', 'name', 'is_closed']


class ThreadSerializer(ModelWithObjectPermissionSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='chatthread-detail')
    master_user = MasterUserField()
    status = ThreadStatusField()
    object_permission = ObjectPermissionSerializer()

    class Meta:
        model = Thread
        fields = ['url', 'id', 'master_user', 'created', 'modified', 'subject', 'status',
                  'object_permission']
        read_only_fields = ['created', 'modified']

        # def create(self, validated_data):
        #     members = validated_data.pop('members', None)
        #     groups = validated_data.pop('groups', None)
        #     permissions = validated_data.pop('permissions', None)
        #
        #     instance = super(ThreadSerializer, self).create(validated_data)
        #
        #     request = self.context['request']
        #     # member = get_member(request)
        #     member = request.user.member
        #
        #     owner_permission_set = ['view_thread', 'change_thread', 'manage_thread', 'delete_thread']
        #     member_permission_set = ['view_thread']
        #     assign_perms_to_new_obj(obj=instance,
        #                             owner=member, owner_perms=owner_permission_set,
        #                             members=members, groups=groups,
        #                             perms=member_permission_set)
        #
        #     return instance


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
    recipient = UserField()
    sender = HiddenUserField()

    class Meta:
        model = DirectMessage
        fields = ['url', 'id', 'recipient', 'sender', 'created', 'modified', 'text']
        read_only_fields = ['created', 'modified']
