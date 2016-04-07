from __future__ import unicode_literals

from django.contrib import admin

from poms.audit.admin import HistoricalAdmin
from poms.common.admin import TreeModelAdmin
from poms.counterparties.models import Counterparty, Responsible, CounterpartyClassifier, ResponsibleClassifier
from poms.obj_attrs.admin import AttrValueInlineBase
from poms.obj_attrs.models import CounterpartyAttrValue, ResponsibleAttrValue


class CounterpartyClassifierAdmin(HistoricalAdmin, TreeModelAdmin):
    model = CounterpartyClassifier
    list_display = ['id', 'formatted_name', 'parent', 'master_user']
    list_select_related = ['master_user', 'parent']
    raw_id_fields = ['master_user', 'parent']


admin.site.register(CounterpartyClassifier, CounterpartyClassifierAdmin)


class CounterpartyAttrValueInline(AttrValueInlineBase):
    model = CounterpartyAttrValue


class CounterpartyAdmin(HistoricalAdmin):
    model = Counterparty
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']
    inlines = [CounterpartyAttrValueInline]
    raw_id_fields = ['master_user']


admin.site.register(Counterparty, CounterpartyAdmin)


class ResponsibleClassifierAdmin(HistoricalAdmin, TreeModelAdmin):
    model = ResponsibleClassifier
    list_display = ['id', 'formatted_name', 'parent', 'master_user']
    list_select_related = ['master_user', 'parent']
    raw_id_fields = ['master_user', 'parent']


admin.site.register(ResponsibleClassifier, ResponsibleClassifierAdmin)


class ResponsibleAttrValueInline(AttrValueInlineBase):
    model = ResponsibleAttrValue


class ResponsibleAdmin(HistoricalAdmin):
    model = Responsible
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']
    inlines = [ResponsibleAttrValueInline]
    raw_id_fields = ['master_user']


admin.site.register(Responsible, ResponsibleAdmin)
