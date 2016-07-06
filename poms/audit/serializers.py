from __future__ import unicode_literals

import json
from collections import OrderedDict

import six
from django.utils import timezone
from django.utils.encoding import force_text
from django.utils.text import get_text_list
from django.utils.translation import ugettext as _
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
    data = serializers.SerializerMethodField()

    class Meta:
        model = Version
        fields = ('url', 'id', 'date', 'user', 'username', 'comment', 'object', 'data')

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
        changes = value.revision.comment
        if changes and changes.startswith('['):
            try:
                changes = json.loads(changes)
            except ValueError:
                return changes
            messages = []
            for m in changes:
                action = m.get('action', None)
                object_repr = m.get('object_repr', '')
                name = m.get('object_name', m.get('content_type', ''))
                message = None
                if action == 'add':
                    message = _('Added %(name)s "%(object)s".') % {
                        'name': name,
                        'object': object_repr
                    }
                elif action == 'change':
                    fields = m.get('fields', [])
                    fields_repr = []
                    for f in fields:
                        if isinstance(f, six.string_types):
                            fields_repr.append('"%s"' % f)
                        else:
                            fields_repr.append('"%s"' % f['verbose_name'])
                    if fields_repr:
                        fields_repr.sort()
                        message = _('Changed %(list)s for %(name)s "%(object)s".') % {
                            'list': get_text_list(fields_repr, _('and')),
                            'name': name,
                            'object': object_repr
                        }
                    else:
                        message = _('Changed %(name)s "%(object)s".') % {
                            'name': name,
                            'object': object_repr
                        }
                elif action == 'delete':
                    message = _('Deleted %(name)s "%(object)s".') % {
                        'name': name,
                        'object': object_repr
                    }
                if message:
                    messages.append(message)
            return ' '.join(messages)
        return changes

    def get_object(self, value):
        return getattr(value, 'object_json', None)

    def get_data(self, value):
        changes = value.revision.comment
        if changes and changes.startswith('['):
            try:
                return json.loads(changes)
            except ValueError:
                return None
        return None
