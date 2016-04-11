from __future__ import unicode_literals

from django.contrib import admin

from poms.audit.admin import HistoricalAdmin
from poms.common.admin import TreeModelAdmin
from poms.counterparties.models import Counterparty, Responsible, CounterpartyClassifier, ResponsibleClassifier


class CounterpartyClassifierAdmin(HistoricalAdmin, TreeModelAdmin):
    model = CounterpartyClassifier
    list_display = ['id', 'formatted_name', 'parent', 'master_user']
    list_select_related = ['master_user', 'parent']
    raw_id_fields = ['master_user', 'parent']


admin.site.register(CounterpartyClassifier, CounterpartyClassifierAdmin)


class CounterpartyAdmin(HistoricalAdmin):
    model = Counterparty
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']
    raw_id_fields = ['master_user']


admin.site.register(Counterparty, CounterpartyAdmin)


class ResponsibleClassifierAdmin(HistoricalAdmin, TreeModelAdmin):
    model = ResponsibleClassifier
    list_display = ['id', 'formatted_name', 'parent', 'master_user']
    list_select_related = ['master_user', 'parent']
    raw_id_fields = ['master_user', 'parent']


admin.site.register(ResponsibleClassifier, ResponsibleClassifierAdmin)


class ResponsibleAdmin(HistoricalAdmin):
    model = Responsible
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']
    raw_id_fields = ['master_user']


admin.site.register(Responsible, ResponsibleAdmin)
