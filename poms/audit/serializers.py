from __future__ import unicode_literals

from django.utils.encoding import force_text
from notifications.models import Notification
from rest_framework import serializers

from poms.audit.models import AuthLog


class AuthLogSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='authlog-detail')

    class Meta:
        model = AuthLog
        fields = ['url', 'date', 'user_ip', 'user_agent', 'is_success']


class NotificationSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='notification-detail')
    actor = serializers.SerializerMethodField()
    target = serializers.SerializerMethodField()
    target_content_type = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['url', 'id', 'actor', 'verb', 'description', 'target', 'target_content_type', 'target_object_id',
                  'level','timestamp', 'unread']

    def get_actor(self, value):
        return int(value.actor_object_id)

    def get_target(self, value):
        return '%s' % value.target

    def get_target_content_type(self, value):
        if value.target_content_type:
            # return '%s.%s' % value.target_content_type.natural_key()
            return '%s' % value.target_content_type
        else:
            return None
