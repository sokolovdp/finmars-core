from __future__ import unicode_literals

import json
from collections import OrderedDict

import six
from django.utils import timezone
from rest_framework import serializers

from poms.audit.fields import ObjectHistoryContentTypeField
from poms.audit.history import make_comment
from poms.audit.models import AuthLogEntry, ObjectHistoryEntry
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


# class VersionSerializer(serializers.ModelSerializer):
#     url = serializers.SerializerMethodField()
#     date = serializers.SerializerMethodField()
#     member = serializers.SerializerMethodField()
#     comment = serializers.SerializerMethodField()
#     # object = serializers.SerializerMethodField()
#     object_id = serializers.SerializerMethodField()
#     object_repr = serializers.SerializerMethodField()
#
#     # data = serializers.SerializerMethodField()
#
#     class Meta:
#         model = Version
#         fields = ('url', 'id', 'date', 'member', 'comment', 'object_id', 'object_repr')
#
#     def get_url(self, value):
#         request = self.context['request']
#         return '%s?version_id=%s' % (request.build_absolute_uri(location=request.path), value.id)
#
#     def get_date(self, value):
#         return timezone.localtime(value.revision.date_created)
#
#     def get_member(self, value):
#         info = getattr(value.revision, 'info', None).first()
#         return info.member_id if info else None
#
#     def get_comment(self, value):
#         changes = value.revision.comment
#         return make_comment(changes)
#
#     # def get_object(self, value):
#     #     return getattr(value, 'object_json', None)
#
#     def get_object_id(self, value):
#         return int(value.object_id)
#
#     def get_object_repr(self, value):
#         return six.text_type(value._object_version.object)
#
#     def get_data(self, value):
#         changes = value.revision.comment
#         if changes and changes.startswith('{'):
#             try:
#                 return json.loads(changes)
#             except ValueError:
#                 return None
#         return None


class ObjectHistoryEntrySerializer(serializers.ModelSerializer):
    content_type = ObjectHistoryContentTypeField()
    comment = serializers.SerializerMethodField()
    message = serializers.SerializerMethodField()

    class Meta:
        model = ObjectHistoryEntry
        fields = ('url', 'id', 'member', 'created', 'action_flag', 'content_type', 'object_id', 'comment', 'message')

    def get_comment(self, value):
        return make_comment(value.message)

    def get_message(self, value):
        # if value.message:
        #     try:
        #         return json.loads(value.message)
        #     except ValueError:
        #         pass
        return None

# def audit_get_comment(changes):
#     if changes and changes.startswith('['):
#         try:
#             changes = json.loads(changes)
#         except ValueError:
#             return changes
#         messages = []
#         for m in changes:
#             action = m.get('action', None)
#             object_repr = m.get('object_repr', '')
#             name = m.get('object_name', m.get('content_type', ''))
#
#             if action == 'add':
#                 message = _('Added %(name)s "%(object)s".') % {
#                     'name': name,
#                     'object': object_repr
#                 }
#                 messages.append(message)
#
#             elif action == 'change':
#                 try:
#                     for f in m.get('fields', []):
#                         message = _(
#                             'Changed %(field)s for %(name)s "%(object)s" from %(old_value)s to %(new_value)s.') % {
#                                       'field': f['verbose_name'],
#                                       'name': name,
#                                       'object': object_repr,
#                                       'old_value': force_text(f['old_value']),
#                                       'new_value': force_text(f['new_value']),
#                                   }
#                         messages.append(message)
#                 except KeyError:
#                     pass
#
#                     # fields = m.get('fields', [])
#                     # fields_repr = []
#                     # for f in fields:
#                     #     if isinstance(f, six.string_types):
#                     #         fields_repr.append('"%s"' % f)
#                     #     else:
#                     #         fields_repr.append('"%s"' % f['verbose_name'])
#                     # if fields_repr:
#                     #     fields_repr.sort()
#                     #     message = _('Changed %(list)s for %(name)s "%(object)s".') % {
#                     #         'list': get_text_list(fields_repr, _('and')),
#                     #         'name': name,
#                     #         'object': object_repr
#                     #     }
#                     # else:
#                     #     message = _('Changed %(name)s "%(object)s".') % {
#                     #         'name': name,
#                     #         'object': object_repr
#                     #     }
#
#             elif action == 'delete':
#                 message = _('Deleted %(name)s "%(object)s".') % {
#                     'name': name,
#                     'object': object_repr
#                 }
#                 messages.append(message)
#         return ' '.join(messages)
#     return changes
