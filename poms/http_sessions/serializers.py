from __future__ import unicode_literals

from django.conf import settings
from rest_framework import serializers

from poms.http_sessions.models import Session


class SessionSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(lookup_field='id', view_name='session-detail')
    is_current = serializers.SerializerMethodField()

    class Meta:
        model = Session
        fields = ['url', 'id', 'user_ip', 'user_agent', 'is_current']

    def get_is_current(self, instance):
        request = self.context['request']
        session_key = request.COOKIES.get(settings.SESSION_COOKIE_NAME)
        return instance.session_key == session_key
