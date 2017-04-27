from __future__ import unicode_literals

from rest_framework import serializers

from poms.audit.fields import ObjectHistoryContentTypeField
from poms.audit.models import AuthLogEntry, ObjectHistory4Entry
from poms.common.fields import DateTimeTzAwareField
from poms.common.middleware import get_city_by_ip
from poms.common.serializers import ContentTypeSerializer
from poms.users.serializers import MemberViewSerializer


class AuthLogEntrySerializer(serializers.ModelSerializer):
    date = DateTimeTzAwareField()
    user_location = serializers.SerializerMethodField()

    class Meta:
        model = AuthLogEntry
        fields = ('id', 'date', 'user_ip', 'user_agent', 'human_user_agent', 'is_success', 'user_location',)

    def get_user_location(self, instance):
        loc = get_city_by_ip(instance.user_ip)
        return loc


class ObjectHistory4EntrySerializer(serializers.ModelSerializer):
    member = MemberViewSerializer(read_only=True)
    created = DateTimeTzAwareField(read_only=True)
    actor_content_type = ObjectHistoryContentTypeField()
    content_type = ObjectHistoryContentTypeField()
    value_content_type = ObjectHistoryContentTypeField()
    old_value_content_type = ObjectHistoryContentTypeField()
    message = serializers.ReadOnlyField()

    actor_content_type_object = ContentTypeSerializer(source='actor_content_type', read_only=True)
    content_type_object = ContentTypeSerializer(source='content_type', read_only=True)
    value_content_type_object = ContentTypeSerializer(source='value_content_type', read_only=True)
    old_value_content_type_object = ContentTypeSerializer(source='old_value_content_type', read_only=True)

    class Meta:
        model = ObjectHistory4Entry
        fields = [
            'id', 'member', 'group_id', 'created', 'action_flag',
            'actor_content_type', 'actor_content_type_repr', 'actor_object_id', 'actor_object_repr',
            'content_type', 'content_type_repr', 'object_id', 'object_repr',
            'field_name', 'field_name_repr',
            'value', 'value_content_type', 'value_content_type_repr', 'value_object_id',
            'old_value', 'old_value_content_type', 'old_value_content_type_repr', 'old_value_object_id',
            'message',
            'actor_content_type_object', 'content_type_object', 'value_content_type_object',
            'old_value_content_type_object',
        ]
        read_only_fields = fields
