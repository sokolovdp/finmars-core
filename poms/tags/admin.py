from __future__ import unicode_literals

from django.contrib import admin

from poms.audit.admin import HistoricalAdmin
from poms.obj_perms.admin import UserObjectPermissionAdmin, GroupObjectPermissionAdmin
from poms.tags.models import Tag, TagUserObjectPermission, TagGroupObjectPermission


# admin.site.register(AccountTag, HistoricalAdmin)
# admin.site.register(CurrencyTag, HistoricalAdmin)
# admin.site.register(InstrumentTypeTag, HistoricalAdmin)
# admin.site.register(InstrumentTag, HistoricalAdmin)
# admin.site.register(CounterpartyTag, HistoricalAdmin)
# admin.site.register(ResponsibleTag, HistoricalAdmin)
# admin.site.register(PortfolioTag, HistoricalAdmin)
# admin.site.register(TransactionTypeTag, HistoricalAdmin)


# class TaggedObjectInline(admin.TabularInline):
#     model = TaggedObject
#     extra = 0
#
#
# class TagAdmin(HistoricalAdmin):
#     model = Tag
#     inlines = [TaggedObjectInline]
#
#
# admin.site.register(Tag, TagAdmin)


class TagAdmin(HistoricalAdmin):
    model = Tag
    list_display = ['id', 'master_user', 'name', 'content_type']
    filter_horizontal = ['accounts', 'currencies', 'instrument_types', 'instruments', 'counterparties', 'responsibles',
                         'portfolios', 'transaction_types']
    # 'strategies',

admin.site.register(Tag, TagAdmin)

admin.site.register(TagUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(TagGroupObjectPermission, GroupObjectPermissionAdmin)
