from __future__ import unicode_literals

from django.contrib import admin

from poms.accounts.models import Account, AccountType, AccountAttributeType, AccountClassifier
from poms.audit.admin import HistoricalAdmin
from poms.common.admin import ClassifierAdmin
from poms.obj_attrs.admin import AbstractAttributeTypeAdmin, AbstractAttributeInline, \
    AbstractAttributeTypeClassifierInline, AbstractAttributeTypeOptionInline
from poms.obj_perms.admin import UserObjectPermissionInline, \
    GroupObjectPermissionInline


class AccountTypeAdmin(HistoricalAdmin):
    model = AccountType
    list_display = ['id', 'master_user', 'name', 'is_deleted', ]
    list_select_related = ['master_user']
    list_filter = ['is_deleted', ]
    search_fields = ['id', 'user_code', 'name']
    raw_id_fields = ['master_user']
    inlines = [
        UserObjectPermissionInline,
        GroupObjectPermissionInline,
    ]


admin.site.register(AccountType, AccountTypeAdmin)


class AccountAdmin(HistoricalAdmin):
    model = Account
    list_display = ['id', 'master_user', 'name', 'type', 'is_deleted', ]
    list_select_related = ['master_user', 'type']
    list_filter = ['is_deleted', ]
    search_fields = ['id', 'user_code', 'name']
    raw_id_fields = ['master_user', 'type']
    inlines = [
        AbstractAttributeInline,
        UserObjectPermissionInline,
        GroupObjectPermissionInline,
    ]


admin.site.register(Account, AccountAdmin)


class AccountAttributeTypeAdmin(AbstractAttributeTypeAdmin):
    inlines = [
        AbstractAttributeTypeClassifierInline,
        AbstractAttributeTypeOptionInline,
        UserObjectPermissionInline,
        GroupObjectPermissionInline,
    ]


admin.site.register(AccountAttributeType, AccountAttributeTypeAdmin)

admin.site.register(AccountClassifier, ClassifierAdmin)
