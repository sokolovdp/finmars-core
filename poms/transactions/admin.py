from __future__ import unicode_literals

from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from poms.audit.admin import HistoricalAdmin
from poms.transactions.models import TransactionClass, Transaction


class TransactionClassAdmin(HistoricalAdmin):
    model = TransactionClass
    list_display = ['id', 'system_code', 'name']
    ordering = ['id']


admin.site.register(TransactionClass, TransactionClassAdmin)


# class TransactionClassifierAdmin(MPTTModelAdmin):
#     model = TransactionClassifier
#     list_display = ['name', 'master_user']
#     mptt_level_indent = 20
#
#
# admin.site.register(TransactionClassifier, TransactionClassifierAdmin)


class TransactionAdmin(HistoricalAdmin, ImportExportModelAdmin):
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
    actions = ['make_canceled', 'make_active']

    def make_canceled(self, request, queryset):
        queryset.update(is_canceled=True)
    make_canceled.short_description = "Mark selected transaction as canceled"

    def make_active(self, request, queryset):
        queryset.update(is_canceled=False)
    make_active.short_description = "Mark selected transaction as active"

admin.site.register(Transaction, TransactionAdmin)
