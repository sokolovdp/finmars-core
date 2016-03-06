from __future__ import unicode_literals

from django.contrib import admin
from guardian.admin import GuardedModelAdmin
from mptt.admin import MPTTModelAdmin
from reversion.admin import VersionAdmin

from poms.accounts.models import Account, AccountType, AccountClassifier


class AccountTypeAdmin(VersionAdmin):
    model = AccountType
    list_display = ['code', 'name']
    ordering = ['code']


admin.site.register(AccountType, AccountTypeAdmin)


class AccountClassifierAdmin(MPTTModelAdmin):
    model = AccountClassifier
    list_display = ['name', 'master_user']
    mptt_level_indent = 20


admin.site.register(AccountClassifier, AccountClassifierAdmin)


class AccountAdmin(VersionAdmin, GuardedModelAdmin):
    model = Account
    list_display = ['name', 'master_user']


admin.site.register(Account, AccountAdmin)
