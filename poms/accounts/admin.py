from __future__ import unicode_literals

from django.contrib import admin

from poms.accounts.models import Account, AccountType, AccountClassifier, AccountAttrValue
from poms.audit.admin import HistoricalAdmin
from poms.common.admin import TreeModelAdmin
from poms.users.admin import AttrValueAdminBase


class AccountTypeAdmin(HistoricalAdmin):
    model = AccountType
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']
    raw_id_fields = ['master_user']


admin.site.register(AccountType, AccountTypeAdmin)


class AccountClassifierAdmin(HistoricalAdmin, TreeModelAdmin):
    model = AccountClassifier
    list_display = ['id', 'formatted_name', 'parent', 'master_user']
    list_select_related = ['master_user']
    raw_id_fields = ['master_user', 'parent']


admin.site.register(AccountClassifier, AccountClassifierAdmin)


class AccountAttrValueInline(AttrValueAdminBase):
    model = AccountAttrValue


class AccountAdmin(HistoricalAdmin):
    model = Account
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']
    raw_id_fields = ['master_user', 'type']
    inlines = [AccountAttrValueInline]

    # related_lookup_fields = {
    #     'fk': ['master_user', 'type'],
    #     'm2m': ['tags'],
    # }
    # autocomplete_lookup_fields = {
    #     'fk': ['master_user', 'type'],
    #     'm2m': ['tags'],
    # }


admin.site.register(Account, AccountAdmin)


# admin.site.register(AccountTypeUserObjectPermission, UserObjectPermissionAdmin)
# admin.site.register(AccountTypeGroupObjectPermission, GroupObjectPermissionAdmin)
# admin.site.register(AccountClassifierUserObjectPermission, UserObjectPermissionAdmin)
# admin.site.register(AccountClassifierGroupObjectPermission, GroupObjectPermissionAdmin)
# admin.site.register(AccountUserObjectPermission, UserObjectPermissionAdmin)
# admin.site.register(AccountGroupObjectPermission, GroupObjectPermissionAdmin)
