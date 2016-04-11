from __future__ import unicode_literals

from django.contrib import admin

from poms.audit.admin import HistoricalAdmin
from poms.common.admin import TreeModelAdmin
from poms.instruments.models import Instrument, PriceHistory, InstrumentClassifier, InstrumentClass, InstrumentType, \
    DailyPricingModel, AccrualCalculationModel, PaymentFrequency, CostMethod, \
    ManualPricingFormula, AccrualCalculationSchedule, InstrumentTypeUserObjectPermission, \
    InstrumentTypeGroupObjectPermission, InstrumentClassifierUserObjectPermission, \
    InstrumentClassifierGroupObjectPermission, InstrumentUserObjectPermission, InstrumentGroupObjectPermission, \
    InstrumentAttributeType, InstrumentAttributeTypeOption, InstrumentAttributeTypeUserObjectPermission, \
    InstrumentAttributeTypeGroupObjectPermission
from poms.obj_attrs.admin import AttributeTypeAdminBase, AttributeTypeOptionInlineBase
from poms.obj_perms.admin import UserObjectPermissionAdmin, GroupObjectPermissionAdmin


class InstrumentClassAdmin(HistoricalAdmin):
    model = InstrumentClass
    list_display = ['id', 'system_code', 'name']
    ordering = ['id']


admin.site.register(InstrumentClass, InstrumentClassAdmin)


class DailyPricingModelAdmin(HistoricalAdmin):
    model = DailyPricingModel
    list_display = ['id', 'system_code', 'name']
    ordering = ['id']


admin.site.register(DailyPricingModel, DailyPricingModelAdmin)


class AccrualCalculationModelAdmin(HistoricalAdmin):
    model = AccrualCalculationModel
    list_display = ['id', 'system_code', 'name']
    ordering = ['id']


admin.site.register(AccrualCalculationModel, AccrualCalculationModelAdmin)


class PaymentFrequencyAdmin(HistoricalAdmin):
    model = PaymentFrequency
    list_display = ['id', 'system_code', 'name']
    ordering = ['id']


admin.site.register(PaymentFrequency, PaymentFrequencyAdmin)


class CostMethodAdmin(HistoricalAdmin):
    model = InstrumentClass
    list_display = ['id', 'system_code', 'name']
    ordering = ['id']


admin.site.register(CostMethod, InstrumentClassAdmin)


class InstrumentTypeAdmin(HistoricalAdmin):
    model = InstrumentType
    list_display = ['id', 'name', 'master_user', 'instrument_class']
    list_select_related = ['master_user', 'instrument_class']
    list_filter = ['instrument_class']
    raw_id_fields = ['master_user']


admin.site.register(InstrumentType, InstrumentTypeAdmin)
admin.site.register(InstrumentTypeUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(InstrumentTypeGroupObjectPermission, GroupObjectPermissionAdmin)


class InstrumentClassifierAdmin(HistoricalAdmin, TreeModelAdmin):
    model = InstrumentClassifier
    list_display = ['id', 'formatted_name', 'parent', 'master_user']
    list_select_related = ['master_user', 'parent']
    raw_id_fields = ['master_user', 'parent']


admin.site.register(InstrumentClassifier, InstrumentClassifierAdmin)
admin.site.register(InstrumentClassifierUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(InstrumentClassifierGroupObjectPermission, GroupObjectPermissionAdmin)


class ManualPricingFormulaInline(admin.StackedInline):
    model = ManualPricingFormula
    extra = 0


class AccrualCalculationScheduleInline(admin.StackedInline):
    model = AccrualCalculationSchedule
    extra = 0


class InstrumentAdmin(HistoricalAdmin):
    model = Instrument
    list_display = ['id', 'name', 'master_user', 'type', 'pricing_currency', 'accrued_currency']
    list_select_related = ['master_user', 'type', 'pricing_currency', 'accrued_currency']
    inlines = [ManualPricingFormulaInline, AccrualCalculationScheduleInline, ]
    raw_id_fields = ['master_user', 'type', 'pricing_currency', 'accrued_currency',
                     'daily_pricing_model']


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

admin.site.register(InstrumentAttributeType, AttributeTypeAdminBase)
admin.site.register(InstrumentAttributeTypeOption, AttributeTypeOptionInlineBase)
admin.site.register(InstrumentAttributeTypeUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(InstrumentAttributeTypeGroupObjectPermission, GroupObjectPermissionAdmin)
