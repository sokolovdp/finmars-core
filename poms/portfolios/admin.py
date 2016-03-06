from __future__ import unicode_literals

from django.contrib import admin
from mptt.admin import MPTTModelAdmin

from poms.portfolios.models import Portfolio, PortfolioClassifier


class PortfolioClassifierAdmin(MPTTModelAdmin):
    model = PortfolioClassifier
    list_display = ['name', 'master_user']
    mptt_level_indent = 20


admin.site.register(PortfolioClassifier, PortfolioClassifierAdmin)


class PortfolioAdmin(admin.ModelAdmin):
    model = Portfolio


admin.site.register(Portfolio, PortfolioAdmin)
