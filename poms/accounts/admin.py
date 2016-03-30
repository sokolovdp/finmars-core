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


class UserObjectPermissionInlineBase(admin.TabularInline):
    extra = 0

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'permission':
            qs = kwargs.get('queryset', db_field.remote_field.model.objects)
            ctype = ContentType.objects.get_for_model(self.parent_model)
            kwargs['queryset'] = qs.select_related('content_type').filter(content_type=ctype)
        return super(UserObjectPermissionInlineBase, self).formfield_for_foreignkey(db_field, request=request,
                                                                                    **kwargs)


# class AccountUserObjectPermissionInline(UserObjectPermissionInlineBase):
#     model = AccountUserObjectPermission
#
#
# class AccountGroupObjectPermissionInline(UserObjectPermissionInlineBase):
#     model = AccountGroupObjectPermission


class AccountAdmin(HistoricalAdmin):
    model = Account
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']
    # inlines = [AccountUserObjectPermissionInline, AccountGroupObjectPermissionInline]


admin.site.register(Account, AccountAdmin)


def register_object_perms_admin(*args):
    for model in args:
        if issubclass(model, UserObjectPermissionBase):
            admin.site.register(model, UserObjectPermissionAdmin)
        elif issubclass(model, GroupObjectPermissionBase):
            admin.site.register(model, GroupObjectPermissionAdmin)


register_object_perms_admin(AccountTypeUserObjectPermission, AccountTypeGroupObjectPermission,
                            AccountClassifierUserObjectPermission, AccountClassifierGroupObjectPermission,
                            AccountUserObjectPermission, AccountGroupObjectPermission)

# admin.site.register(AccountTypeUserObjectPermission, UserObjectPermissionAdmin)
# admin.site.register(AccountTypeGroupObjectPermission, GroupObjectPermissionAdmin)
# admin.site.register(AccountUserObjectPermission, UserObjectPermissionAdmin)
# admin.site.register(AccountGroupObjectPermission, GroupObjectPermissionAdmin)
