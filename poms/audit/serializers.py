from __future__ import unicode_literals

from rest_framework import serializers
from reversion.models import Version

from poms.audit.models import AuthLogEntry


class AuthLogEntrySerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='authlog-detail')

    class Meta:
        model = AuthLogEntry
        fields = ['url', 'date', 'user_ip', 'user_agent', 'is_success']


class VersionSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    comment = serializers.SerializerMethodField()
    object = serializers.SerializerMethodField()

    class Meta:
        model = Version
        fields = ['id', 'date', 'user', 'username', 'comment', 'object']

    def get_date(self, value):
        return value.revision.date_created

    def get_user(self, value):
        return value.revision.user_id

    def get_username(self, value):
        info = getattr(value.revision, 'info', None)
        return getattr(info, 'username', None)

    def get_comment(self, value):
        return value.revision.comment

    def get_object(self, value):
        return getattr(value, 'object_json', None)
