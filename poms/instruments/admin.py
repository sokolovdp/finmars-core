from __future__ import unicode_literals

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from import_export.admin import ImportExportModelAdmin
from mptt.admin import MPTTModelAdmin
from reversion.admin import VersionAdmin

from poms.instruments.models import Instrument, PriceHistory, InstrumentClassifier


class InstrumentClassifierAdmin(VersionAdmin, MPTTModelAdmin):
    # change_list_template = 'admin/mptt_change_list.html'
    model = InstrumentClassifier
    list_display = ['name', 'parent', 'master_user']
    mptt_level_indent = 20


admin.site.register(InstrumentClassifier, InstrumentClassifierAdmin)


class InstrumentAdmin(VersionAdmin):
    model = Instrument
    list_display = ['name', 'pricing_currency', 'accrued_currency', 'price_multiplier', 'master_user']

    # def get_classifiers(self, obj):
    #     return ', '.join(p.name for p in obj.classifiers.all())
    #
    # get_classifiers.short_name = _('classifiers')
    # get_classifiers.short_description = _('classifiers')


admin.site.register(Instrument, InstrumentAdmin)


class PriceHistoryAdmin(VersionAdmin, ImportExportModelAdmin):
    model = PriceHistory
    list_display = ['id', 'date', 'instrument', 'principal_price', 'accrued_price', 'factor']
    date_hierarchy = 'date'


admin.site.register(PriceHistory, PriceHistoryAdmin)
