from __future__ import unicode_literals

from django.contrib import admin

from poms.notifications.models import Notification


class NotificationAdmin(admin.ModelAdmin):
    model = Notification
    list_display = ['id', 'recipient', 'create_date', 'read_date', 'actor_repr', 'verb', 'target_repr',
                    'action_object_repr']
    list_select_related = ['recipient']
    date_hierarchy = 'create_date'


admin.site.register(Notification, NotificationAdmin)
