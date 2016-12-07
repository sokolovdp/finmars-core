from __future__ import unicode_literals

from django.contrib import admin

from poms.accounts.models import Account, AccountType
from poms.obj_attrs.admin import GenericAttributeInline
from poms.obj_perms.admin import GenericObjectPermissionInline
from poms.tags.admin import GenericTagLinkInline


class AccountTypeAdmin(admin.ModelAdmin):
    model = AccountType
    list_display = ['id', 'master_user', 'user_code', 'name', 'is_deleted', ]
    list_select_related = ['master_user']
    list_filter = ['is_deleted', ]
    ordering = ['master_user', 'user_code']
    search_fields = ['id', 'user_code', 'name']
    raw_id_fields = ['master_user']
    inlines = [
        GenericTagLinkInline,
        GenericObjectPermissionInline,
        # UserObjectPermissionInline,
        # GroupObjectPermissionInline,
    ]


admin.site.register(AccountType, AccountTypeAdmin)


class AccountAdmin(admin.ModelAdmin):
    model = Account
    list_display = ['id', 'master_user', 'type', 'user_code', 'name', 'is_deleted', ]
    list_select_related = ['master_user', 'type']
    list_filter = ['is_deleted', ]
    ordering = ['master_user', 'type', 'user_code']
    search_fields = ['id', 'user_code', 'name']
    raw_id_fields = ['master_user', 'type']
    inlines = [
        # AbstractAttributeInline,
        GenericAttributeInline,
        GenericTagLinkInline,
        GenericObjectPermissionInline,
        # UserObjectPermissionInline,
        # GroupObjectPermissionInline,
    ]


admin.site.register(Account, AccountAdmin)


# class AccountAttributeTypeAdmin(AbstractAttributeTypeAdmin):
#     inlines = [
#         AbstractAttributeTypeClassifierInline,
#         AbstractAttributeTypeOptionInline,
#         GenericObjectPermissionInline,
#         # UserObjectPermissionInline,
#         # GroupObjectPermissionInline,
#     ]


# admin.site.register(AccountAttributeType, AccountAttributeTypeAdmin)
#
# admin.site.register(AccountClassifier, ClassifierAdmin)
