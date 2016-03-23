from django.contrib import admin

from poms.notifications.models import Notification


class NotificationAdmin(admin.ModelAdmin):
    model = Notification
    list_display = ['id', 'recipient', 'timestamp', 'unread', 'actor', 'verb', 'target', 'action_object', 'public']
    date_hierarchy = 'timestamp'


admin.site.register(Notification, NotificationAdmin)
