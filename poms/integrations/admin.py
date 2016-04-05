from django.contrib import admin

from poms.audit.admin import HistoricalAdmin
from poms.integrations.models import PricingPolicy, PricingPolicyAttr


class PricingPolicyAttrInline(admin.TabularInline):
    model = PricingPolicyAttr
    ordering = ['name']
    extra = 0


class PricingPolicyAdmin(HistoricalAdmin):
    model = PricingPolicy
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']
    ordering = ['user_code']
    inlines = [PricingPolicyAttrInline]


admin.site.register(PricingPolicy, PricingPolicyAdmin)
