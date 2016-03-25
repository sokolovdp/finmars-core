from __future__ import unicode_literals

from django.contrib import admin
from mptt.admin import MPTTModelAdmin

from poms.audit.history import HistoricalAdmin
from poms.strategies.models import Strategy


class StrategyAdmin(HistoricalAdmin, MPTTModelAdmin):
    model = Strategy
    list_display = ['id', 'name', 'parent', 'master_user']
    list_select_related = ['master_user']
    mptt_level_indent = 20
    mptt_indent_field = "name"


admin.site.register(Strategy, StrategyAdmin)
