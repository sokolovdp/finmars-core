from __future__ import unicode_literals, print_function

from django import forms
from django.contrib import admin
from django.core.urlresolvers import reverse_lazy
from django.utils.html import escape
from django.utils.translation import ugettext_lazy

from poms.common.admin import ClassModelAdmin, AbstractModelAdmin
from poms.integrations.models import Task, ImportConfig, ProviderClass, CurrencyMapping, \
    InstrumentTypeMapping, InstrumentAttributeValueMapping, FactorScheduleDownloadMethod, AccrualScheduleDownloadMethod, \
    InstrumentDownloadScheme, InstrumentDownloadSchemeInput, InstrumentDownloadSchemeAttribute, PriceDownloadScheme, \
    AccrualCalculationModelMapping, PeriodicityMapping, PricingAutomatedSchedule, ComplexTransactionFileImportScheme, \
    ComplexTransactionFileImportField, ComplexTransactionFileImportSchemeType

admin.site.register(ProviderClass, ClassModelAdmin)
admin.site.register(FactorScheduleDownloadMethod, ClassModelAdmin)
admin.site.register(AccrualScheduleDownloadMethod, ClassModelAdmin)


class ImportConfigForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), required=False)

    class Meta:
        model = ImportConfig
        fields = ['master_user', 'provider', 'p12cert', 'password', 'cert', 'key']


class ImportConfigAdmin(AbstractModelAdmin):
    model = ImportConfig
    master_user_path = 'master_user'
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


class InstrumentDownloadSchemeAdmin(AbstractModelAdmin):
    model = InstrumentDownloadScheme
    master_user_path = 'master_user'
    list_display = ['id', 'master_user', 'provider', 'scheme_name', 'fields0']
    list_select_related = ['master_user', 'provider', ]
    ordering = ['master_user', 'provider', 'scheme_name']
    list_filter = ['provider']
    search_fields = ['id', 'scheme_name', ]
    raw_id_fields = ['master_user', 'price_download_scheme']
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


class PriceDownloadSchemeAdmin(AbstractModelAdmin):
    model = PriceDownloadScheme
    master_user_path = 'master_user'
    list_display = ['id', 'master_user', 'provider', 'scheme_name', 'instrument_yesterday_fields0',
                    'instrument_history_fields0', 'currency_history_fields0']
    list_select_related = ['master_user', 'provider']
    list_filter = ['provider']
    ordering = ['master_user', 'provider', 'scheme_name']
    search_fields = ['id', 'scheme_name']
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


class CurrencyMappingAdmin(AbstractModelAdmin):
    model = CurrencyMapping
    master_user_path = 'master_user'
    list_display = ['id', 'master_user', 'provider', 'value', 'currency']
    list_select_related = ['master_user', 'provider', 'currency']
    raw_id_fields = ['master_user', 'currency']
    ordering = ['master_user', 'provider', 'value']


admin.site.register(CurrencyMapping, CurrencyMappingAdmin)


class InstrumentTypeMappingAdmin(AbstractModelAdmin):
    model = InstrumentTypeMapping
    master_user_path = 'master_user'
    list_display = ['id', 'master_user', 'provider', 'value', 'instrument_type']
    list_select_related = ['master_user', 'provider', 'instrument_type']
    raw_id_fields = ['master_user', 'instrument_type']
    ordering = ['master_user', 'provider', 'value']


admin.site.register(InstrumentTypeMapping, InstrumentTypeMappingAdmin)


class AccrualCalculationModelMappingAdmin(AbstractModelAdmin):
    model = AccrualCalculationModelMapping
    master_user_path = 'master_user'
    list_display = ['id', 'master_user', 'provider', 'value', 'accrual_calculation_model']
    list_select_related = ['master_user', 'accrual_calculation_model', 'provider']
    list_filter = ['accrual_calculation_model']
    raw_id_fields = ['master_user']
    ordering = ['master_user', 'provider', 'value']


admin.site.register(AccrualCalculationModelMapping, AccrualCalculationModelMappingAdmin)


class PeriodicityMappingAdmin(AbstractModelAdmin):
    model = PeriodicityMapping
    master_user_path = 'master_user'
    list_display = ['id', 'master_user', 'provider', 'value', 'periodicity']
    list_select_related = ['master_user', 'provider', 'periodicity']
    list_filter = ['periodicity']
    raw_id_fields = ['master_user']
    ordering = ['master_user', 'provider', 'value']


admin.site.register(PeriodicityMapping, PeriodicityMappingAdmin)


class InstrumentAttributeValueMappingAdmin(AbstractModelAdmin):
    model = InstrumentAttributeValueMapping
    master_user_path = 'master_user'
    list_display = ['id', 'master_user', 'provider', 'value', 'attribute_type', 'value_string', 'value_float',
                    'value_date', 'classifier']
    list_select_related = ['attribute_type__master_user', 'attribute_type', 'classifier', 'provider']
    raw_id_fields = ['master_user', 'attribute_type', 'classifier']
    ordering = ['master_user', 'provider', 'value']

    def master_user(self, obj):
        return obj.attribute_type.master_user

    master_user.admin_order_field = 'attribute_type__master_user__name'


admin.site.register(InstrumentAttributeValueMapping, InstrumentAttributeValueMappingAdmin)


class TaskAdmin(AbstractModelAdmin):
    model = Task
    master_user_path = 'master_user'
    list_display = ['id', 'parent', 'created', 'status', 'master_user', 'member', 'provider', 'action',
                    'response_id']
    list_select_related = ['parent', 'master_user', 'member', 'provider']
    ordering = ['-created']
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


class PricingAutomatedScheduleAdmin(AbstractModelAdmin):
    model = PricingAutomatedSchedule
    master_user_path = 'master_user'
    list_display = ['id', 'master_user', 'is_enabled', 'cron_expr', 'last_run_at', 'next_run_at', 'last_run_task_url']
    list_select_related = ['master_user', ]
    list_filter = ['is_enabled', 'last_run_at', 'next_run_at']
    ordering = ['master_user']
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


# --------


# class ComplexTransactionFileImportSchemeAdmin(AbstractModelAdmin):
#     model = ComplexTransactionFileImportScheme
#     master_user_path = 'master_user'
#     list_display = ['id', 'master_user', 'scheme_name']
#     list_select_related = ['master_user', ]
#     search_fields = ['id', 'scheme_name', ]
#     raw_id_fields = ['master_user']
#     save_as = True
#
#
# admin.site.register(ComplexTransactionFileImportScheme, ComplexTransactionFileImportSchemeAdmin)
#
#
# class ComplexTransactionFileImportFieldInline(admin.TabularInline):
#     model = ComplexTransactionFileImportField
#     extra = 0
#
#
# class ComplexTransactionFileImportSchemeTypeAdmin(AbstractModelAdmin):
#     model = ComplexTransactionFileImportSchemeType
#     master_user_path = 'scheme__master_user'
#     list_display = ['id', 'master_user', 'scheme', 'transaction_type', 'user_code']
#     list_select_related = ['scheme', 'scheme__master_user', 'transaction_type']
#     search_fields = ['id', 'scheme__scheme_name', ]
#     raw_id_fields = ['scheme', 'transaction_type']
#     inlines = [
#         ComplexTransactionFileImportFieldInline,
#     ]
#     save_as = True
#
#     def master_user(self, obj):
#         return obj.scheme.master_user
#
#     master_user.admin_order_field = 'scheme__master_user'
#
#
# admin.site.register(ComplexTransactionFileImportSchemeType, ComplexTransactionFileImportSchemeTypeAdmin)

