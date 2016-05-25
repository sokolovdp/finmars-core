from __future__ import unicode_literals

from django.contrib import admin

from poms.accounts.models import Account, AccountType, AccountClassifier, AccountTypeGroupObjectPermission, \
    AccountGroupObjectPermission, AccountAttributeType, AccountAttributeTypeGroupObjectPermission, AccountAttribute, \
    AccountAttributeTypeOption
from poms.audit.admin import HistoricalAdmin
from poms.common.admin import ClassifierAdmin
from poms.obj_attrs.admin import AttributeTypeAdminBase, AttributeInlineBase, AttributeTypeOptionInlineBase
from poms.obj_perms.admin import GroupObjectPermissionAdmin


class AccountTypeAdmin(HistoricalAdmin):
    model = AccountType
    list_display = ['id', 'master_user', 'name', ]
    list_select_related = ['master_user']
    raw_id_fields = ['master_user']


admin.site.register(AccountType, AccountTypeAdmin)
# admin.site.register(AccountTypeUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(AccountTypeGroupObjectPermission, GroupObjectPermissionAdmin)

admin.site.register(AccountClassifier, ClassifierAdmin)
# admin.site.register(AccountClassifierUserObjectPermission, UserObjectPermissionAdmin)
# admin.site.register(AccountClassifierGroupObjectPermission, GroupObjectPermissionAdmin)


class AccountAttributeInline(AttributeInlineBase):
    model = AccountAttribute


class AccountAdmin(HistoricalAdmin):
    model = Account
    list_display = ['id', 'master_user', 'name', 'type']
    list_select_related = ['master_user', 'type']
    raw_id_fields = ['master_user', 'type']
    inlines = [AccountAttributeInline]


admin.site.register(Account, AccountAdmin)
# admin.site.register(AccountUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(AccountGroupObjectPermission, GroupObjectPermissionAdmin)

admin.site.register(AccountAttributeType, AttributeTypeAdminBase)
admin.site.register(AccountAttributeTypeOption, AttributeTypeOptionInlineBase)
# admin.site.register(AccountAttributeTypeUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(AccountAttributeTypeGroupObjectPermission, GroupObjectPermissionAdmin)
