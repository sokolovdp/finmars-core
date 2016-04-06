from __future__ import unicode_literals

from django.contrib import admin
from mptt.admin import MPTTModelAdmin

from poms.audit.admin import HistoricalAdmin
from poms.counterparties.models import Counterparty, Responsible, CounterpartyClassifier, CounterpartyAttrValue, \
    ResponsibleAttrValue, ResponsibleClassifier
from poms.users.admin import AttrValueAdminBase


class CounterpartyClassifierAdmin(HistoricalAdmin, MPTTModelAdmin):
    model = CounterpartyClassifier
    list_display = ['id', 'name', 'parent', 'master_user']
    list_select_related = ['master_user', 'parent']
    mptt_level_indent = 20
    mptt_indent_field = "name"
    raw_id_fields = ['master_user', 'parent']


admin.site.register(CounterpartyClassifier, CounterpartyClassifierAdmin)


class CounterpartyAttrValueInline(AttrValueAdminBase):
    model = CounterpartyAttrValue


class CounterpartyAdmin(HistoricalAdmin):
    model = Counterparty
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']
    inlines = [CounterpartyAttrValueInline]
    raw_id_fields = ['master_user']


admin.site.register(Counterparty, CounterpartyAdmin)


class ResponsibleClassifierAdmin(HistoricalAdmin, MPTTModelAdmin):
    model = ResponsibleClassifier
    list_display = ['id', 'name', 'parent', 'master_user']
    list_select_related = ['master_user', 'parent']
    mptt_level_indent = 20
    mptt_indent_field = "name"
    raw_id_fields = ['master_user', 'parent']


admin.site.register(ResponsibleClassifier, ResponsibleClassifierAdmin)


class ResponsibleAttrValueInline(AttrValueAdminBase):
    model = ResponsibleAttrValue


class ResponsibleAdmin(HistoricalAdmin):
    model = Responsible
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']
    inlines = [ResponsibleAttrValueInline]
    raw_id_fields = ['master_user']


admin.site.register(Responsible, ResponsibleAdmin)
