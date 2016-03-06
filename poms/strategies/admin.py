from __future__ import unicode_literals

from django.contrib import admin

from poms.strategies.models import Strategy


class StrategyAdmin(admin.ModelAdmin):
    model = Strategy
    list_display = ['name', 'master_user']


admin.site.register(Strategy, StrategyAdmin)
