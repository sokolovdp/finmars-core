from __future__ import unicode_literals

from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from reversion.admin import VersionAdmin

from poms.counterparties.models import Counterparty, Responsible, CounterpartyClassifier


class ResponsibleAdmin(VersionAdmin):
    model = Responsible


admin.site.register(Responsible, ResponsibleAdmin)


class CounterpartyClassifierAdmin(VersionAdmin, MPTTModelAdmin):
    model = CounterpartyClassifier
    list_display = ['name', 'parent', 'master_user']
    mptt_level_indent = 20


admin.site.register(CounterpartyClassifier, CounterpartyClassifierAdmin)


class CounterpartyAdmin(VersionAdmin):
    list_display = ['name', 'master_user']
    model = Counterparty


admin.site.register(Counterparty, CounterpartyAdmin)
