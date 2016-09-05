from __future__ import unicode_literals

from django.contrib import admin, messages
from django.db import models
from django.forms import widgets

from poms.audit.admin import HistoricalAdmin
from poms.common.admin import ClassModelAdmin, ClassifierAdmin
from poms.instruments.models import Instrument, PriceHistory, InstrumentClass, InstrumentType, \
    DailyPricingModel, AccrualCalculationModel, Periodicity, CostMethod, \
    ManualPricingFormula, AccrualCalculationSchedule, InstrumentAttributeType, InstrumentAttribute, \
    InstrumentFactorSchedule, EventSchedule, \
    PricingPolicy, PaymentSizeDetail, InstrumentClassifier, EventScheduleAction, EventScheduleConfig
from poms.obj_attrs.admin import AbstractAttributeTypeAdmin, AbstractAttributeInline, \
    AbstractAttributeTypeClassifierInline, AbstractAttributeTypeOptionInline
from poms.obj_perms.admin import UserObjectPermissionInline, \
    GroupObjectPermissionInline

admin.site.register(InstrumentClass, ClassModelAdmin)
admin.site.register(DailyPricingModel, ClassModelAdmin)
admin.site.register(AccrualCalculationModel, ClassModelAdmin)
admin.site.register(Periodicity, ClassModelAdmin)
admin.site.register(CostMethod, ClassModelAdmin)
admin.site.register(PaymentSizeDetail, ClassModelAdmin)


class PricingPolicyAdmin(HistoricalAdmin):
    model = PricingPolicy
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']
    raw_id_fields = ['master_user']
    ordering = ['user_code']


admin.site.register(PricingPolicy, PricingPolicyAdmin)


class InstrumentTypeAdmin(HistoricalAdmin):
    model = InstrumentType
    list_display = ['id', 'name', 'master_user', 'instrument_class']
    list_select_related = ['master_user', 'instrument_class']
    list_filter = ['instrument_class']
    raw_id_fields = ['master_user', 'one_off_event', 'regular_event']
    inlines = [
        UserObjectPermissionInline,
        GroupObjectPermissionInline,
    ]


admin.site.register(InstrumentType, InstrumentTypeAdmin)


class InstrumentAttributeInline(AbstractAttributeInline):
    model = InstrumentAttribute


class ManualPricingFormulaInline(admin.TabularInline):
    model = ManualPricingFormula
    extra = 0
    formfield_overrides = {
        models.TextField: {'widget': widgets.Textarea(attrs={'cols': '40', 'rows': '3'})},
    }


class AccrualCalculationScheduleInline(admin.TabularInline):
    model = AccrualCalculationSchedule
    extra = 0
    formfield_overrides = {
        models.TextField: {'widget': widgets.Textarea(attrs={'cols': '40', 'rows': '3'})},
    }


class InstrumentFactorScheduleInline(admin.TabularInline):
    model = InstrumentFactorSchedule
    extra = 0


# class EventScheduleInline(admin.StackedInline):
#     model = EventSchedule
#     extra = 0


class InstrumentAdmin(HistoricalAdmin):
    model = Instrument
    list_display = ['id', 'master_user', 'name', 'instrument_type', 'pricing_currency', 'accrued_currency',
                    'reference_for_pricing', 'daily_pricing_model', 'price_download_scheme']
    list_select_related = ['master_user', 'instrument_type', 'pricing_currency', 'accrued_currency']
    list_filter = ['instrument_type__instrument_class']
    raw_id_fields = ['master_user', 'instrument_type', 'pricing_currency', 'accrued_currency', 'price_download_scheme']
    search_fields = ['name']
    inlines = [
        InstrumentAttributeInline,
        ManualPricingFormulaInline,
        AccrualCalculationScheduleInline,
        InstrumentFactorScheduleInline,
        # EventScheduleInline,
        UserObjectPermissionInline,
        GroupObjectPermissionInline,
    ]
    actions = ['rebuild_event_schedules', 'calculate_prices_accrued_price']

    def rebuild_event_schedules(self, request, queryset):
        for instr in queryset:
            try:
                instr.rebuild_event_schedules()
            except ValueError as e:
                messages.error(request, '%s: %s' % (instr, e))

    rebuild_event_schedules.short_description = "Rebuild event schedules"

    def calculate_prices_accrued_price(self, request, queryset):
        for instr in queryset:
            instr.calculate_prices_accrued_price(save=True)

    calculate_prices_accrued_price.short_description = "Calculate accrued price for prices"


admin.site.register(Instrument, InstrumentAdmin)


class AccrualCalculationScheduleAdmin(admin.ModelAdmin):
    model = AccrualCalculationSchedule
    list_display = ['id', 'master_user', 'instrument', 'accrual_start_date', 'first_payment_date',
                    'accrual_calculation_model', 'periodicity']
    list_select_related = ['instrument', 'instrument__master_user', 'accrual_calculation_model', 'periodicity']
    list_filter = ['accrual_calculation_model', 'periodicity']
    raw_id_fields = ['instrument']
    search_fields = ['instrument__name']

    def master_user(self, obj):
        return obj.instrument.master_user


admin.site.register(AccrualCalculationSchedule, AccrualCalculationScheduleAdmin)


class EventScheduleActionInline(admin.TabularInline):
    model = EventScheduleAction
    raw_id_fields = ['transaction_type']
    extra = 0


class EventScheduleAdmin(admin.ModelAdmin):
    model = EventSchedule
    list_display = ['id', 'master_user', 'instrument', 'name', 'event_class', 'notification_class', 'effective_date',
                    'periodicity', 'final_date', 'is_auto_generated', 'accrual_calculation_schedule', 'factor_schedule']
    list_select_related = ['instrument', 'instrument__master_user', 'event_class', 'notification_class']
    raw_id_fields = ['instrument', 'accrual_calculation_schedule']
    search_fields = ['instrument__name']

    inlines = [
        EventScheduleActionInline
    ]

    def master_user(self, obj):
        return obj.instrument.master_user


admin.site.register(EventSchedule, EventScheduleAdmin)


class PriceHistoryAdmin(HistoricalAdmin):
    model = PriceHistory
    list_display = ['id', 'date', 'instrument', 'principal_price', 'accrued_price']
    list_select_related = ['instrument']
    list_filter = ['date']
    search_fields = ['instrument__name']
    date_hierarchy = 'date'
    raw_id_fields = ['instrument', 'pricing_policy']
    actions = ['calculate_accrued_price']

    def calculate_accrued_price(self, request, queryset):
        for p in queryset:
            p.calculate_accrued_price(save=True)

    calculate_accrued_price.short_description = "Calculate accrued price"


admin.site.register(PriceHistory, PriceHistoryAdmin)


class InstrumentAttributeTypeAdmin(AbstractAttributeTypeAdmin):
    inlines = [
        AbstractAttributeTypeClassifierInline,
        AbstractAttributeTypeOptionInline,
        UserObjectPermissionInline,
        GroupObjectPermissionInline,
    ]


admin.site.register(InstrumentAttributeType, InstrumentAttributeTypeAdmin)

admin.site.register(InstrumentClassifier, ClassifierAdmin)


class EventScheduleConfigAdmin(admin.ModelAdmin):
    model = EventScheduleConfig
    list_display = ('id', 'master_user', 'notification_class')
    list_select_related = ('master_user', 'notification_class',)
    raw_id_fields = ('master_user',)

    def master_user(self, obj):
        return obj.instrument.master_user


admin.site.register(EventScheduleConfig, EventScheduleConfigAdmin)
