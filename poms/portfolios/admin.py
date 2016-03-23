from __future__ import unicode_literals

from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from reversion.admin import VersionAdmin

from poms.portfolios.models import Portfolio, PortfolioClassifier


class PortfolioClassifierAdmin(VersionAdmin, MPTTModelAdmin):
    model = PortfolioClassifier
    list_display = ['name', 'parent', 'master_user']
    mptt_level_indent = 20


admin.site.register(PortfolioClassifier, PortfolioClassifierAdmin)


class PortfolioAdmin(VersionAdmin):
    model = Portfolio


admin.site.register(Portfolio, PortfolioAdmin)
