from __future__ import unicode_literals

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from import_export.admin import ImportExportModelAdmin
from mptt.admin import MPTTModelAdmin

from poms.instruments.models import Instrument, PriceHistory, InstrumentClassifier


class InstrumentClassifierAdmin(MPTTModelAdmin):
    model = InstrumentClassifier
    list_display = ['id', 'name', 'parent', 'master_user']
    list_select_related = ['master_user', 'parent']
    mptt_level_indent = 20
    mptt_indent_field = "name"


admin.site.register(InstrumentClassifier, InstrumentClassifierAdmin)


class InstrumentAdmin(admin.ModelAdmin):
    model = Instrument
    list_display = ['id', 'name', 'master_user', 'pricing_currency', 'accrued_currency']
    list_select_related = ['master_user', 'pricing_currency', 'accrued_currency']

    # def get_classifiers(self, obj):
    #     return ', '.join(p.name for p in obj.classifiers.all())
    #
    # get_classifiers.short_name = _('classifiers')
    # get_classifiers.short_description = _('classifiers')


admin.site.register(Instrument, InstrumentAdmin)


class PriceHistoryAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    model = PriceHistory
    list_display = ['id', 'date', 'instrument', 'principal_price', 'accrued_price', 'factor']
    list_select_related = ['instrument']
    date_hierarchy = 'date'


admin.site.register(PriceHistory, PriceHistoryAdmin)
