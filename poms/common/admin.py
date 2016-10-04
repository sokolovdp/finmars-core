from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from mptt.admin import MPTTModelAdmin


class TreeModelAdmin(MPTTModelAdmin):
    mptt_level_indent = 20
    mptt_indent_field = 'name'


class ClassifierAdmin(admin.ModelAdmin):
    list_display = ['id', 'master_user', 'attribute_type', 'tree_id', 'level', 'parent', 'name', ]
    list_select_related = ['attribute_type', 'attribute_type__master_user', 'parent']
    ordering = ['attribute_type', 'tree_id', 'level', ]
    search_fields = ['attribute_type__name', 'parent__name']
    raw_id_fields = ['attribute_type', 'parent']

    def master_user(self, obj):
        return obj.attribute_type.master_user


class ClassModelAdmin(TranslationAdmin):
    list_display = ['id', 'system_code', 'name']
    search_fields = ['id', 'system_code', 'name']
