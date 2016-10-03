from __future__ import unicode_literals

from django.contrib import admin

from poms.audit.admin import HistoricalAdmin
from poms.chats.models import Thread, Message, DirectMessage, ThreadGroup
from poms.obj_perms.admin import UserObjectPermissionInline, \
    GroupObjectPermissionInline


class ThreadGroupAdmin(HistoricalAdmin):
    model = ThreadGroup
    list_display = ['id', 'master_user', 'name', 'is_deleted', ]
    list_select_related = ['master_user', ]
    ordering = ['master_user', 'name']
    search_fields = ['id', 'name']
    list_filter = ['is_deleted', ]
    raw_id_fields = ['master_user', ]
    inlines = [
        UserObjectPermissionInline,
        GroupObjectPermissionInline
    ]


admin.site.register(ThreadGroup, ThreadGroupAdmin)


class ThreadAdmin(HistoricalAdmin):
    model = Thread
    list_display = ['id', 'master_user', 'thread_group', 'subject', 'created', 'closed', 'is_deleted', ]
    list_select_related = ['master_user', 'thread_group', ]
    ordering = ['master_user', 'thread_group', 'subject']
    search_fields = ['id', 'subject']
    list_filter = ['created', 'closed', 'is_deleted', ]
    date_hierarchy = 'created'
    raw_id_fields = ['master_user', 'thread_group', ]
    inlines = [
        UserObjectPermissionInline,
        GroupObjectPermissionInline
    ]


admin.site.register(Thread, ThreadAdmin)


class MessageAdmin(HistoricalAdmin):
    model = Message
    list_display = ['id', 'master_user', 'thread', 'created', 'sender', 'short_text']
    list_select_related = ['thread', 'thread__master_user', 'sender']
    ordering = ['-created']
    search_fields = ['thread__id', 'thread__subject']
    date_hierarchy = 'created'
    raw_id_fields = ['thread', 'sender']

    def master_user(self, obj):
        return obj.thread.master_user

    master_user.admin_order_field = 'thread__master_user'


admin.site.register(Message, MessageAdmin)


class DirectMessageAdmin(HistoricalAdmin):
    model = DirectMessage
    list_display = ['id', 'created', 'sender', 'recipient', 'short_text']
    list_select_related = ['sender', 'recipient']
    ordering = ['-created']
    date_hierarchy = 'created'
    raw_id_fields = ['recipient', 'sender']


admin.site.register(DirectMessage, DirectMessageAdmin)
