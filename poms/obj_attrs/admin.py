from django.contrib import admin

from poms.audit.admin import HistoricalAdmin
from poms.obj_attrs.models import AccountAttr, CounterpartyAttr, ResponsibleAttr, PortfolioAttr, InstrumentAttr, \
    TransactionAttr, Scheme, PortfolioAttrValue, TransactionAttrValue, InstrumentAttrValue, ResponsibleAttrValue, \
    CounterpartyAttrValue, AccountAttrValue


class AttrInlineBase(admin.StackedInline):
    ordering = ['order', 'name']
    raw_id_fields = ['classifier']
    extra = 0


class AttrValueInlineBase(admin.StackedInline):
    extra = 0
    raw_id_fields = ['attr', 'classifier']


class AccountAttrInline(AttrInlineBase):
    model = AccountAttr


class CounterpartyAttrInline(AttrInlineBase):
    model = CounterpartyAttr


class ResponsibleAttrInline(AttrInlineBase):
    model = ResponsibleAttr


class PortfolioAttrInline(AttrInlineBase):
    model = PortfolioAttr


class InstrumentAttrInline(AttrInlineBase):
    model = InstrumentAttr


class TransactionAttrInline(AttrInlineBase):
    model = TransactionAttr
    raw_id_fields = ['strategy_position', 'strategy_cash']
    ordering = ['order', 'name']
    extra = 0


class AttrSchemeAdmin(HistoricalAdmin, admin.ModelAdmin):
    model = Scheme
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']
    raw_id_fields = ['master_user']
    inlines = [
        AccountAttrInline,
        CounterpartyAttrInline,
        ResponsibleAttrInline,
        PortfolioAttrInline,
        InstrumentAttrInline,
        TransactionAttrInline
    ]


admin.site.register(Scheme, AttrSchemeAdmin)


class AttrAdmin(HistoricalAdmin):
    list_display = ['id', 'scheme', 'name', 'value_type', 'classifier']
    list_select_related = ['scheme', 'scheme__master_user', 'classifier']
    raw_id_fields = ['scheme', 'classifier']


class AttrValueAdmin(HistoricalAdmin):
    list_display = ['id', 'content_object', 'attr', 'value', 'classifier']
    list_select_related = ['attr', 'attr__scheme', 'attr__scheme__master_user', 'classifier']
    raw_id_fields = ['attr', 'content_object', 'classifier']


class TransactionAttrAdmin(AttrAdmin):
    list_display = ['id', 'scheme', 'name', 'value_type', 'strategy_position', 'strategy_cash']
    list_select_related = ['scheme', 'scheme__master_user', 'strategy_position', 'strategy_cash']
    raw_id_fields = ['scheme', 'strategy_position', 'strategy_cash']


class TransactionAttrValueAdmin(AttrValueAdmin):
    list_display = ['id', 'content_object', 'attr', 'value', 'strategy_position', 'strategy_cash']
    list_select_related = ['attr', 'attr__scheme', 'attr__scheme__master_user', 'strategy_position', 'strategy_cash']
    raw_id_fields = ['attr', 'content_object', 'strategy_position', 'strategy_cash']


admin.site.register(AccountAttr, AttrAdmin)
admin.site.register(AccountAttrValue, AttrValueAdmin)
admin.site.register(CounterpartyAttr, AttrAdmin)
admin.site.register(CounterpartyAttrValue, AttrValueAdmin)
admin.site.register(ResponsibleAttr, AttrAdmin)
admin.site.register(ResponsibleAttrValue, AttrValueAdmin)
admin.site.register(InstrumentAttr, AttrAdmin)
admin.site.register(InstrumentAttrValue, AttrValueAdmin)
admin.site.register(PortfolioAttr, AttrAdmin)
admin.site.register(PortfolioAttrValue, AttrValueAdmin)
admin.site.register(TransactionAttr, TransactionAttrAdmin)
admin.site.register(TransactionAttrValue, TransactionAttrValueAdmin)
