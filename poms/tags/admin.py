from __future__ import unicode_literals

from django.contrib import admin

from poms.audit.admin import HistoricalAdmin
from poms.obj_perms.admin import UserObjectPermissionInline, \
    GroupObjectPermissionInline
from poms.tags.filters import TagContentTypeFilter
from poms.tags.models import Tag


class TagAdmin(HistoricalAdmin):
    model = Tag
    list_display = ['id', 'master_user', 'name']
    filter_horizontal = ['content_types', 'account_types', 'accounts', 'currencies', 'instrument_types', 'instruments',
                         'counterparties', 'responsibles', 'portfolios', 'transaction_types',
                         'strategies1', 'strategies2', 'strategies3', 'thread_groups', 'threads']
    raw_id_fields = ['master_user', 'account_types']
    inlines = [
        UserObjectPermissionInline,
        GroupObjectPermissionInline,
    ]

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == 'content_types':
            qs = kwargs.get('queryset', db_field.remote_field.model.objects)
            kwargs['queryset'] = TagContentTypeFilter().filter_queryset(request, qs, None).order_by('model')
        return super(TagAdmin, self).formfield_for_manytomany(db_field, request=request, **kwargs)


admin.site.register(Tag, TagAdmin)
# admin.site.register(TagUserObjectPermission, UserObjectPermissionAdmin)
# admin.site.register(TagGroupObjectPermission, GroupObjectPermissionAdmin)
