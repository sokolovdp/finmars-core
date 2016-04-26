from __future__ import unicode_literals

from django.contrib import admin

from poms.notifications.models import Notification


class NotificationAdmin(admin.ModelAdmin):
    model = Notification
    list_display = ['id', 'recipient', 'create_date', 'type', 'message',
                    'actor', 'verb', 'target', 'action_object']
    list_select_related = ['recipient']
    raw_id_fields = ['recipient']
    date_hierarchy = 'create_date'

    def get_queryset(self, request):
        queryset = super(NotificationAdmin, self).get_queryset(request)
        queryset.prefetch_related('actor', 'target', 'action_object')
        return queryset


admin.site.register(Notification, NotificationAdmin)
