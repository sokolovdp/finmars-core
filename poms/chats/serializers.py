from __future__ import unicode_literals

from rest_framework import serializers

from poms.chats.fields import ThreadField, ThreadGroupField, ThreadGroupDefault
from poms.chats.models import Thread, Message, DirectMessage, ThreadGroup
from poms.common.fields import DateTimeTzAwareField
from poms.obj_perms.serializers import ModelWithObjectPermissionSerializer
from poms.tags.serializers import ModelWithTagSerializer
from poms.users.fields import MasterUserField, HiddenMemberField, MemberField
from poms.users.serializers import MemberViewSerializer


class ThreadGroupSerializer(ModelWithTagSerializer):
    # url = serializers.HyperlinkedIdentityField(view_name='chatthreadgroup-detail')
    master_user = MasterUserField()

    # tags = TagField(many=True, required=False, allow_null=True)
    # tags_object = TagViewSerializer(source='tags', many=True, read_only=True)

    class Meta:
        model = ThreadGroup
        fields = [
            'url', 'id', 'master_user', 'name', 'is_deleted',
            # 'tags', 'tags_object'
        ]


class ThreadGroupViewSerializer(serializers.ModelSerializer):
    # url = serializers.HyperlinkedIdentityField(view_name='chatthreadgroup-detail')

    class Meta:
        model = ThreadGroup
        fields = ['url', 'id', 'name', 'is_deleted', ]


class MessageSerializer(serializers.ModelSerializer):
    # url = serializers.HyperlinkedIdentityField(view_name='chatmessage-detail')
    thread = ThreadField()
    sender = HiddenMemberField()
    created = DateTimeTzAwareField(read_only=True)
    modified = DateTimeTzAwareField(read_only=True)
    sender_object = MemberViewSerializer(source='sender', read_only=True)

    class Meta:
        model = Message
        fields = ['url', 'id', 'thread', 'sender', 'created', 'modified', 'text', 'sender_object']
        read_only_fields = ['created', 'modified']


class ThreadSerializer(ModelWithObjectPermissionSerializer, ModelWithTagSerializer):
    # url = serializers.HyperlinkedIdentityField(view_name='chatthread-detail')
    master_user = MasterUserField()
    thread_group = ThreadGroupField(default=ThreadGroupDefault())
    thread_group_object = ThreadGroupViewSerializer(source='thread_group', read_only=True)
    is_closed = serializers.BooleanField(read_only=True)
    created = DateTimeTzAwareField(read_only=True)
    modified = DateTimeTzAwareField(read_only=True)
    closed = DateTimeTzAwareField(read_only=True)
    # tags = TagField(many=True, required=False, allow_null=True)
    # tags_object = TagViewSerializer(source='tags', many=True, read_only=True)
    messages_count = serializers.IntegerField(read_only=True)
    messages_last = MessageSerializer(read_only=True, many=True)

    class Meta:
        model = Thread
        fields = [
            'url', 'id', 'master_user', 'thread_group', 'thread_group_object',
            'subject', 'is_closed', 'is_deleted', 'created', 'modified', 'closed',
            'messages_count', 'messages_last'
            # 'tags', 'tags_object',
        ]
        read_only_fields = ['is_closed', 'created', 'modified', 'closed']


# class ThreadBulkObjectPermissionSerializer(AbstractBulkObjectPermissionSerializer):
#     content_objects = ThreadField(many=True, allow_null=False, allow_empty=False)
#
#     class Meta:
#         model = Thread


class DirectMessageSerializer(serializers.ModelSerializer):
    # url = serializers.HyperlinkedIdentityField(view_name='chatdirectmessage-detail')
    sender = HiddenMemberField()
    recipient = MemberField()
    created = DateTimeTzAwareField(read_only=True)
    modified = DateTimeTzAwareField(read_only=True)

    sender_object = MemberViewSerializer(source='sender', read_only=True)
    recipient_object = MemberViewSerializer(source='recipient', read_only=True)

    class Meta:
        model = DirectMessage
        fields = ['url', 'id', 'sender', 'sender_object', 'recipient', 'recipient_object', 'created', 'modified',
                  'text', ]
        read_only_fields = ['created', 'modified']
