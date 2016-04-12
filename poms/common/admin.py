from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from mptt.admin import MPTTModelAdmin

from poms.audit.admin import HistoricalAdmin


class TreeModelAdmin(MPTTModelAdmin):
    list_display = ['id', 'formatted_name', 'parent']
    list_select_related = ['parent']
    mptt_level_indent = 20
    mptt_indent_field = 'formatted_name'
    raw_id_fields = ['parent']

    def formatted_name(self, obj):
        return format_html('<div style="padding-left: {}px">{}</div>', self.mptt_level_indent * obj.level, obj.name)

    formatted_name.short_description = _('name')


class ClassModelAdmin(HistoricalAdmin):
    list_display = ['id', 'system_code', 'name']
    ordering = ['id']
    fields = ['id', 'system_code', 'name', 'description']
    readonly_fields = ['id']
