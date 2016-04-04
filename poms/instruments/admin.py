from __future__ import unicode_literals

from django.contrib import admin
from mptt.admin import MPTTModelAdmin

from poms.audit.admin import HistoricalAdmin
from poms.instruments.models import Instrument, PriceHistory, InstrumentClassifier, InstrumentClass, InstrumentType, \
    InstrumentTypeTag, InstrumentTag, DailyPricingModel, AccrualCalculationModel, PaymentFrequency, CostMethod


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


admin.site.register(InstrumentTypeTag, InstrumentTypeTagAdmin)


class InstrumentTypeAdmin(HistoricalAdmin):
    model = InstrumentType
    list_display = ['id', 'instrument_class', 'name', 'master_user']
    list_select_related = ['master_user']
    list_filter = ['instrument_class']
    filter_horizontal = ['tags', ]


admin.site.register(InstrumentType, InstrumentTypeAdmin)


class InstrumentClassifierAdmin(HistoricalAdmin, MPTTModelAdmin):
    # change_list_template = 'admin/mptt_change_list.html'
    model = InstrumentClassifier
    list_display = ['id', 'name', 'parent', 'master_user']
    list_select_related = ['master_user', 'parent']
    mptt_level_indent = 20
    mptt_indent_field = "name"


admin.site.register(InstrumentClassifier, InstrumentClassifierAdmin)


class InstrumentTagAdmin(HistoricalAdmin):
    model = InstrumentTag
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']


admin.site.register(InstrumentTag, InstrumentTagAdmin)


class InstrumentAdmin(HistoricalAdmin):
    model = Instrument
    list_display = ['id', 'name', 'type', 'master_user', 'pricing_currency', 'accrued_currency']
    list_select_related = ['master_user', 'pricing_currency', 'accrued_currency']
    filter_horizontal = ['tags', ]

    # def get_classifiers(self, obj):
    #     return ', '.join(p.name for p in obj.classifiers.all())
    #
    # get_classifiers.short_name = _('classifiers')
    # get_classifiers.short_description = _('classifiers')


admin.site.register(Instrument, InstrumentAdmin)


class PriceHistoryAdmin(HistoricalAdmin):
    model = PriceHistory
    list_display = ['id', 'date', 'instrument', 'principal_price', 'accrued_price', 'factor']
    list_select_related = ['instrument']
    date_hierarchy = 'date'


admin.site.register(PriceHistory, PriceHistoryAdmin)
