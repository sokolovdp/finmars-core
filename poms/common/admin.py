from mptt.admin import MPTTModelAdmin

from poms.audit.admin import HistoricalAdmin


class TreeModelAdmin(MPTTModelAdmin):
    mptt_level_indent = 20
    mptt_indent_field = 'name'

    # def formatted_name(self, obj):
    #     return format_html('<div style="padding-left: {}px">{}</div>', self.mptt_level_indent * obj.level, obj.name)
    # formatted_name.short_description = _('name')


class ClassifierAdmin(HistoricalAdmin, TreeModelAdmin):
    # list_display = ['id', 'master_user', 'formatted_name', 'parent', ]
    # list_select_related = ['master_user', 'parent']
    # raw_id_fields = ['master_user', 'parent']
    # fields = ['master_user', 'parent', 'user_code', 'name', 'short_name', 'notes']

    list_display = ['id', 'master_user', 'attribute_type', 'name', 'parent', ]
    list_select_related = ['attribute_type', 'attribute_type__master_user', 'parent']
    raw_id_fields = ['attribute_type', 'parent']

    def master_user(self, obj):
        return obj.attribute_type.master_user


class ClassModelAdmin(HistoricalAdmin):
    list_display = ['id', 'system_code', 'name_en', 'name']
    ordering = ['id']
    # fields = ['id', 'system_code', ]
    readonly_fields = ['id']
