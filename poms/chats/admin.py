from __future__ import unicode_literals

from django.contrib import admin

from poms.audit.admin import HistoricalAdmin
from poms.chats.models import Thread, Message, DirectMessage, ThreadStatus


class ThreadStatusAdmin(HistoricalAdmin):
    model = ThreadStatus
    list_display = ['id', 'master_user', 'name', 'is_closed']
    raw_id_fields = ['master_user']


admin.site.register(ThreadStatus, ThreadStatusAdmin)


class MessageInline(admin.StackedInline):
    raw_id_fields = ['sender']
    model = Message
    extra = 1
    ordering = ['create_date']


class ThreadAdmin(HistoricalAdmin):
    model = Thread
    list_display = ['id', 'master_user', 'create_date', 'subject', 'status', 'status_date']
    date_hierarchy = 'create_date'
    list_select_related = ['status', 'master_user']
    raw_id_fields = ['master_user']
    inlines = [MessageInline]


admin.site.register(Thread, ThreadAdmin)


class MessageAdmin(HistoricalAdmin):
    model = Message
    list_display = ['id', 'thread', 'create_date', 'sender', 'short_text']
    list_select_related = ['thread', 'sender']
    date_hierarchy = 'create_date'
    raw_id_fields = ['thread', 'sender']


admin.site.register(Message, MessageAdmin)


class DirectMessageAdmin(HistoricalAdmin):
    model = DirectMessage
    list_display = ['id', 'create_date', 'recipient', 'sender', 'short_text']
    list_select_related = ['recipient', 'sender']
    date_hierarchy = 'create_date'
    raw_id_fields = ['recipient', 'sender']


admin.site.register(DirectMessage, DirectMessageAdmin)
