from __future__ import unicode_literals

from django.contrib import admin
from reversion.admin import VersionAdmin

from poms.audit.models import AuthLogEntry


class AuthLogEntryAdmin(admin.ModelAdmin):
    model = AuthLogEntry
    list_display = ['id', 'date', 'user', 'is_success', 'user_ip', 'user_agent']
    list_select_related = ['user']
    date_hierarchy = 'date'
    ordering = ('-date',)
    fields = ['id', 'date', 'user', 'is_success', 'user_ip', 'user_agent']
    readonly_fields = ['id', 'date', 'is_success', 'user', 'user_ip', 'user_agent', ]

    def has_add_permission(self, request):
        return False


admin.site.register(AuthLogEntry, AuthLogEntryAdmin)


class HistoricalAdmin(VersionAdmin):
    history_latest_first = True
    ignore_duplicate_revisions = True
