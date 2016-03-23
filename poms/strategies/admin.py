from __future__ import unicode_literals

from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from reversion.admin import VersionAdmin

from poms.strategies.models import Strategy


class StrategyAdmin(VersionAdmin, MPTTModelAdmin):
    model = Strategy
    list_display = ['name', 'parent', 'master_user']
    mptt_level_indent = 20


admin.site.register(Strategy, StrategyAdmin)
