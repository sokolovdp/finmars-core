from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from poms.obj_perms.admin import GenericObjectPermissionInline
from poms.tags.filters import get_tag_content_types
from poms.tags.models import Tag, TagLink


class TagLinkInline(admin.TabularInline):
    model = TagLink
    extra = 0


class GenericTagLinkInline(GenericTabularInline):
    model = TagLink
    raw_id_fields = ['tag']
    extra = 0


class TagLinkAdmin(admin.ModelAdmin):
    model = TagLink
    list_display = ['id', 'master_user', 'content_type', 'object_id', 'content_object', 'tag']
    list_select_related = ['tag', 'tag__master_user', 'content_type']
    raw_id_fields = ['tag']

    def get_queryset(self, request):
        qs = super(TagLinkAdmin, self).get_queryset(request)
        return qs.prefetch_related('content_object')

    def master_user(self, obj):
        return obj.tag.master_user


admin.site.register(TagLink, TagLinkAdmin)


class TagAdmin(admin.ModelAdmin):
    model = Tag
    list_display = ['id', 'master_user', 'user_code', 'name', ]
    list_select_related = ['master_user']
    ordering = ['master_user', 'user_code']
    list_filter = ['content_types']
    search_fields = ['id', 'user_code', 'name']
    filter_horizontal = ['content_types', ]
    raw_id_fields = [
        'master_user',
        # 'account_types', 'accounts', 'currencies', 'instrument_types', 'instruments',
        # 'counterparty_groups', 'counterparties',
        # 'responsible_groups', 'responsibles',
        # 'portfolios',
        # 'transaction_type_groups', 'transaction_types',
        # 'strategy1_groups', 'strategy1_subgroups', 'strategies1',
        # 'strategy2_groups', 'strategy2_subgroups', 'strategies2',
        # 'strategy3_groups', 'strategy3_subgroups', 'strategies3',
        # 'thread_groups', 'threads'
    ]
    inlines = [
        TagLinkInline,
        GenericObjectPermissionInline,
        # UserObjectPermissionInline,
        # GroupObjectPermissionInline,
    ]

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == 'content_types':
            qs = kwargs.get('queryset', db_field.remote_field.model.objects)
            kwargs['queryset'] = qs.filter(pk__in=get_tag_content_types())
        return super(TagAdmin, self).formfield_for_manytomany(db_field, request=request, **kwargs)


admin.site.register(Tag, TagAdmin)
