from __future__ import unicode_literals

from django.contrib import admin

from poms.audit.admin import HistoricalAdmin
from poms.common.admin import ClassModelAdmin, ClassifierAdmin
from poms.instruments.models import Instrument, PriceHistory, InstrumentClassifier, InstrumentClass, InstrumentType, \
    DailyPricingModel, AccrualCalculationModel, PeriodicityPeriod, CostMethod, \
    ManualPricingFormula, AccrualCalculationSchedule, InstrumentTypeGroupObjectPermission, \
    InstrumentGroupObjectPermission, \
    InstrumentAttributeType, InstrumentAttributeTypeOption, InstrumentAttributeTypeGroupObjectPermission, \
    InstrumentAttribute, InstrumentFactorSchedule, EventSchedule, \
    PricingPolicy, PaymentSizeDetail, InstrumentTypeUserObjectPermission, InstrumentUserObjectPermission, \
    InstrumentAttributeTypeUserObjectPermission
from poms.obj_attrs.admin import AbstractAttributeTypeAdmin, AbstractAttributeTypeOptionAdmin, AbstractAttributeInline, \
    AbstractAttributeTypeClassifierInline
from poms.obj_perms.admin import GroupObjectPermissionAdmin, UserObjectPermissionAdmin

admin.site.register(InstrumentClass, ClassModelAdmin)
admin.site.register(DailyPricingModel, ClassModelAdmin)
admin.site.register(AccrualCalculationModel, ClassModelAdmin)
admin.site.register(PeriodicityPeriod, ClassModelAdmin)
admin.site.register(CostMethod, ClassModelAdmin)
admin.site.register(PaymentSizeDetail, ClassModelAdmin)


class PricingPolicyAdmin(HistoricalAdmin):
    model = PricingPolicy
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']
    ordering = ['user_code']


admin.site.register(PricingPolicy, PricingPolicyAdmin)


class InstrumentTypeAdmin(HistoricalAdmin):
    model = InstrumentType
    list_display = ['id', 'name', 'master_user', 'instrument_class']
    list_select_related = ['master_user', 'instrument_class']
    list_filter = ['instrument_class']
    raw_id_fields = ['master_user']


admin.site.register(InstrumentType, InstrumentTypeAdmin)
admin.site.register(InstrumentTypeUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(InstrumentTypeGroupObjectPermission, GroupObjectPermissionAdmin)

admin.site.register(InstrumentClassifier, ClassifierAdmin)


# admin.site.register(InstrumentClassifierUserObjectPermission, UserObjectPermissionAdmin)
# admin.site.register(InstrumentClassifierGroupObjectPermission, GroupObjectPermissionAdmin)


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


class EventScheduleInline(admin.StackedInline):
    model = EventSchedule
    extra = 0


class InstrumentAdmin(HistoricalAdmin):
    model = Instrument
    list_display = ['id', 'master_user', 'name', 'instrument_type', 'pricing_currency', 'accrued_currency']
    list_select_related = ['master_user', 'instrument_type', 'pricing_currency', 'accrued_currency']
    raw_id_fields = ['master_user', 'instrument_type', 'pricing_currency', 'accrued_currency']
    inlines = [InstrumentAttributeInline, ManualPricingFormulaInline, AccrualCalculationScheduleInline,
               InstrumentFactorScheduleInline, EventScheduleInline]


admin.site.register(Instrument, InstrumentAdmin)
admin.site.register(InstrumentUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(InstrumentGroupObjectPermission, GroupObjectPermissionAdmin)


class PriceHistoryAdmin(HistoricalAdmin):
    model = PriceHistory
    list_display = ['id', 'date', 'instrument', 'principal_price', 'accrued_price', 'factor']
    list_select_related = ['instrument']
    date_hierarchy = 'date'
    raw_id_fields = ['instrument', 'pricing_policy']


admin.site.register(PriceHistory, PriceHistoryAdmin)


class InstrumentAttributeTypeClassifierInline(AbstractAttributeTypeClassifierInline):
    model = InstrumentClassifier


class InstrumentAttributeTypeAdmin(AbstractAttributeTypeAdmin):
    inlines = [InstrumentAttributeTypeClassifierInline]


admin.site.register(InstrumentAttributeType, InstrumentAttributeTypeAdmin)
admin.site.register(InstrumentAttributeTypeOption, AbstractAttributeTypeOptionAdmin)
admin.site.register(InstrumentAttributeTypeUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(InstrumentAttributeTypeGroupObjectPermission, GroupObjectPermissionAdmin)
