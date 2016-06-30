from __future__ import unicode_literals

from django.contrib import admin

from poms.audit.admin import HistoricalAdmin
from poms.common.admin import ClassifierAdmin
from poms.obj_attrs.admin import AttributeTypeAdminBase, AttributeTypeOptionAdminBase, AttributeInlineBase, \
    AttributeTypeClassifierInlineBase
from poms.obj_perms.admin import GroupObjectPermissionAdmin, UserObjectPermissionAdmin
from poms.portfolios.models import Portfolio, PortfolioClassifier, PortfolioGroupObjectPermission, \
    PortfolioAttributeType, PortfolioAttributeTypeOption, PortfolioAttributeTypeGroupObjectPermission, \
    PortfolioAttribute, PortfolioUserObjectPermission, PortfolioAttributeTypeUserObjectPermission

admin.site.register(PortfolioClassifier, ClassifierAdmin)


# admin.site.register(PortfolioClassifierUserObjectPermission, UserObjectPermissionAdmin)
# admin.site.register(PortfolioClassifierGroupObjectPermission, GroupObjectPermissionAdmin)


class PortfolioAttributeInline(AttributeInlineBase):
    model = PortfolioAttribute


class PortfolioAdmin(HistoricalAdmin):
    model = Portfolio
    list_display = ['id', 'master_user', 'name']
    list_select_related = ['master_user']
    raw_id_fields = ['master_user']
    filter_horizontal = ['accounts', 'responsibles', 'counterparties', 'transaction_types']
    inlines = [PortfolioAttributeInline]


admin.site.register(Portfolio, PortfolioAdmin)
admin.site.register(PortfolioUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(PortfolioGroupObjectPermission, GroupObjectPermissionAdmin)


class PortfolioAttributeTypeClassifierInline(AttributeTypeClassifierInlineBase):
    model = PortfolioClassifier


class AccountAttributeTypeAdmin(AttributeTypeAdminBase):
    inlines = [PortfolioAttributeTypeClassifierInline]


admin.site.register(PortfolioAttributeType, AccountAttributeTypeAdmin)
admin.site.register(PortfolioAttributeTypeOption, AttributeTypeOptionAdminBase)
admin.site.register(PortfolioAttributeTypeUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(PortfolioAttributeTypeGroupObjectPermission, GroupObjectPermissionAdmin)
