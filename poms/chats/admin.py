from __future__ import unicode_literals

from django.contrib import admin

from poms.audit.admin import HistoricalAdmin
from poms.chats.models import Thread, Message, DirectMessage


class ThreadAdmin(HistoricalAdmin):
    model = Thread
    list_display = ['id', 'master_user', 'create_date', 'subject', 'status', 'status_date']
    date_hierarchy = 'create_date'


admin.site.register(Thread, ThreadAdmin)


class MessageAdmin(HistoricalAdmin):
    model = Message
    list_display = ['id', 'thread', 'create_date', 'sender', 'short_text']
    date_hierarchy = 'create_date'


admin.site.register(Message, MessageAdmin)


class DirectMessageAdmin(HistoricalAdmin):
    model = DirectMessage
    list_display = ['id', 'create_date', 'recipient', 'sender', 'short_text']
    date_hierarchy = 'create_date'


admin.site.register(DirectMessage, DirectMessageAdmin)
