from __future__ import unicode_literals

from django.contrib import admin
from mptt.admin import MPTTModelAdmin

from poms.counterparties.models import Counterparty, Responsible, CounterpartyClassifier


class ResponsibleAdmin(admin.ModelAdmin):
    model = Responsible


admin.site.register(Responsible, ResponsibleAdmin)


class CounterpartyClassifierAdmin(MPTTModelAdmin):
    model = CounterpartyClassifier
    list_display = ['name', 'master_user']
    mptt_level_indent = 20


admin.site.register(CounterpartyClassifier, CounterpartyClassifierAdmin)


class CounterpartyAdmin(admin.ModelAdmin):
    list_display = ['name', 'master_user']
    model = Counterparty


admin.site.register(Counterparty, CounterpartyAdmin)
