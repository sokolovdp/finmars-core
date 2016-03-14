from __future__ import unicode_literals

from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from poms.transactions.models import TransactionClass, Transaction


class TransactionClassAdmin(admin.ModelAdmin):
    model = TransactionClass
    list_display = ['code', 'name']
    ordering = ['code']


admin.site.register(TransactionClass, TransactionClassAdmin)


# class TransactionClassifierAdmin(MPTTModelAdmin):
#     model = TransactionClassifier
#     list_display = ['name', 'master_user']
#     mptt_level_indent = 20
#
#
# admin.site.register(TransactionClassifier, TransactionClassifierAdmin)


class TransactionAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    model = Transaction
    list_select_related = ['transaction_class', 'instrument', 'transaction_currency', 'settlement_currency',
                           'account_cash', 'account_position', 'account_interim',
                           'master_user', 'master_user__user']
    save_as = True
    list_display = ['id', 'transaction_date', 'transaction_class', 'instrument', 'transaction_currency',
                    'settlement_currency',
                    'position_size_with_sign', 'is_canceled',
                    'accounting_date', 'cash_date',
                    'account_cash', 'account_position', 'account_interim',
                    'master_user']
    ordering = ['transaction_date', 'id']
    date_hierarchy = 'transaction_date'


admin.site.register(Transaction, TransactionAdmin)
