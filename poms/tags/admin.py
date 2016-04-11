from __future__ import unicode_literals

from django.contrib import admin

from poms.audit.admin import HistoricalAdmin
from poms.tags.models import Tag2, Tag, TaggedObject


# admin.site.register(AccountTag, HistoricalAdmin)
# admin.site.register(CurrencyTag, HistoricalAdmin)
# admin.site.register(InstrumentTypeTag, HistoricalAdmin)
# admin.site.register(InstrumentTag, HistoricalAdmin)
# admin.site.register(CounterpartyTag, HistoricalAdmin)
# admin.site.register(ResponsibleTag, HistoricalAdmin)
# admin.site.register(PortfolioTag, HistoricalAdmin)
# admin.site.register(TransactionTypeTag, HistoricalAdmin)


class TaggedObjectInline(admin.TabularInline):
    model = TaggedObject
    extra = 0


class TagAdmin(HistoricalAdmin):
    model = Tag
    inlines = [TaggedObjectInline]


admin.site.register(Tag, TagAdmin)


class Tag2Admin(HistoricalAdmin):
    model = Tag2
    list_display = ['id', 'master_user', 'name', 'content_type']
    filter_horizontal = ['accounts', 'currencies', 'instrument_types', 'instruments', 'counterparties', 'responsibles',
                         'portfolios', 'transaction_types']
    # 'strategies',


admin.site.register(Tag2, Tag2Admin)
