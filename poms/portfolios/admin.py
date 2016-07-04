from __future__ import unicode_literals

from django.contrib import admin

from poms.audit.admin import HistoricalAdmin
from poms.obj_attrs.admin import AbstractAttributeTypeAdmin, AbstractAttributeInline, \
    AbstractAttributeTypeClassifierInline, AbstractAttributeTypeOptionInline
from poms.obj_perms.admin import UserObjectPermissionInline, GroupObjectPermissionInline
from poms.portfolios.models import Portfolio, PortfolioAttributeType


# class PortfolioAttributeInline(AbstractAttributeInline):
#     model = PortfolioAttribute


class PortfolioAdmin(HistoricalAdmin):
    model = Portfolio
    list_display = ['id', 'master_user', 'name']
    list_select_related = ['master_user']
    raw_id_fields = ['master_user']
    filter_horizontal = ['accounts', 'responsibles', 'counterparties', 'transaction_types']
    # inlines = [PortfolioAttributeInline]
    inlines = [
        AbstractAttributeInline,
        UserObjectPermissionInline,
        GroupObjectPermissionInline,
    ]


admin.site.register(Portfolio, PortfolioAdmin)


# admin.site.register(PortfolioUserObjectPermission, UserObjectPermissionAdmin)
# admin.site.register(PortfolioGroupObjectPermission, GroupObjectPermissionAdmin)


# class PortfolioAttributeTypeClassifierInline(AbstractAttributeTypeClassifierInline):
#     model = PortfolioClassifier


class PortfolioAttributeTypeAdmin(AbstractAttributeTypeAdmin):
    # inlines = [PortfolioAttributeTypeClassifierInline]
    inlines = [
        AbstractAttributeTypeClassifierInline,
        AbstractAttributeTypeOptionInline,
        UserObjectPermissionInline,
        GroupObjectPermissionInline,
    ]


admin.site.register(PortfolioAttributeType, PortfolioAttributeTypeAdmin)
# admin.site.register(PortfolioAttributeTypeOption, AbstractAttributeTypeOptionAdmin)
# admin.site.register(PortfolioAttributeTypeUserObjectPermission, UserObjectPermissionAdmin)
# admin.site.register(PortfolioAttributeTypeGroupObjectPermission, GroupObjectPermissionAdmin)
# admin.site.register(PortfolioClassifier, ClassifierAdmin)
