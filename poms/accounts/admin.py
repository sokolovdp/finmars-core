from __future__ import unicode_literals

from django.contrib import admin
from guardian.admin import GuardedModelAdminMixin
from mptt.admin import MPTTModelAdmin

from poms.accounts.models import Account, AccountType, AccountClassifier, AccountUserObjectPermission, \
    AccountGroupObjectPermission
from poms.audit.admin import HistoricalAdmin


class AccountTypeAdmin(GuardedModelAdminMixin, HistoricalAdmin):
    model = AccountType
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']


admin.site.register(AccountType, AccountTypeAdmin)


class AccountClassifierAdmin(GuardedModelAdminMixin, HistoricalAdmin, MPTTModelAdmin):
    model = AccountClassifier
    list_display = ['id', 'name', 'parent', 'master_user']
    list_select_related = ['master_user']
    mptt_level_indent = 20
    mptt_indent_field = "name"


admin.site.register(AccountClassifier, AccountClassifierAdmin)


class AccountUserObjectPermissionInline(admin.TabularInline):
    model = AccountUserObjectPermission
    extra = 0

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'permission':
            qs = kwargs.get('queryset', db_field.remote_field.model.objects)
            kwargs['queryset'] = qs.select_related('content_type')
        return super(AccountUserObjectPermissionInline, self).formfield_for_foreignkey(db_field, request=request,
                                                                                       **kwargs)


class AccountGroupObjectPermissionInline(admin.TabularInline):
    model = AccountGroupObjectPermission
    extra = 0

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'permission':
            qs = kwargs.get('queryset', db_field.remote_field.model.objects)
            kwargs['queryset'] = qs.select_related('content_type')
        return super(AccountGroupObjectPermissionInline, self).formfield_for_foreignkey(db_field, request=request,
                                                                                        **kwargs)


class AccountAdmin(GuardedModelAdminMixin, HistoricalAdmin):
    model = Account
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']
    inlines = [AccountUserObjectPermissionInline, AccountGroupObjectPermissionInline]


admin.site.register(Account, AccountAdmin)
