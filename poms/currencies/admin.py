from __future__ import unicode_literals

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from poms.audit.admin import HistoricalAdmin
from poms.currencies.models import Currency, CurrencyHistory


class GlobalCurrencyFilter(admin.SimpleListFilter):
    title = _('is global')
    parameter_name = 'master_user'

    def lookups(self, request, model_admin):
        return (
            ('1', _('Yes')),
            ('0', _('No')),
        )

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.filter(master_user__isnull=True)
        if self.value() == '0':
            return queryset.filter(master_user__isnull=False)


class CurrencyAdmin(HistoricalAdmin):
    model = Currency
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']
    ordering = ['user_code']
    list_filter = [GlobalCurrencyFilter]

    def is_global(self, obj):
        return obj.is_global

    is_global.short_name = _('is global')
    is_global.boolean = True
    is_global.admin_order_field = 'master_user'

    def is_system(self, obj):
        return obj.is_system

    is_system.short_name = _('is system')
    is_system.boolean = True


admin.site.register(Currency, CurrencyAdmin)


class CurrencyHistoryAdmin(HistoricalAdmin):
    model = CurrencyHistory
    list_display = ['id', 'currency', 'date', 'fx_rate']
    list_select_related = ['currency', 'master_user']
    list_filter = ['date']
    date_hierarchy = 'date'


admin.site.register(CurrencyHistory, CurrencyHistoryAdmin)
