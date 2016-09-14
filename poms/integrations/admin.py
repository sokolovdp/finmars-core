from __future__ import unicode_literals, print_function

from django import forms
from django.conf import settings
from django.contrib import admin
from django.core.urlresolvers import reverse_lazy
from django.utils.html import escape
from django.utils.translation import ugettext_lazy

from poms.audit.admin import HistoricalAdmin
from poms.common.admin import ClassModelAdmin
from poms.integrations.models import Task, ImportConfig, ProviderClass, CurrencyMapping, \
    InstrumentTypeMapping, InstrumentAttributeValueMapping, FactorScheduleDownloadMethod, AccrualScheduleDownloadMethod, \
    InstrumentDownloadScheme, InstrumentDownloadSchemeInput, InstrumentDownloadSchemeAttribute, PriceDownloadScheme, \
    AccrualCalculationModelMapping, PeriodicityMapping, PricingAutomatedSchedule

if settings.DEBUG and 'kombu.transport.django' in settings.INSTALLED_APPS:
    from kombu.transport.django.models import Queue, Message


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

admin.site.register(ProviderClass, ClassModelAdmin)
admin.site.register(FactorScheduleDownloadMethod, ClassModelAdmin)
admin.site.register(AccrualScheduleDownloadMethod, ClassModelAdmin)


class ImportConfigForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), required=False)

    class Meta:
        model = ImportConfig
        fields = ['master_user', 'provider', 'p12cert', 'password', 'cert', 'key']


class ImportConfigAdmin(HistoricalAdmin):
    model = ImportConfig
    form = ImportConfigForm
    list_display = ['id', 'master_user', 'provider', ]
    list_select_related = ['master_user', 'provider', ]
    raw_id_fields = ['master_user', ]


admin.site.register(ImportConfig, ImportConfigAdmin)


class InstrumentDownloadSchemeInputInline(admin.TabularInline):
    model = InstrumentDownloadSchemeInput
    extra = 0


class InstrumentDownloadSchemeAttributeInline(admin.TabularInline):
    model = InstrumentDownloadSchemeAttribute
    extra = 0
    raw_id_fields = ['attribute_type']


class InstrumentDownloadSchemeAdmin(HistoricalAdmin):
    model = InstrumentDownloadScheme
    list_display = ['id', 'master_user', 'scheme_name', 'provider', 'fields0']
    list_select_related = ['master_user', 'provider', ]
    raw_id_fields = ['master_user', 'price_download_scheme']
    search_fields = ['scheme_name', ]
    inlines = [
        InstrumentDownloadSchemeInputInline,
        InstrumentDownloadSchemeAttributeInline,
    ]
    save_as = True

    def fields0(self, obj):
        f = obj.fields
        if f:
            return ', '.join(f)
        return None

    fields0.short_description = ugettext_lazy('fields')


admin.site.register(InstrumentDownloadScheme, InstrumentDownloadSchemeAdmin)


class PriceDownloadSchemeAdmin(admin.ModelAdmin):
    model = PriceDownloadScheme
    list_display = ['id', 'master_user', 'scheme_name', 'provider', 'instrument_yesterday_fields0',
                    'instrument_history_fields0', 'currency_history_fields0']
    list_select_related = ['master_user', 'provider']
    search_fields = ['scheme_name']
    list_filter = ['provider']
    raw_id_fields = ['master_user']

    def instrument_yesterday_fields0(self, obj):
        f = obj.instrument_yesterday_fields
        if f:
            return ', '.join(f)
        return None

    instrument_yesterday_fields0.short_description = ugettext_lazy('instrument yesterday fields')

    def instrument_history_fields0(self, obj):
        f = obj.instrument_history_fields
        if f:
            return ', '.join(f)
        return None

    instrument_history_fields0.short_description = ugettext_lazy('instrument history fields')

    def currency_history_fields0(self, obj):
        f = obj.currency_history_fields
        if f:
            return ', '.join(f)
        return None

    currency_history_fields0.short_description = ugettext_lazy('currency history fields')


