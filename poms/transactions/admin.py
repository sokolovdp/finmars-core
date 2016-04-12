from __future__ import unicode_literals

from django.contrib import admin

from poms.audit.admin import HistoricalAdmin
from poms.obj_attrs.admin import AttributeTypeAdminBase, AttributeTypeOptionInlineBase
from poms.obj_perms.admin import UserObjectPermissionAdmin, GroupObjectPermissionAdmin
from poms.transactions.models import TransactionClass, Transaction, TransactionType, TransactionTypeInput, \
    TransactionTypeItem, TransactionTypeUserObjectPermission, TransactionTypeGroupObjectPermission, \
    TransactionAttributeType, TransactionAttributeTypeOption, TransactionAttributeTypeUserObjectPermission, \
    TransactionAttributeTypeGroupObjectPermission


class TransactionClassAdmin(HistoricalAdmin):
    model = TransactionClass
    list_display = ['id', 'system_code', 'name']
    ordering = ['id']


admin.site.register(TransactionClass, TransactionClassAdmin)


class TransactionTypeInputInline(admin.StackedInline):
    model = TransactionTypeInput
    extra = 0


class TransactionTypeItemInline(admin.StackedInline):
    model = TransactionTypeItem
    extra = 0


class TransactionTypeAdmin(HistoricalAdmin):
    model = TransactionType
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']
    raw_id_fields = ['master_user']
    filter_horizontal = ['instrument_types']
    inlines = [TransactionTypeInputInline, TransactionTypeItemInline]

    def get_inline_instances(self, request, obj=None):
        if obj:
            return super(TransactionTypeAdmin, self).get_inline_instances(request, obj)
        return []


admin.site.register(TransactionType, TransactionTypeAdmin)
admin.site.register(TransactionTypeUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(TransactionTypeGroupObjectPermission, GroupObjectPermissionAdmin)


class TransactionAdmin(HistoricalAdmin):
    model = Transaction
    list_select_related = ['master_user', 'transaction_class', 'instrument', 'transaction_currency',
                           'settlement_currency', 'account_cash', 'account_position', 'account_interim', ]
    list_display = ['id', 'master_user',
                    'is_canceled', 'transaction_class', 'portfolio',
                    'instrument', 'transaction_currency',
                    'position_size_with_sign',
                    'settlement_currency', 'cash_consideration',
                    'principal_with_sign', 'carry_with_sign', 'overheads_with_sign',
                    'account_cash', 'account_position', 'account_interim',
                    'transaction_date', 'accounting_date', 'cash_date']
    list_filter = ['is_canceled']
    ordering = ['transaction_date', 'id']
    date_hierarchy = 'transaction_date'
    # actions = ['make_canceled', 'make_active']

    raw_id_fields = ['master_user', 'portfolio', 'instrument', 'transaction_currency', 'settlement_currency',
                     'account_position', 'account_cash', 'account_interim', 'responsible', 'counterparty']

    # inlines = [TransactionAttrValueInline]

    def make_canceled(self, request, queryset):
        queryset.update(is_canceled=True)

    make_canceled.short_description = "Mark selected transaction as canceled"

    def make_active(self, request, queryset):
        queryset.update(is_canceled=False)

    make_active.short_description = "Mark selected transaction as active"


admin.site.register(Transaction, TransactionAdmin)


class TransactionAttributeTypeAdmin(AttributeTypeAdminBase):
    list_display = ['id', 'master_user', 'name', 'value_type', 'strategy_position_root', 'strategy_cash_root']
    list_select_related = ['master_user', 'strategy_position_root', 'strategy_cash_root']
    raw_id_fields = ['master_user', 'strategy_position_root', 'strategy_cash_root']


admin.site.register(TransactionAttributeType, TransactionAttributeTypeAdmin)
admin.site.register(TransactionAttributeTypeOption, AttributeTypeOptionInlineBase)
admin.site.register(TransactionAttributeTypeUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(TransactionAttributeTypeGroupObjectPermission, GroupObjectPermissionAdmin)
