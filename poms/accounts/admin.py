from __future__ import unicode_literals

from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from reversion.admin import VersionAdmin

from poms.accounts.models import Account, AccountType, AccountClassifier


class AccountTypeAdmin(VersionAdmin):
    model = AccountType
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']


admin.site.register(AccountType, AccountTypeAdmin)


class AccountClassifierAdmin(VersionAdmin, MPTTModelAdmin):
    model = AccountClassifier
    list_display = ['id', 'name', 'parent', 'master_user']
    list_select_related = ['master_user']
    mptt_level_indent = 20
    mptt_indent_field = "name"


admin.site.register(AccountClassifier, AccountClassifierAdmin)


class AccountAdmin(VersionAdmin):
    model = Account
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']


admin.site.register(Account, AccountAdmin)
