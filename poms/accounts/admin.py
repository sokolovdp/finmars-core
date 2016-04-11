from __future__ import unicode_literals

from django.contrib import admin

from poms.accounts.models import Account, AccountType, AccountClassifier, AccountTypeUserObjectPermission, \
    AccountTypeGroupObjectPermission, AccountClassifierUserObjectPermission, AccountClassifierGroupObjectPermission, \
    AccountUserObjectPermission, AccountGroupObjectPermission, AccountAttributeType, \
    AccountAttributeTypeUserObjectPermission, AccountAttributeTypeGroupObjectPermission, AccountAttribute, \
    AccountAttributeTypeOption
from poms.audit.admin import HistoricalAdmin
from poms.common.admin import TreeModelAdmin
from poms.obj_attrs.admin import AttributeTypeAdminBase, AttributeInlineBase, AttributeTypeOptionInlineBase
from poms.obj_attrs.models import AttributeTypeOptionBase
from poms.obj_perms.admin import UserObjectPermissionAdmin, GroupObjectPermissionAdmin


class AccountTypeAdmin(HistoricalAdmin):
    model = AccountType
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']
    raw_id_fields = ['master_user']


admin.site.register(AccountType, AccountTypeAdmin)
admin.site.register(AccountTypeUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(AccountTypeGroupObjectPermission, GroupObjectPermissionAdmin)


class AccountClassifierAdmin(HistoricalAdmin, TreeModelAdmin):
    model = AccountClassifier
    list_display = ['id', 'formatted_name', 'parent', 'master_user']
    list_select_related = ['master_user']
    raw_id_fields = ['master_user', 'parent']


admin.site.register(AccountClassifier, AccountClassifierAdmin)
admin.site.register(AccountClassifierUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(AccountClassifierGroupObjectPermission, GroupObjectPermissionAdmin)


class AttributeInline(AttributeInlineBase):
    model = AccountAttribute


class AccountAdmin(HistoricalAdmin):
    model = Account
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']
    raw_id_fields = ['master_user', 'type']
    inlines = [AttributeInline]


admin.site.register(Account, AccountAdmin)
admin.site.register(AccountUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(AccountGroupObjectPermission, GroupObjectPermissionAdmin)


admin.site.register(AccountAttributeType, AttributeTypeAdminBase)
admin.site.register(AccountAttributeTypeOption, AttributeTypeOptionInlineBase)
admin.site.register(AccountAttributeTypeUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(AccountAttributeTypeGroupObjectPermission, GroupObjectPermissionAdmin)
