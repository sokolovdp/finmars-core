from __future__ import unicode_literals

from django.contrib import admin

from poms.audit.admin import HistoricalAdmin
from poms.common.admin import TreeModelAdmin
from poms.obj_attrs.admin import AttributeTypeAdminBase, AttributeTypeOptionInlineBase, AttributeInlineBase
from poms.obj_perms.admin import UserObjectPermissionAdmin, GroupObjectPermissionAdmin
from poms.portfolios.models import Portfolio, PortfolioClassifier, PortfolioClassifierUserObjectPermission, \
    PortfolioClassifierGroupObjectPermission, PortfolioGroupObjectPermission, PortfolioUserObjectPermission, \
    PortfolioAttributeType, PortfolioAttributeTypeOption, PortfolioAttributeTypeUserObjectPermission, \
    PortfolioAttributeTypeGroupObjectPermission, PortfolioAttribute


class PortfolioClassifierAdmin(HistoricalAdmin, TreeModelAdmin):
    model = PortfolioClassifier
    list_display = ['id', 'master_user', 'formatted_name', 'parent']
    list_select_related = ['master_user', 'parent']
    raw_id_fields = ['master_user', 'parent']


admin.site.register(PortfolioClassifier, PortfolioClassifierAdmin)
admin.site.register(PortfolioClassifierUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(PortfolioClassifierGroupObjectPermission, GroupObjectPermissionAdmin)


class PortfolioAttributeInline(AttributeInlineBase):
    model = PortfolioAttribute


class PortfolioAdmin(HistoricalAdmin):
    model = Portfolio
    list_display = ['id', 'master_user', 'name']
    list_select_related = ['master_user']
    raw_id_fields = ['master_user']
    inlines = [PortfolioAttributeInline]


admin.site.register(Portfolio, PortfolioAdmin)
admin.site.register(PortfolioUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(PortfolioGroupObjectPermission, GroupObjectPermissionAdmin)

admin.site.register(PortfolioAttributeType, AttributeTypeAdminBase)
admin.site.register(PortfolioAttributeTypeOption, AttributeTypeOptionInlineBase)
admin.site.register(PortfolioAttributeTypeUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(PortfolioAttributeTypeGroupObjectPermission, GroupObjectPermissionAdmin)
