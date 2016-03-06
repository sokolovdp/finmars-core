from __future__ import unicode_literals

from django.contrib import admin
from reversion.admin import VersionAdmin

from poms.transactions.models import TransactionClass, Transaction


class TransactionClassAdmin(VersionAdmin):
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


class TransactionAdmin(admin.ModelAdmin):
    model = Transaction
    save_as = True
    list_display = ['id', 'accounting_date', 'master_user', 'instrument', 'transaction_class',
                    'position_size_with_sign', 'principal_with_sign']


admin.site.register(Transaction, TransactionAdmin)
