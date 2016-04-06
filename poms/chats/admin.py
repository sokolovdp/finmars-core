from __future__ import unicode_literals

from django.contrib import admin

from poms.audit.admin import HistoricalAdmin
from poms.chats.models import Thread, Message, DirectMessage, ThreadStatus
from poms.users.obj_perms.api import register_admin


class ThreadStatusAdmin(HistoricalAdmin):
    model = ThreadStatus
    list_display = ['id', 'master_user', 'name', 'is_closed']
    raw_id_fields = ['master_user']


admin.site.register(ThreadStatus, ThreadStatusAdmin)


class MessageInline(admin.StackedInline):
    model = Message
    list_select_related = ['sender']
    raw_id_fields = ['sender']
    ordering = ['created']
    extra = 0


class ThreadAdmin(HistoricalAdmin):
    model = Thread
    list_select_related = ['master_user', 'status']
    list_display = ['id', 'master_user', 'modified', 'subject', 'status']
    date_hierarchy = 'modified'
    ordering = ['modified']
    raw_id_fields = ['master_user', 'status']
    inlines = [MessageInline]


admin.site.register(Thread, ThreadAdmin)


class MessageAdmin(HistoricalAdmin):
    model = Message
    list_display = ['id', 'modified', 'thread', 'sender', 'short_text']
    list_select_related = ['thread', 'sender']
    date_hierarchy = 'modified'
    raw_id_fields = ['thread', 'sender']


admin.site.register(Message, MessageAdmin)


class DirectMessageAdmin(HistoricalAdmin):
    model = DirectMessage
    list_display = ['id', 'modified', 'recipient', 'sender', 'short_text']
    list_select_related = ['recipient', 'sender']
    date_hierarchy = 'modified'
    raw_id_fields = ['recipient', 'sender']


admin.site.register(DirectMessage, DirectMessageAdmin)


register_admin(Thread)

