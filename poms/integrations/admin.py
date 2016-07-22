from django.conf import settings
from django.contrib import admin
from kombu.transport.django.models import Queue, Message

from poms.audit.admin import HistoricalAdmin
from poms.integrations.models import InstrumentMapping, InstrumentAttributeMapping, BloombergRequestLogEntry

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


class InstrumentAttributeMappingInline(admin.TabularInline):
    model = InstrumentAttributeMapping
    extra = 0
    raw_id_fields = ['attribute_type']


class InstrumentMappingAdmin(HistoricalAdmin):
    model = InstrumentMapping
    inlines = [InstrumentAttributeMappingInline]
    list_display = ['id', 'master_user', 'mapping_name']
    list_select_related = ['master_user', ]
    raw_id_fields = ['master_user', ]
    search_fields = ['mapping_name', ]


admin.site.register(InstrumentMapping, InstrumentMappingAdmin)


class BloombergRequestLogEntryAdmin(admin.ModelAdmin):
    model = BloombergRequestLogEntry
    list_display = ['id', 'created', 'master_user', 'member', 'token', 'request_id', 'is_success',
                    'is_user_got_response']
    list_select_related = ['master_user', 'member', ]
    raw_id_fields = ['master_user', 'member', ]
    search_fields = ['request_id', 'token', ]
    list_filter = ['created', 'is_success', 'is_user_got_response']
    date_hierarchy = 'created'

    if not settings.DEBUG:
        readonly_fields = ['id', 'created', 'modified', 'master_user', 'member', 'token',
                           'is_success', 'is_user_got_response',
                           'request_id', 'request', 'response', ]

    def has_add_permission(self, request):
        return settings.DEBUG


admin.site.register(BloombergRequestLogEntry, BloombergRequestLogEntryAdmin)
