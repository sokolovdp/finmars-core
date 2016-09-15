from __future__ import unicode_literals

from django.contrib import admin

from poms.audit.admin import HistoricalAdmin
from poms.common.admin import ClassifierAdmin
from poms.obj_attrs.admin import AbstractAttributeTypeAdmin, AbstractAttributeInline, \
    AbstractAttributeTypeClassifierInline, AbstractAttributeTypeOptionInline
from poms.obj_perms.admin import UserObjectPermissionInline, GroupObjectPermissionInline
from poms.portfolios.models import Portfolio, PortfolioAttributeType, PortfolioClassifier


class PortfolioAdmin(HistoricalAdmin):
    model = Portfolio
    list_display = ['id', 'master_user', 'name', 'is_deleted', ]
    list_select_related = ['master_user']
    list_filter = ['is_deleted', ]
    raw_id_fields = ['master_user', 'accounts', 'responsibles', 'counterparties', 'transaction_types']
    inlines = [
        AbstractAttributeInline,
        UserObjectPermissionInline,
        GroupObjectPermissionInline,
    ]


admin.site.register(Portfolio, PortfolioAdmin)


class PortfolioAttributeTypeAdmin(AbstractAttributeTypeAdmin):
    inlines = [
        AbstractAttributeTypeClassifierInline,
        AbstractAttributeTypeOptionInline,
        UserObjectPermissionInline,
        GroupObjectPermissionInline,
    ]


admin.site.register(PortfolioAttributeType, PortfolioAttributeTypeAdmin)

admin.site.register(PortfolioClassifier, ClassifierAdmin)
