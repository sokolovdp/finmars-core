from __future__ import unicode_literals

from django.contrib import admin

from poms.audit.admin import HistoricalAdmin
from poms.obj_perms.admin import UserObjectPermissionInline, GroupObjectPermissionInline
from poms.tags.filters import get_tag_content_types
from poms.tags.models import Tag


class TagAdmin(HistoricalAdmin):
    model = Tag
    list_display = ['id', 'master_user', 'name', ]
    list_select_related = ['master_user']
    filter_horizontal = ['content_types', ]
    raw_id_fields = [
        'master_user', 'account_types', 'accounts', 'currencies', 'instrument_types', 'instruments',
        'counterparty_groups', 'counterparties',
        'responsible_groups', 'responsibles',
        'portfolios',
        'transaction_type_groups', 'transaction_types',
        'strategy1_groups', 'strategy1_subgroups', 'strategies1',
        'strategy2_groups', 'strategy2_subgroups', 'strategies2',
        'strategy3_groups', 'strategy3_subgroups', 'strategies3',
        'thread_groups', 'threads'
    ]
    inlines = [
        UserObjectPermissionInline,
        GroupObjectPermissionInline,
    ]

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == 'content_types':
            qs = kwargs.get('queryset', db_field.remote_field.model.objects)
            kwargs['queryset'] = qs.filter(pk__in=get_tag_content_types())
        return super(TagAdmin, self).formfield_for_manytomany(db_field, request=request, **kwargs)


admin.site.register(Tag, TagAdmin)
