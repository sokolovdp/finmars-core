from __future__ import unicode_literals

from django.contrib import admin
from mptt.admin import MPTTModelAdmin

from poms.audit.mixins import HistoricalAdmin
from poms.portfolios.models import Portfolio, PortfolioClassifier


class PortfolioClassifierAdmin(HistoricalAdmin, MPTTModelAdmin):
    model = PortfolioClassifier
    list_display = ['id', 'name', 'parent', 'master_user']
    list_select_related = ['master_user', 'parent']
    mptt_level_indent = 20
    mptt_indent_field = "name"


admin.site.register(PortfolioClassifier, PortfolioClassifierAdmin)


class PortfolioAdmin(HistoricalAdmin):
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']
    model = Portfolio


admin.site.register(Portfolio, PortfolioAdmin)
