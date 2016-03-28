from __future__ import unicode_literals

from django.contrib import admin

from poms.audit.admin import HistoricalAdmin
from poms.u2u_messages.models import Channel, Member, Message, Status


class MemberInline(admin.TabularInline):
    model = Member
    extra = 0


class ChannelAdmin(HistoricalAdmin):
    model = Channel
    list_display = ['id', 'name', 'master_user']
    inlines = [MemberInline]


admin.site.register(Channel, ChannelAdmin)


class StatusInline(admin.TabularInline):
    model = Status
    extra = 0


class MessageAdmin(HistoricalAdmin):
    model = Message
    list_display = ['id', 'channel', 'sender', 'text']
    inlines = [StatusInline]


admin.site.register(Message, MessageAdmin)
