from __future__ import unicode_literals

from django.contrib import admin

from poms.audit.admin import HistoricalAdmin
from poms.common.admin import TreeModelAdmin
from poms.instruments.models import Instrument, PriceHistory, InstrumentClassifier, InstrumentClass, InstrumentType, \
    InstrumentTypeTag, InstrumentTag, DailyPricingModel, AccrualCalculationModel, PaymentFrequency, CostMethod, \
    ManualPricingFormula, InstrumentAttrValue, AccrualCalculationSchedule
from poms.users.admin import AttrValueAdminBase


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


class InstrumentTypeTagAdmin(HistoricalAdmin):
    model = InstrumentTypeTag
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']
    raw_id_fields = ['master_user']


admin.site.register(InstrumentTypeTag, InstrumentTypeTagAdmin)


class InstrumentTypeAdmin(HistoricalAdmin):
    model = InstrumentType
    list_display = ['id', 'name', 'master_user', 'instrument_class']
    list_select_related = ['master_user', 'instrument_class']
    list_filter = ['instrument_class']
    filter_horizontal = ['tags', ]
    raw_id_fields = ['master_user']


admin.site.register(InstrumentType, InstrumentTypeAdmin)


class InstrumentClassifierAdmin(HistoricalAdmin, TreeModelAdmin):
    model = InstrumentClassifier
    list_display = ['id', 'name', 'parent', 'master_user']
    list_select_related = ['master_user', 'parent']
    raw_id_fields = ['master_user', 'parent']


admin.site.register(InstrumentClassifier, InstrumentClassifierAdmin)


class InstrumentTagAdmin(HistoricalAdmin):
    model = InstrumentTag
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']
    raw_id_fields = ['master_user']


admin.site.register(InstrumentTag, InstrumentTagAdmin)


class ManualPricingFormulaAdmin(HistoricalAdmin):
    model = ManualPricingFormula
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']
    raw_id_fields = ['master_user']


admin.site.register(ManualPricingFormula, ManualPricingFormulaAdmin)


class InstrumentAttrValueInline(AttrValueAdminBase):
    model = InstrumentAttrValue


class AccrualCalculationScheduleInline(admin.StackedInline):
    model = AccrualCalculationSchedule
    extra = 0


class InstrumentAdmin(HistoricalAdmin):
    model = Instrument
    list_display = ['id', 'name', 'master_user', 'type', 'pricing_currency', 'accrued_currency']
    list_select_related = ['master_user', 'type', 'pricing_currency', 'accrued_currency']
    filter_horizontal = ['tags']
    inlines = [InstrumentAttrValueInline, AccrualCalculationScheduleInline]
    raw_id_fields = ['master_user', 'type', 'pricing_currency', 'accrued_currency',
                     'daily_pricing_model', 'accrual_calculation_model', 'payment_frequency',
                     'manual_pricing_formula']


admin.site.register(Instrument, InstrumentAdmin)


class PriceHistoryAdmin(HistoricalAdmin):
    model = PriceHistory
    list_display = ['id', 'date', 'instrument', 'principal_price', 'accrued_price', 'factor']
    list_select_related = ['instrument']
    date_hierarchy = 'date'
    raw_id_fields = ['instrument', 'pricing_policy']


admin.site.register(PriceHistory, PriceHistoryAdmin)
