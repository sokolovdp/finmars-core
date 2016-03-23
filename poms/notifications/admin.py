from django.contrib import admin

from poms.notifications.models import Notification


class NotificationAdmin(admin.ModelAdmin):
    model = Notification
    list_display = ['id', 'recipient', 'create_date', 'read_date', 'actor', 'verb', 'target', 'action_object', 'public']
    date_hierarchy = 'create_date'


admin.site.register(Notification, NotificationAdmin)
