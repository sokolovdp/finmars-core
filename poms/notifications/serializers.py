from __future__ import unicode_literals

import json

from django.utils.encoding import force_text
from rest_framework import serializers

from poms.notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='notification-detail')
    message = serializers.SerializerMethodField()
    actor = serializers.SerializerMethodField()
    actor_type = serializers.SerializerMethodField()
    actor_name = serializers.SerializerMethodField()
    target = serializers.SerializerMethodField()
    target_type = serializers.SerializerMethodField()
    target_name = serializers.SerializerMethodField()
    data = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['url', 'id', 'level', 'create_date', 'read_date', 'message', 'timesince',
                  'actor', 'actor_type', 'actor_name',
                  'verb',
                  'target', 'target_type', 'target_name',
                  'description', 'data']
        # read_only_fields = set(fields) - {'read_date'}

    def get_message(self, value):
        return force_text(value)

    def get_actor(self, value):
        if value.actor_object_id:
            return int(value.actor_object_id)
        return None

    def get_actor_type(self, value):
        if value.actor_content_type:
            return '%s' % value.actor_content_type.model
        return None

    def get_actor_name(self, value):
        if value.actor:
            return '%s' % value.actor
        return None

    def get_target(self, value):
        if value.target_object_id:
            return int(value.target_object_id)
        return None

    def get_target_type(self, value):
        if value.target_content_type:
            return '%s' % value.target_content_type.model
        return None

    def get_target_name(self, value):
        if value.target:
            return '%s' % value.target
        return None

    def get_data(self, value):
        if value.data:
            return json.loads(value.data)
        return None
