from django.conf import settings
from django.contrib import admin
from kombu.transport.django.models import Queue, Message

if settings.DEBUG and 'kombu.transport.django' in settings.INSTALLED_APPS:
    class QueueAdmin(admin.ModelAdmin):
        model = Queue
        list_display = ('id', 'name')
        list_display_links = ('id',)
        search_fields = ('name',)


    admin.site.register(Queue, QueueAdmin)


    class MessageAdmin(admin.ModelAdmin):
        model = Message
        list_display = ('id', '_queue', 'visible', 'sent_at',)
        list_display_links = ('id',)
        # list_filter = ('queue',)
        search_fields = ('queue__name',)
        date_hierarchy = 'sent_at'
        raw_id_fields = ('queue',)
        list_select_related = ('queue',)

        def _queue(self, instanse):
            return instanse.queue.name

        _queue.short_description = 'Queue'
        _queue.admin_order_field = 'queue__name'


    admin.site.register(Message, MessageAdmin)
