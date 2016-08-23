from __future__ import unicode_literals

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from poms.audit.admin import HistoricalAdmin
from poms.currencies.models import Currency, CurrencyHistory


class CurrencyAdmin(HistoricalAdmin):
    model = Currency
    list_display = ['id', 'master_user', 'name', 'reference_for_pricing', 'daily_pricing_model', 'price_download_scheme']
    list_select_related = ['master_user']
    raw_id_fields = ['master_user', 'price_download_scheme']
    ordering = ['master_user', 'user_code']

    def is_system(self, obj):
        return obj.is_system

    is_system.short_name = _('is system')
    is_system.boolean = True


admin.site.register(Currency, CurrencyAdmin)


# admin.site.register(CurrencyUserObjectPermission, UserObjectPermissionAdmin)
# admin.site.register(CurrencyGroupObjectPermission, GroupObjectPermissionAdmin)


class CurrencyHistoryAdmin(HistoricalAdmin):
    model = CurrencyHistory
    list_display = ['id', 'currency', 'master_user', 'date', 'fx_rate']
    list_select_related = ['currency', 'currency__master_user']
    list_filter = ['date']
    date_hierarchy = 'date'
    raw_id_fields = ['currency', 'pricing_policy']

    def master_user(self, obj):
        return obj.currency.master_user


admin.site.register(CurrencyHistory, CurrencyHistoryAdmin)
