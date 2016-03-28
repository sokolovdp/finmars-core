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
    actor_repr = serializers.SerializerMethodField()
    target = serializers.SerializerMethodField()
    target_type = serializers.SerializerMethodField()
    target_repr = serializers.SerializerMethodField()
    action_object = serializers.SerializerMethodField()
    action_object_type = serializers.SerializerMethodField()
    action_object_repr = serializers.SerializerMethodField()
    data = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['url', 'id', 'level', 'create_date', 'read_date',
                  'type',
                  'message', 'timesince',
                  'actor', 'actor_type', 'actor_repr',
                  'verb',
                  'target', 'target_type', 'target_repr',
                  'action_object', 'action_object_type', 'action_object_repr',
                  'data']

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

    def get_actor_repr(self, value):
        if value.actor_object_id:
            return '%s' % value.actor
        return None

    def get_target(self, value):
        if value.target_object_id:
            return int(value.target_object_id)
        return None

    def get_target_type(self, value):
        if value.target_content_type_id:
            return '%s' % value.target_content_type.model
        return None

    def get_target_repr(self, value):
        if value.target_object_id:
            return '%s' % value.target
        return None

    def get_action_object(self, value):
        if value.action_object_object_id:
            return int(value.action_object_object_id)
        return None

    def get_action_object_type(self, value):
        if value.action_object_content_type_id:
            return '%s' % value.action_object_content_type.model
        return None

    def get_action_object_repr(self, value):
        if value.action_object_object_id:
            return '%s' % value.action_object
        return None

    def get_data(self, value):
        if value.data:
            return json.loads(value.data)
        return None
