from __future__ import unicode_literals

from django.contrib import admin

from poms.accounts.models import Account, AccountType, AccountClassifier, AccountTypeGroupObjectPermission, \
    AccountGroupObjectPermission, AccountAttributeType, AccountAttributeTypeGroupObjectPermission, AccountAttribute, \
    AccountAttributeTypeOption, AccountTypeUserObjectPermission, AccountUserObjectPermission, \
    AccountAttributeTypeUserObjectPermission
from poms.audit.admin import HistoricalAdmin
from poms.common.admin import ClassifierAdmin
from poms.obj_attrs.admin import AttributeTypeAdminBase, AttributeInlineBase, AttributeTypeOptionAdminBase, \
    AttributeTypeClassifierInlineBase
from poms.obj_perms.admin import GroupObjectPermissionAdmin, UserObjectPermissionAdmin


class AccountTypeAdmin(HistoricalAdmin):
    model = AccountType
    list_display = ['id', 'master_user', 'name', ]
    list_select_related = ['master_user']
    raw_id_fields = ['master_user']


admin.site.register(AccountType, AccountTypeAdmin)
admin.site.register(AccountTypeUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(AccountTypeGroupObjectPermission, GroupObjectPermissionAdmin)


class AccountAttributeInline(AttributeInlineBase):
    model = AccountAttribute


class AccountAdmin(HistoricalAdmin):
    model = Account
    list_display = ['id', 'master_user', 'name', 'type']
    list_select_related = ['master_user', 'type']
    raw_id_fields = ['master_user', 'type']
    inlines = [AccountAttributeInline]


admin.site.register(Account, AccountAdmin)
admin.site.register(AccountUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(AccountGroupObjectPermission, GroupObjectPermissionAdmin)


class AccountAttributeTypeClassifierInline(AttributeTypeClassifierInlineBase):
    model = AccountClassifier


class AccountAttributeTypeAdmin(AttributeTypeAdminBase):
    inlines = [AccountAttributeTypeClassifierInline]


admin.site.register(AccountAttributeType, AccountAttributeTypeAdmin)
admin.site.register(AccountAttributeTypeOption, AttributeTypeOptionAdminBase)
admin.site.register(AccountAttributeTypeUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(AccountAttributeTypeGroupObjectPermission, GroupObjectPermissionAdmin)

admin.site.register(AccountClassifier, ClassifierAdmin)
# admin.site.register(AccountClassifierUserObjectPermission, UserObjectPermissionAdmin)
# admin.site.register(AccountClassifierGroupObjectPermission, GroupObjectPermissionAdmin)
