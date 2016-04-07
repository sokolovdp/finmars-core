from __future__ import unicode_literals

from django.contrib import admin

from poms.audit.admin import HistoricalAdmin
from poms.tags.models import AccountTag, CommonTag, PortfolioTag, InstrumentTag, InstrumentTypeTag, CurrencyTag, \
    ResponsibleTag, CounterpartyTag, TransactionTypeTag

admin.site.register(AccountTag, HistoricalAdmin)
admin.site.register(CurrencyTag, HistoricalAdmin)
admin.site.register(InstrumentTypeTag, HistoricalAdmin)
admin.site.register(InstrumentTag, HistoricalAdmin)
admin.site.register(CounterpartyTag, HistoricalAdmin)
admin.site.register(ResponsibleTag, HistoricalAdmin)
admin.site.register(PortfolioTag, HistoricalAdmin)
admin.site.register(TransactionTypeTag, HistoricalAdmin)
admin.site.register(CommonTag, HistoricalAdmin)
