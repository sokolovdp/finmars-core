from __future__ import unicode_literals

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from poms.chats.fields import ThreadField, ThreadStatusField
from poms.chats.models import Thread, Message, DirectMessage, ThreadStatus
from poms.obj_perms.models import ThreadUserObjectPermission
from poms.users.fields import MasterUserField, MemberField, get_member, HiddenMemberField


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
    members = MemberField(many=True, write_only=True)

    class Meta:
        model = Thread
        fields = ['url', 'id', 'master_user', 'created', 'modified', 'subject', 'status', 'members']
        read_only_fields = ['created', 'modified']

    def create(self, validated_data):
        members = validated_data.pop('members', None)
        instance = super(ThreadSerializer, self).create(validated_data)

        owner_permission_set = ['view_thread', 'change_thread', 'manage_thread', 'delete_thread']
        member_permission_set = ['view_thread']

        request = self.context['request']
        member = get_member(request)
        ctype = ContentType.objects.get_for_model(Thread)
        permissions = list(Permission.objects.filter(content_type=ctype))

        object_permissions = []

        for p in permissions:
            if p.codename in owner_permission_set:
                object_permissions.append(
                    ThreadUserObjectPermission(content_object=instance, member=member, permission=p)
                )

        print('members: ', members)
        if members:
            for m in members:
                if m.id == member.id:
                    continue
                for p in permissions:
                    if p.codename in member_permission_set:
                        object_permissions.append(
                            ThreadUserObjectPermission(content_object=instance, member=m, permission=p)
                        )

        ThreadUserObjectPermission.objects.bulk_create(object_permissions)

        return instance


class MessageSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='chatmessage-detail')
    thread = ThreadField()
    sender = HiddenMemberField()

    class Meta:
        model = Message
        fields = ['url', 'id', 'thread', 'sender', 'created', 'modified', 'text']
        read_only_fields = ['created', 'modified']

        # def validate(self, attrs):
        #     request = self.context['request']
        #     attrs['sender'] = get_member(request)
        #     return attrs


class DirectMessageSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='chatdirectmessage-detail')

    class Meta:
        model = DirectMessage
        fields = ['url', 'id', 'recipient', 'sender', 'created', 'modified', 'text']
        read_only_fields = ['created', 'modified']
