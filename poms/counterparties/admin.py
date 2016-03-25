from __future__ import unicode_literals

from django.contrib import admin
from mptt.admin import MPTTModelAdmin

from poms.audit.history import HistoricalAdmin
from poms.counterparties.models import Counterparty, Responsible, CounterpartyClassifier


class CounterpartyClassifierAdmin(HistoricalAdmin, MPTTModelAdmin):
    model = CounterpartyClassifier
    list_display = ['id', 'name', 'parent', 'master_user']
    list_select_related = ['master_user', 'parent']
    mptt_level_indent = 20
    mptt_indent_field = "name"


admin.site.register(CounterpartyClassifier, CounterpartyClassifierAdmin)


class CounterpartyAdmin(HistoricalAdmin):
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']
    model = Counterparty


admin.site.register(Counterparty, CounterpartyAdmin)


class ResponsibleAdmin(HistoricalAdmin):
    model = Responsible
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']


admin.site.register(Responsible, ResponsibleAdmin)
