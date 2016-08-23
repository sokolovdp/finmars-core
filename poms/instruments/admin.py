from __future__ import unicode_literals

from django.contrib import admin

from poms.audit.admin import HistoricalAdmin
from poms.common.admin import ClassModelAdmin, ClassifierAdmin
from poms.instruments.models import Instrument, PriceHistory, InstrumentClass, InstrumentType, \
    DailyPricingModel, AccrualCalculationModel, Periodicity, CostMethod, \
    ManualPricingFormula, AccrualCalculationSchedule, InstrumentAttributeType, InstrumentAttribute, \
    InstrumentFactorSchedule, EventSchedule, \
    PricingPolicy, PaymentSizeDetail, InstrumentClassifier, EventScheduleAction
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


class ManualPricingFormulaInline(admin.StackedInline):
    model = ManualPricingFormula
    extra = 0


class AccrualCalculationScheduleInline(admin.StackedInline):
    model = AccrualCalculationSchedule
    extra = 0


class InstrumentFactorScheduleInline(admin.StackedInline):
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
    raw_id_fields = ['master_user', 'instrument_type', 'pricing_currency', 'accrued_currency', 'price_download_scheme']
    inlines = [
        InstrumentAttributeInline,
        ManualPricingFormulaInline,
        AccrualCalculationScheduleInline,
        InstrumentFactorScheduleInline,
        # EventScheduleInline,
        UserObjectPermissionInline,
        GroupObjectPermissionInline,
    ]


admin.site.register(Instrument, InstrumentAdmin)


class EventScheduleActionInline(admin.TabularInline):
    model = EventScheduleAction
    extra = 0


class EventScheduleAdmin(admin.ModelAdmin):
    model = EventSchedule
    list_display = ['id', 'master_user', 'instrument', 'name', 'event_class', 'notification_class', 'effective_date',
                    'notify_in_n_days']
    list_select_related = ['instrument', 'instrument__master_user', 'event_class', 'notification_class']
    raw_id_fields = ['instrument']

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
    date_hierarchy = 'date'
    raw_id_fields = ['instrument', 'pricing_policy']


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
