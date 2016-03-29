from __future__ import unicode_literals

from rest_framework import serializers

from poms.u2u_messages.fields import ChannelField
from poms.u2u_messages.models import Channel, Message, Member
from poms.users.fields import MasterUserField


class MemberSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='u2umember-detail')
    channel = ChannelField()

    class Meta:
        model = Member
        fields = ['url', 'id', 'channel', 'user', 'join_date']


class ChannelSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='u2uchannel-detail')
    master_user = MasterUserField()
    # users = MemberSerializer(many=True, read_only=True)

    class Meta:
        model = Channel
        fields = ['url', 'id', 'master_user', 'create_date', 'name', 'users', 'members']


class MessageSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='u2umessage-detail')
    channel = ChannelField()

    class Meta:
        model = Message
        fields = ['url', 'id', 'channel', 'sender', 'create_date', 'text']
