from __future__ import unicode_literals

from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from reversion.admin import VersionAdmin

from poms.accounts.models import Account, AccountType, AccountClassifier


class AccountTypeAdmin(VersionAdmin):
    model = AccountType
    list_display = ['name', 'master_user']


admin.site.register(AccountType, AccountTypeAdmin)


class AccountClassifierAdmin(VersionAdmin, MPTTModelAdmin):
    model = AccountClassifier
    list_display = ['name', 'parent', 'master_user']
    mptt_level_indent = 20


admin.site.register(AccountClassifier, AccountClassifierAdmin)


class AccountAdmin(VersionAdmin):
    model = Account
    list_display = ['name', 'master_user']


admin.site.register(Account, AccountAdmin)
