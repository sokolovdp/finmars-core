from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from mptt.admin import MPTTModelAdmin

from poms.accounts.models import Account, AccountType, AccountClassifier, AccountTypeUserObjectPermission, \
    AccountTypeGroupObjectPermission, AccountUserObjectPermission, AccountGroupObjectPermission, \
    AccountClassifierUserObjectPermission, AccountClassifierGroupObjectPermission
from poms.audit.admin import HistoricalAdmin
from poms.users.admin import UserObjectPermissionAdmin, GroupObjectPermissionAdmin
from poms.users.models import UserObjectPermissionBase, GroupObjectPermissionBase


class AccountTypeAdmin(HistoricalAdmin):
    model = AccountType
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']


admin.site.register(AccountType, AccountTypeAdmin)


class AccountClassifierAdmin(HistoricalAdmin, MPTTModelAdmin):
    model = AccountClassifier
    list_display = ['id', 'name', 'parent', 'master_user']
    list_select_related = ['master_user']
    mptt_level_indent = 20
    mptt_indent_field = "name"


admin.site.register(AccountClassifier, AccountClassifierAdmin)


class AccountAdmin(HistoricalAdmin):
    model = Account
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']


admin.site.register(Account, AccountAdmin)


admin.site.register(AccountTypeUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(AccountTypeGroupObjectPermission, GroupObjectPermissionAdmin)
admin.site.register(AccountClassifierUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(AccountClassifierGroupObjectPermission, GroupObjectPermissionAdmin)
admin.site.register(AccountUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(AccountGroupObjectPermission, GroupObjectPermissionAdmin)

