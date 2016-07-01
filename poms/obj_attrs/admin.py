from django.contrib import admin
from django.contrib.admin import widgets
from django.db import models

from poms.audit.admin import HistoricalAdmin


class AbstractAttributeTypeAdmin(HistoricalAdmin):
    list_display = ['id', 'master_user', 'name', 'value_type', ]
    list_select_related = ['master_user', ]
    raw_id_fields = ['master_user']
    save_as = True


class AbstractAttributeTypeClassifierInline(admin.TabularInline):
    extra = 0
    # raw_id_fields = ['parent']
    formfield_overrides = {
        models.TextField: {'widget': widgets.AdminTextInputWidget},
    }

    # def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
    #     if db_field.name == 'parent':
    #         qs = kwargs.get('queryset', db_field.remote_field.model.objects)
    #         # obj_field = self.model._meta.get_field('parent')
    #         # obj_ctype = ContentType.objects.get_for_model(obj_field.rel.to)
    #         kwargs['queryset'] = qs.filter(
    #             attribute_type__master_user__members__user=request.user
    #             # attribute_type=self.parent_model
    #         )
    #         # kwargs['queryset'] = qs.select_related('content_type')
    #     return super(AttributeTypeClassifierInlineBase, self).formfield_for_foreignkey(db_field, request=request, **kwargs)


class AbstractAttributeTypeOptionInline(admin.TabularInline):
    extra = 0
    raw_id_fields = ['member']


class AbstractAttributeTypeOptionAdmin(HistoricalAdmin):
    extra = 0
    list_display = ['id', 'member', 'attribute_type', 'is_hidden']
    fields = ['member', 'attribute_type', 'is_hidden']
    raw_id_fields = ['member']


class AbstractAttributeInline(admin.TabularInline):
    extra = 0
    fields = ['attribute_type', 'value_string', 'value_float', 'value_date', 'classifier']
    raw_id_fields = ['attribute_type', 'classifier']
