from django.contrib import admin
from mptt.admin import MPTTModelAdmin

from poms.audit.admin import HistoricalAdmin


class TreeModelAdmin(MPTTModelAdmin):
    mptt_level_indent = 20
    mptt_indent_field = 'name'


class ClassifierAdmin(HistoricalAdmin, admin.ModelAdmin):
    list_display = ['id', 'master_user', 'attribute_type', 'parent', 'name', ]
    list_select_related = ['attribute_type', 'attribute_type__master_user', 'parent']
    search_fields = ['attribute_type__name', 'parent__name']
    raw_id_fields = ['attribute_type', 'parent']

    def master_user(self, obj):
        return obj.attribute_type.master_user


class ClassModelAdmin(HistoricalAdmin):
    list_display = ['id', 'system_code', 'name_en', 'name']
    search_fields = ['id', 'system_code', 'name_en']
    ordering = ['id']
    readonly_fields = ['id']
