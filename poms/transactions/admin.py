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
    save_as = True
    list_display = ['id', 'transaction_date', 'transaction_class', 'instrument', 'transaction_currency',
                    'position_size_with_sign', 'is_canceled', 'master_user']
    ordering = ['transaction_date', 'id']
    date_hierarchy = 'transaction_date'


admin.site.register(Transaction, TransactionAdmin)
