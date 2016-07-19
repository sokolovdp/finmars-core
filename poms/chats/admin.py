from __future__ import unicode_literals

from django.contrib import admin

from poms.audit.admin import HistoricalAdmin
from poms.chats.models import Thread, Message, DirectMessage, ThreadGroup
from poms.obj_perms.admin import UserObjectPermissionInline, \
    GroupObjectPermissionInline


# class ThreadStatusAdmin(HistoricalAdmin):
#     model = ThreadStatus
#     list_display = ['id', 'master_user', 'name', 'is_closed']
#     raw_id_fields = ['master_user']
#
#
# admin.site.register(ThreadStatus, ThreadStatusAdmin)


# class MessageInline(admin.StackedInline):
#     model = Message
#     list_select_related = ['sender']
#     raw_id_fields = ['sender']
#     ordering = ['created']
#     extra = 0


class ThreadGroupAdmin(HistoricalAdmin):
    model = ThreadGroup
    list_display = ['id', 'master_user', 'name', ]
    list_select_related = ['master_user', ]
    raw_id_fields = ['master_user', ]
    search_fields = ['id', 'name']


admin.site.register(ThreadGroup, ThreadGroupAdmin)


class ThreadAdmin(HistoricalAdmin):
    model = Thread
    list_display = ['id', 'master_user', 'thread_group', 'subject', 'created', 'closed', ]
    list_select_related = ['master_user', 'thread_group', ]
    date_hierarchy = 'created'
    ordering = ['created']
    raw_id_fields = ['master_user', 'thread_group', ]
    # inlines = [MessageInline]
    search_fields = ['id', 'subject']
    inlines = [
        UserObjectPermissionInline,
        GroupObjectPermissionInline
    ]


admin.site.register(Thread, ThreadAdmin)


# admin.site.register(ThreadUserObjectPermission, UserObjectPermissionAdmin)
# admin.site.register(ThreadGroupObjectPermission, GroupObjectPermissionAdmin)


class MessageAdmin(HistoricalAdmin):
    model = Message
    list_display = ['id', 'master_user', 'created', 'thread', 'sender', 'short_text']
    list_select_related = ['thread', 'thread__master_user', 'sender']
    date_hierarchy = 'created'
    ordering = ['created']
    raw_id_fields = ['thread', 'sender']
    search_fields = ['thread__id', 'thread__subject']

    def master_user(self, obj):
        return obj.thread.master_user

    master_user.admin_order_field = 'thread__master_user'


admin.site.register(Message, MessageAdmin)


class DirectMessageAdmin(HistoricalAdmin):
    model = DirectMessage
    list_display = ['id', 'created', 'sender', 'recipient', 'short_text']
    list_select_related = ['sender', 'recipient']
    date_hierarchy = 'created'
    raw_id_fields = ['recipient', 'sender']


admin.site.register(DirectMessage, DirectMessageAdmin)

# register_admin(Thread)
