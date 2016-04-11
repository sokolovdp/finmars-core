from __future__ import unicode_literals

from django.contrib import admin

from poms.audit.admin import HistoricalAdmin
from poms.obj_perms.admin import UserObjectPermissionAdmin, GroupObjectPermissionAdmin
from poms.tags.models import Tag, TagUserObjectPermission, TagGroupObjectPermission


class TagAdmin(HistoricalAdmin):
    model = Tag
    list_display = ['id', 'master_user', 'name', 'content_type']
    filter_horizontal = ['accounts', 'currencies', 'instrument_types', 'instruments', 'counterparties', 'responsibles',
                         'portfolios', 'transaction_types']
    # 'strategies',


admin.site.register(Tag, TagAdmin)

admin.site.register(TagUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(TagGroupObjectPermission, GroupObjectPermissionAdmin)
