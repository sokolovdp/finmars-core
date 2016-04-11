from __future__ import unicode_literals

from django.contrib import admin

from poms.audit.admin import HistoricalAdmin
from poms.common.admin import TreeModelAdmin
from poms.portfolios.models import Portfolio, PortfolioClassifier


class PortfolioClassifierAdmin(HistoricalAdmin, TreeModelAdmin):
    model = PortfolioClassifier
    list_display = ['id', 'formatted_name', 'parent', 'master_user']
    list_select_related = ['master_user', 'parent']
    raw_id_fields = ['master_user', 'parent']


admin.site.register(PortfolioClassifier, PortfolioClassifierAdmin)


class PortfolioAdmin(HistoricalAdmin):
    model = Portfolio
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']
    raw_id_fields = ['master_user']


admin.site.register(Portfolio, PortfolioAdmin)
