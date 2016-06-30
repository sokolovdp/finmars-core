from __future__ import unicode_literals

from collections import OrderedDict

import six
from django.utils import timezone
from rest_framework import serializers
from reversion.models import Version

from poms.audit.models import AuthLogEntry
from poms.common.fields import DateTimeTzAwareField
from poms.common.middleware import get_city_by_ip


class AuthLogEntrySerializer(serializers.ModelSerializer):
    date = DateTimeTzAwareField()
    user_location = serializers.SerializerMethodField()

    class Meta:
        model = AuthLogEntry
        fields = ('url', 'id', 'date', 'user_ip', 'user_agent', 'is_success', 'user_location',)

    def get_user_location(self, instance):
        loc = get_city_by_ip(instance.user_ip)
        return OrderedDict(sorted(six.iteritems(loc))) if loc else None


class VersionSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    comment = serializers.SerializerMethodField()
    object = serializers.SerializerMethodField()

    class Meta:
        model = Version
        fields = ('url', 'id', 'date', 'user', 'username', 'comment', 'object',)

    def get_url(self, value):
        request = self.context['request']
        return '%s?version_id=%s' % (request.build_absolute_uri(location=request.path), value.id)

    def get_date(self, value):
        return timezone.localtime(value.revision.date_created)

    def get_user(self, value):
        return value.revision.user_id

    def get_username(self, value):
        info = getattr(value.revision, 'info', None)
        if info is None:
            info = list(info.all())
            if len(info) > 0:
                info = info[0]
                return getattr(info, 'username', None)
        return None

    def get_comment(self, value):
        return value.revision.comment

    def get_object(self, value):
        return getattr(value, 'object_json', None)
