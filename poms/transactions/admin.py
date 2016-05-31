from __future__ import unicode_literals

from django.contrib import admin

from poms.audit.admin import HistoricalAdmin
from poms.common.admin import ClassModelAdmin
from poms.obj_attrs.admin import AttributeTypeAdminBase, AttributeTypeOptionAdminBase, AttributeInlineBase
from poms.obj_perms.admin import GroupObjectPermissionAdmin, UserObjectPermissionAdmin
from poms.transactions.models import TransactionClass, Transaction, TransactionType, TransactionTypeInput, \
    TransactionTypeItem, TransactionTypeGroupObjectPermission, \
    TransactionAttributeType, TransactionAttributeTypeOption, TransactionAttributeTypeGroupObjectPermission, \
    TransactionAttribute, ActionClass, EventToHandle, \
    ExternalCashFlow, ExternalCashFlowStrategy, NotificationClass, EventClass, PeriodicityGroup, \
    TransactionTypeUserObjectPermission, TransactionAttributeTypeUserObjectPermission

admin.site.register(TransactionClass, ClassModelAdmin)
admin.site.register(ActionClass, ClassModelAdmin)
admin.site.register(EventClass, ClassModelAdmin)
admin.site.register(NotificationClass, ClassModelAdmin)
admin.site.register(PeriodicityGroup, ClassModelAdmin)


class TransactionTypeInputInline(admin.StackedInline):
    model = TransactionTypeInput
    extra = 0


class TransactionTypeItemInline(admin.StackedInline):
    model = TransactionTypeItem
    extra = 0

    fields = (
        'order', 'transaction_class',
        ('instrument', 'instrument_input'),
        ('transaction_currency', 'transaction_currency_input'),
        ('position_size_with_sign', 'position_size_with_sign_expr'),
        ('settlement_currency', 'settlement_currency_input'),
        ('cash_consideration', 'cash_consideration_expr'),
        ('account_position', 'account_position_input'),
        ('account_cash', 'account_cash_input'),
        ('account_interim', 'account_interim_input'),

        ('strategy1_position', 'strategy1_position_input'),
        ('strategy1_cash', 'strategy1_cash_input'),
        ('strategy2_position', 'strategy2_position_input'),
        ('strategy2_cash', 'strategy2_cash_input'),
        ('strategy3_position', 'strategy3_position_input'),
        ('strategy3_cash', 'strategy3_cash_input'),

        # ('accounting_date', 'accounting_date_expr'),
        # ('cash_date', 'cash_date_expr'),
    )


class EventToHandleInline(admin.StackedInline):
    model = EventToHandle
    list_display = ['id', 'master_user', 'name']
    raw_id_fields = ['master_user']
    extra = 0


class TransactionTypeAdmin(HistoricalAdmin):
    model = TransactionType
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']
    raw_id_fields = ['master_user']
    filter_horizontal = ['instrument_types']
    inlines = [TransactionTypeInputInline, TransactionTypeItemInline, EventToHandleInline]

    def get_inline_instances(self, request, obj=None):
        if obj:
            return super(TransactionTypeAdmin, self).get_inline_instances(request, obj)
        return []


admin.site.register(TransactionType, TransactionTypeAdmin)
admin.site.register(TransactionTypeUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(TransactionTypeGroupObjectPermission, GroupObjectPermissionAdmin)


# class EventToHandleAdmin(HistoricalAdmin):
#     model = EventToHandle
#     list_display = ['id', 'master_user', 'name', 'transaction_type']
#     raw_id_fields = ['master_user', 'transaction_type']
#
#
# admin.site.register(EventToHandle, HistoricalAdmin)


class TransactionAttributeInline(AttributeInlineBase):
    model = TransactionAttribute
    fields = ['attribute_type', 'value_string', 'value_float', 'value_date']
    raw_id_fields = ['attribute_type']


class TransactionAdmin(HistoricalAdmin):
    model = Transaction
    list_select_related = ['master_user', 'transaction_class',
                           'instrument', 'transaction_currency', 'settlement_currency',
                           'portfolio', 'account_cash', 'account_position', 'account_interim',
                           'strategy1_position', 'strategy1_cash', 'strategy2_position', 'strategy2_cash',
                           'strategy3_position', 'strategy3_cash']
    list_display = ['id', 'master_user',
                    'is_canceled', 'transaction_class',
                    'transaction_date', 'accounting_date', 'cash_date',
                    'instrument', 'transaction_currency',
                    'position_size_with_sign',
                    'settlement_currency', 'cash_consideration',
                    'principal_with_sign', 'carry_with_sign', 'overheads_with_sign',
                    'account_cash', 'account_position', 'account_interim',
                    'strategy1_position', 'strategy1_cash', 'strategy2_position', 'strategy2_cash',
                    'strategy3_position', 'strategy3_cash',
                    ]
    list_filter = ['is_canceled']
    ordering = ['transaction_date', 'id']
    date_hierarchy = 'transaction_date'
    raw_id_fields = ['master_user', 'portfolio', 'instrument', 'transaction_currency', 'settlement_currency',
                     'account_position', 'account_cash', 'account_interim', 'responsible', 'counterparty',
                     'strategy1_position', 'strategy1_cash',
                     'strategy2_position', 'strategy2_cash',
                     'strategy3_position', 'strategy3_cash'
                     ]
    inlines = [TransactionAttributeInline]
    fields = (
        'master_user',
        'transaction_code',
        'transaction_class',
        ('instrument', 'transaction_currency', 'position_size_with_sign'),
        ('settlement_currency', 'cash_consideration'),
        ('principal_with_sign', 'carry_with_sign', 'overheads_with_sign'),
        ('accounting_date', 'cash_date'),
        'portfolio',
        ('account_position', 'account_cash', 'account_interim'),
        ('strategy1_position', 'strategy1_cash'),
        ('strategy2_position', 'strategy2_cash'),
        ('strategy3_position', 'strategy3_cash'),
        ('responsible', 'counterparty'),
        'reference_fx_rate',
        'is_locked',
        'is_canceled',
        'factor',
        'trade_price',
        'principal_amount', 'carry_amount', 'overheads',
    )


admin.site.register(Transaction, TransactionAdmin)


class TransactionAttributeTypeAdmin(AttributeTypeAdminBase):
    list_display = ['id', 'master_user', 'name', 'value_type']
    list_select_related = ['master_user']
    raw_id_fields = ['master_user']


admin.site.register(TransactionAttributeType, TransactionAttributeTypeAdmin)
admin.site.register(TransactionAttributeTypeOption, AttributeTypeOptionAdminBase)
admin.site.register(TransactionAttributeTypeUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(TransactionAttributeTypeGroupObjectPermission, GroupObjectPermissionAdmin)


class ExternalCashFlowStrategyInline(admin.TabularInline):
    model = ExternalCashFlowStrategy
    raw_id_fields = ['strategy1', 'strategy2', 'strategy3']
    extra = 0


class ExternalCashFlowAdmin(HistoricalAdmin):
    model = ExternalCashFlow
    inlines = [ExternalCashFlowStrategyInline]
    raw_id_fields = ['portfolio', 'account', 'currency']


admin.site.register(ExternalCashFlow, ExternalCashFlowAdmin)
