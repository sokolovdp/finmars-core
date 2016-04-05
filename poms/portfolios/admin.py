from __future__ import unicode_literals

from django.contrib import admin
from mptt.admin import MPTTModelAdmin

from poms.audit.admin import HistoricalAdmin
from poms.portfolios.models import Portfolio, PortfolioClassifier, PortfolioTag, PortfolioAttrValue


class PortfolioClassifierAdmin(HistoricalAdmin, MPTTModelAdmin):
    model = PortfolioClassifier
    list_display = ['id', 'name', 'parent', 'master_user']
    list_select_related = ['master_user', 'parent']
    mptt_level_indent = 20
    mptt_indent_field = "name"


admin.site.register(PortfolioClassifier, PortfolioClassifierAdmin)


class PortfolioTagAdmin(HistoricalAdmin):
    model = PortfolioTag
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']


admin.site.register(PortfolioTag, PortfolioTagAdmin)


class PortfolioAttrValueInline(admin.StackedInline):
    model = PortfolioAttrValue
    ordering = ['portfolio', 'attr__order']
    extra = 0


class PortfolioAdmin(HistoricalAdmin):
    model = Portfolio
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']
    filter_horizontal = ['tags', ]
    inlines = [PortfolioAttrValueInline]


admin.site.register(Portfolio, PortfolioAdmin)
