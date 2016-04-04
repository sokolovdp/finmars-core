from __future__ import unicode_literals

from django.contrib import admin
from django.utils.html import format_html
from mptt.admin import MPTTModelAdmin

from poms.audit.admin import HistoricalAdmin
from poms.strategies.models import Strategy
from django.utils.translation import ugettext_lazy as _


class StrategyAdmin(HistoricalAdmin, MPTTModelAdmin):
    model = Strategy
    list_display = ['id', 'formatted_name', 'parent', 'master_user']
    list_select_related = ['master_user']
    mptt_level_indent = 20
    mptt_indent_field = "name"

    def formatted_name(self, obj):
        return format_html('<div style="padding-left: {}px">{}</div>', self.mptt_level_indent*obj.level, obj.name)
    formatted_name.short_description = _('name')


admin.site.register(Strategy, StrategyAdmin)
