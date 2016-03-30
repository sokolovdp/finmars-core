from __future__ import unicode_literals

from django.contrib import admin

from poms.audit.admin import HistoricalAdmin
from poms.u2u_messages.models import Thread, Message, DirectMessage


class ThreadAdmin(HistoricalAdmin):
    model = Thread
    list_display = ['id', 'subject', 'master_user']


admin.site.register(Thread, ThreadAdmin)


class MessageAdmin(HistoricalAdmin):
    model = Message
    list_display = ['id', 'thread', 'create_date', 'sender', 'short_text']


admin.site.register(Message, MessageAdmin)


class DirectMessageAdmin(HistoricalAdmin):
    model = DirectMessage
    list_display = ['id', 'create_date', 'recipient', 'sender', 'short_text']


admin.site.register(DirectMessage, DirectMessageAdmin)
