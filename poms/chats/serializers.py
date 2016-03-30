from __future__ import unicode_literals

from rest_framework import serializers

from poms.chats.fields import ThreadField
from poms.chats.models import Thread, Message, DirectMessage, ThreadStatus
from poms.users.fields import MasterUserField


class ThreadStatusSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='chatthreadstatus-detail')
    master_user = MasterUserField()

    class Meta:
        model = ThreadStatus
        fields = ['url', 'id', 'master_user', 'name', 'is_closed']


class ThreadSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='chatthread-detail')
    master_user = MasterUserField()

    class Meta:
        model = Thread
        fields = ['url', 'id', 'master_user', 'create_date', 'subject', 'status', 'status_date']
        read_only_fields = ['create_date', 'status_date']


class MessageSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='chatmessage-detail')
    thread = ThreadField()

    class Meta:
        model = Message
        fields = ['url', 'id', 'thread', 'sender', 'create_date', 'text']
        read_only_fields = ['create_date']


class DirectMessageSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='chatdirectmessage-detail')

    class Meta:
        model = DirectMessage
        fields = ['url', 'id', 'recipient', 'sender', 'create_date', 'text']
        read_only_fields = ['create_date']