admin.site.register(PriceDownloadScheme, PriceDownloadSchemeAdmin)


class CurrencyMappingAdmin(admin.ModelAdmin):
    model = CurrencyMapping
    list_display = ['id', 'master_user', 'provider', 'value', 'currency']
    list_select_related = ['master_user', 'provider', 'currency']
    raw_id_fields = ['master_user', 'currency']


admin.site.register(CurrencyMapping, CurrencyMappingAdmin)


class InstrumentTypeMappingAdmin(admin.ModelAdmin):
    model = InstrumentTypeMapping
    list_display = ['id', 'master_user', 'provider', 'value', 'instrument_type']
    list_select_related = ['master_user', 'provider', 'instrument_type']
    raw_id_fields = ['master_user', 'instrument_type']


admin.site.register(InstrumentTypeMapping, InstrumentTypeMappingAdmin)


class AccrualCalculationModelMappingAdmin(admin.ModelAdmin):
    model = AccrualCalculationModelMapping
    list_display = ['id', 'master_user', 'provider', 'value', 'accrual_calculation_model']
    list_select_related = ['master_user', 'accrual_calculation_model', 'provider']
    raw_id_fields = ['master_user']


admin.site.register(AccrualCalculationModelMapping, AccrualCalculationModelMappingAdmin)


class PeriodicityMappingAdmin(admin.ModelAdmin):
    model = PeriodicityMapping
    list_display = ['id', 'master_user', 'provider', 'value', 'periodicity']
    list_select_related = ['master_user', 'provider', 'periodicity']
    raw_id_fields = ['master_user']


admin.site.register(PeriodicityMapping, PeriodicityMappingAdmin)


class InstrumentAttributeValueMappingAdmin(admin.ModelAdmin):
    model = InstrumentAttributeValueMapping
    list_display = ['id', 'master_user', 'provider', 'value', 'attribute_type']
    list_select_related = ['attribute_type__master_user', 'attribute_type', 'classifier', 'provider']
    raw_id_fields = ['master_user', 'attribute_type', 'classifier']

    def master_user(self, obj):
        return obj.attribute_type.master_user

    master_user.admin_order_field = 'attribute_type__master_user__name'


admin.site.register(InstrumentAttributeValueMapping, InstrumentAttributeValueMappingAdmin)


class TaskAdmin(admin.ModelAdmin):
    model = Task
    list_display = ['__str__', 'parent', 'created', 'status', 'master_user', 'member', 'provider', 'action',
                    'response_id']
    list_select_related = ['parent', 'master_user', 'member', 'provider']
    raw_id_fields = ['master_user', 'member', 'parent']
    search_fields = ['response_id', ]
    list_filter = ['provider', 'created', 'action', 'status', ]
    date_hierarchy = 'created'

    readonly_fields = [
        'id', 'celery_tasks_id',
        'master_user', 'member', 'parent',
        'provider', 'action', 'status',
        'request_id', 'response_id', 'options', 'result',
    ]

    def has_add_permission(self, request):
        return False

    def save_model(self, request, obj, form, change):
        pass


admin.site.register(Task, TaskAdmin)


class PricingAutomatedScheduleAdmin(admin.ModelAdmin):
    model = PricingAutomatedSchedule
    list_display = ['id', 'master_user', 'is_enabled', 'cron_expr', 'last_run_at', 'next_run_at', 'last_run_task_url']
    list_select_related = ['master_user', ]
    list_filter = ['is_enabled', 'last_run_at', 'next_run_at']
    date_hierarchy = 'next_run_at'
    raw_id_fields = ['master_user', ]

    # readonly_fields = ['latest_running', 'latest_task']

    def last_run_task_url(self, obj):
        t = obj.last_run_task
        if t:
            return '<a href="%s">%s</a>' % (reverse_lazy("admin:integrations_task_change", args=(t.id,)), escape(t.id))
        return None

    last_run_task_url.allow_tags = True
    last_run_task_url.short_description = ugettext_lazy('last run task')


admin.site.register(PricingAutomatedSchedule, PricingAutomatedScheduleAdmin)
