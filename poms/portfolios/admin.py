from __future__ import unicode_literals

from django.contrib import admin

from poms.common.admin import ClassifierAdmin
from poms.obj_attrs.admin import AbstractAttributeTypeAdmin, AbstractAttributeInline, \
    AbstractAttributeTypeClassifierInline, AbstractAttributeTypeOptionInline, GenericAttributeInline
from poms.obj_perms.admin import GenericObjectPermissionInline
from poms.portfolios.models import Portfolio, PortfolioAttributeType, PortfolioClassifier


class PortfolioAdmin(admin.ModelAdmin):
    model = Portfolio
    list_display = ['id', 'master_user', 'user_code', 'name', 'is_deleted', ]
    list_select_related = ['master_user']
    search_fields = ['id', 'user_code', 'name']
    list_filter = ['is_deleted', ]
    raw_id_fields = ['master_user', 'accounts', 'responsibles', 'counterparties', 'transaction_types']
    inlines = [
        AbstractAttributeInline,
        GenericAttributeInline,
        GenericObjectPermissionInline,
        # UserObjectPermissionInline,
        # GroupObjectPermissionInline,
    ]


admin.site.register(Portfolio, PortfolioAdmin)


class PortfolioAttributeTypeAdmin(AbstractAttributeTypeAdmin):
    inlines = [
        AbstractAttributeTypeClassifierInline,
        AbstractAttributeTypeOptionInline,
        GenericObjectPermissionInline,
        # UserObjectPermissionInline,
        # GroupObjectPermissionInline,
    ]


admin.site.register(PortfolioAttributeType, PortfolioAttributeTypeAdmin)

admin.site.register(PortfolioClassifier, ClassifierAdmin)
