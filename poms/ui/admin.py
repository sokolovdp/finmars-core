from django.contrib import admin

from poms.ui.filters import LayoutContentTypeFilter
from poms.ui.models import TemplateListLayout, TemplateEditLayout, ListLayout, EditLayout


class BaseLayoutAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'content_type':
            qs = kwargs.get('queryset', db_field.remote_field.model.objects)
            kwargs['queryset'] = LayoutContentTypeFilter().filter_queryset(request, qs, None)
        return super(BaseLayoutAdmin, self).formfield_for_foreignkey(db_field, request=request, **kwargs)


class TemplateListLayoutAdmin(BaseLayoutAdmin):
    model = TemplateListLayout
    list_display = ['id', 'master_user', 'content_type', 'name']
    list_select_related = ['master_user', 'content_type']
    raw_id_fields = ['master_user']


admin.site.register(TemplateListLayout, TemplateListLayoutAdmin)


class TemplateEditLayoutAdmin(BaseLayoutAdmin):
    model = TemplateEditLayout
    list_display = ['id', 'master_user', 'content_type']
    list_select_related = ['master_user', 'content_type']
    raw_id_fields = ['master_user']


admin.site.register(TemplateEditLayout, TemplateEditLayoutAdmin)


class ListLayoutAdmin(BaseLayoutAdmin):
    model = ListLayout
    list_display = ['id', 'member', 'content_type', 'name']
    list_select_related = ['member', 'content_type']
    raw_id_fields = ['member']


admin.site.register(ListLayout, ListLayoutAdmin)


class EditLayoutAdmin(BaseLayoutAdmin):
    model = EditLayout
    list_display = ['id', 'member', 'content_type']
    list_select_related = ['member', 'content_type']
    raw_id_fields = ['member']


admin.site.register(EditLayout, EditLayoutAdmin)
