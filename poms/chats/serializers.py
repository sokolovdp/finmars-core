from __future__ import unicode_literals

from rest_framework import serializers

from poms.chats.fields import ThreadField
from poms.chats.models import Thread, Message, DirectMessage
from poms.common.fields import DateTimeTzAwareField
from poms.obj_perms.serializers import ModelWithObjectPermissionSerializer
from poms.users.fields import MasterUserField, HiddenMemberField, MemberField


# class ThreadStatusSerializer(serializers.ModelSerializer):
#     url = serializers.HyperlinkedIdentityField(view_name='chatthreadstatus-detail')
#     master_user = MasterUserField()
#
#     class Meta:
#         model = ThreadStatus
#         fields = ['url', 'id', 'master_user', 'name', 'is_closed']


class ThreadSerializer(ModelWithObjectPermissionSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='chatthread-detail')
    master_user = MasterUserField()
    created = DateTimeTzAwareField(read_only=True)
    modified = DateTimeTzAwareField(read_only=True)
    closed = DateTimeTzAwareField(read_only=True)

    class Meta:
        model = Thread
        fields = ['url', 'id', 'master_user', 'created', 'modified', 'closed', 'subject',]
        read_only_fields = ['created', 'modified', 'closed']


class MessageSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='chatmessage-detail')
    thread = ThreadField()
    sender = HiddenMemberField()
    created = DateTimeTzAwareField(read_only=True)
    modified = DateTimeTzAwareField(read_only=True)

    class Meta:
        model = Message
        fields = ['url', 'id', 'thread', 'sender', 'created', 'modified', 'text']
        read_only_fields = ['created', 'modified']


class DirectMessageSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='chatdirectmessage-detail')
    sender = HiddenMemberField()
    recipient = MemberField()
    created = DateTimeTzAwareField(read_only=True)
    modified = DateTimeTzAwareField(read_only=True)

    class Meta:
        model = DirectMessage
        fields = ['url', 'id', 'sender', 'recipient', 'created', 'modified', 'text']
        read_only_fields = ['created', 'modified']
