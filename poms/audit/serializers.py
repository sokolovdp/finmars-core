from __future__ import unicode_literals

from collections import OrderedDict

import six
from rest_framework import serializers

from poms.audit.fields import ObjectHistoryContentTypeField
from poms.audit.models import AuthLogEntry, ObjectHistory4Entry
from poms.common.fields import DateTimeTzAwareField
from poms.common.middleware import get_city_by_ip
from poms.users.serializers import MemberMiniSerializer


class AuthLogEntrySerializer(serializers.ModelSerializer):
    date = DateTimeTzAwareField()
    user_location = serializers.SerializerMethodField()

    class Meta:
        model = AuthLogEntry
        fields = ('url', 'id', 'date', 'user_ip', 'user_agent', 'human_user_agent', 'is_success', 'user_location',)

    def get_user_location(self, instance):
        loc = get_city_by_ip(instance.user_ip)
        return OrderedDict(sorted(six.iteritems(loc))) if loc else None


class ObjectHistory4EntrySerializer(serializers.ModelSerializer):
    member = MemberMiniSerializer(read_only=True)
    actor_content_type = ObjectHistoryContentTypeField()
    content_type = ObjectHistoryContentTypeField()
    value_content_type = ObjectHistoryContentTypeField()
    old_value_content_type = ObjectHistoryContentTypeField()
    message = serializers.CharField(read_only=True)

    class Meta:
        model = ObjectHistory4Entry
        fields = ('url', 'id', 'member', 'group_id', 'created',
                  'actor_content_type', 'actor_content_type_repr', 'actor_object_id', 'actor_object_repr',
                  'action_flag',
                  'content_type', 'content_type_repr', 'object_id', 'object_repr',
                  'field_name', 'field_name_repr',
                  'value', 'value_repr', 'value_content_type', 'value_content_type_repr', 'value_object_id',
                  'old_value', 'old_value_repr', 'old_value_content_type', 'old_value_content_type_repr',
                  'old_value_object_id',
                  'message')
