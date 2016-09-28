from __future__ import unicode_literals

from rest_framework import serializers

from poms.chats.fields import ThreadField, ThreadGroupField, ThreadGroupDefault
from poms.chats.models import Thread, Message, DirectMessage, ThreadGroup
from poms.common.fields import DateTimeTzAwareField
from poms.common.serializers import ReadonlyModelWithNameSerializer
from poms.obj_perms.serializers import ModelWithObjectPermissionSerializer, \
    ReadonlyNamedModelWithObjectPermissionSerializer
from poms.tags.fields import TagField
from poms.users.fields import MasterUserField, HiddenMemberField, MemberField
from poms.users.serializers import MemberMiniSerializer


class ThreadGroupSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='chatthreadgroup-detail')
    master_user = MasterUserField()
    tags = TagField(many=True, required=False, allow_null=True)
    tags_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='tags', many=True)

    class Meta:
        model = ThreadGroup
        fields = ['url', 'id', 'master_user', 'name', 'is_deleted', 'tags', 'tags_object']


class MessageSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='chatmessage-detail')
    thread = ThreadField()
    sender = HiddenMemberField()
    created = DateTimeTzAwareField(read_only=True)
    modified = DateTimeTzAwareField(read_only=True)
    sender_object = MemberMiniSerializer(read_only=True, source='sender')

    class Meta:
        model = Message
        fields = ['url', 'id', 'thread', 'sender', 'created', 'modified', 'text', 'sender_object']
        read_only_fields = ['created', 'modified']


class ThreadSerializer(ModelWithObjectPermissionSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='chatthread-detail')
    master_user = MasterUserField()
    thread_group = ThreadGroupField(default=ThreadGroupDefault())
    thread_group_object = ReadonlyModelWithNameSerializer(source='thread_group')
    created = DateTimeTzAwareField(read_only=True)
    modified = DateTimeTzAwareField(read_only=True)
    closed = DateTimeTzAwareField(read_only=True)
    tags = TagField(many=True, required=False, allow_null=True)
    tags_object = ReadonlyNamedModelWithObjectPermissionSerializer(source='tags', many=True)
    messages_count = serializers.IntegerField(read_only=True)
    messages_last = MessageSerializer(read_only=True, many=True)

    class Meta:
        model = Thread
        fields = [
            'url', 'id', 'master_user', 'thread_group', 'thread_group_object',
            'created', 'modified', 'closed', 'subject', 'is_deleted',
            'tags', 'tags_object', 'messages_count', 'messages_last'
        ]
        read_only_fields = ['created', 'modified', 'closed']


# class ThreadBulkObjectPermissionSerializer(AbstractBulkObjectPermissionSerializer):
#     content_objects = ThreadField(many=True, allow_null=False, allow_empty=False)
#
#     class Meta:
#         model = Thread


class DirectMessageSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='chatdirectmessage-detail')
    sender = HiddenMemberField()
    recipient = MemberField()
    created = DateTimeTzAwareField(read_only=True)
    modified = DateTimeTzAwareField(read_only=True)

    sender_object = MemberMiniSerializer(read_only=True, source='sender')
    recipient_object = MemberMiniSerializer(read_only=True, source='sender')

    class Meta:
        model = DirectMessage
        fields = ['url', 'id', 'sender', 'recipient', 'created', 'modified', 'text', 'sender_object',
                  'recipient_object']
        read_only_fields = ['created', 'modified']
