from __future__ import unicode_literals

from django.contrib import admin

from poms.audit.admin import HistoricalAdmin
from poms.common.admin import TreeModelAdmin
from poms.strategies.models import Strategy


class StrategyAdmin(HistoricalAdmin, TreeModelAdmin):
    model = Strategy
    list_display = ['id', 'formatted_name', 'parent', 'master_user']
    list_select_related = ['master_user', 'parent']
    raw_id_fields = ['master_user', 'parent']


admin.site.register(Strategy, StrategyAdmin)
