from __future__ import unicode_literals

from collections import OrderedDict

import six
from django.conf import settings
from rest_framework import serializers

from poms.common.middleware import get_city_by_ip
from poms.http_sessions.models import Session


class SessionSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(lookup_field='id', view_name='session-detail')
    is_current = serializers.SerializerMethodField()
    user_location = serializers.SerializerMethodField()

    class Meta:
        model = Session
        fields = ('url', 'id', 'user_ip', 'user_agent', 'is_current', 'user_location',)

    def get_is_current(self, instance):
        request = self.context['request']
        session_key = request.COOKIES.get(settings.SESSION_COOKIE_NAME)
        return instance.session_key == session_key

    def get_user_location(self, instance):
        loc = get_city_by_ip(instance.user_ip)
        return OrderedDict(sorted(six.iteritems(loc))) if loc else None
