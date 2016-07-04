from __future__ import unicode_literals

from django.contrib import admin

from poms.accounts.models import Account, AccountType, AccountAttributeType
from poms.audit.admin import HistoricalAdmin
from poms.obj_attrs.admin import AbstractAttributeTypeAdmin, AbstractAttributeInline, \
    AbstractAttributeTypeClassifierInline, AbstractAttributeTypeOptionInline
from poms.obj_perms.admin import UserObjectPermissionInline, \
    GroupObjectPermissionInline


class AccountTypeAdmin(HistoricalAdmin):
    model = AccountType
    list_display = ['id', 'master_user', 'name', ]
    list_select_related = ['master_user']
    raw_id_fields = ['master_user']
    inlines = [
        UserObjectPermissionInline,
        GroupObjectPermissionInline,
    ]


admin.site.register(AccountType, AccountTypeAdmin)


# admin.site.register(AccountTypeUserObjectPermission, UserObjectPermissionAdmin)
# admin.site.register(AccountTypeGroupObjectPermission, GroupObjectPermissionAdmin)


# class AccountAttributeInline(AbstractAttributeInline):
#     model = AccountAttribute


class AccountAdmin(HistoricalAdmin):
    model = Account
    list_display = ['id', 'master_user', 'name', 'type']
    list_select_related = ['master_user', 'type']
    raw_id_fields = ['master_user', 'type']
    inlines = [
        AbstractAttributeInline,
        UserObjectPermissionInline,
        GroupObjectPermissionInline,
    ]


admin.site.register(Account, AccountAdmin)


# admin.site.register(AccountUserObjectPermission, UserObjectPermissionAdmin)
# admin.site.register(AccountGroupObjectPermission, GroupObjectPermissionAdmin)


# class AccountAttributeTypeClassifierInline(AbstractAttributeTypeClassifierInline):
#     model = AccountClassifier


class AccountAttributeTypeAdmin(AbstractAttributeTypeAdmin):
    inlines = [
        AbstractAttributeTypeClassifierInline,
        AbstractAttributeTypeOptionInline,
        UserObjectPermissionInline,
        GroupObjectPermissionInline,
    ]


admin.site.register(AccountAttributeType, AccountAttributeTypeAdmin)
# admin.site.register(AccountAttributeTypeOption, AbstractAttributeTypeOptionAdmin)
# admin.site.register(AccountAttributeTypeUserObjectPermission, UserObjectPermissionAdmin)
# admin.site.register(AccountAttributeTypeGroupObjectPermission, GroupObjectPermissionAdmin)

# admin.site.register(AccountClassifier, ClassifierAdmin)
# admin.site.register(AccountClassifierUserObjectPermission, UserObjectPermissionAdmin)
# admin.site.register(AccountClassifierGroupObjectPermission, GroupObjectPermissionAdmin)
