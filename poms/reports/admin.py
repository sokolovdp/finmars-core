from django.contrib import admin

from poms.common.admin import ClassModelAdmin
from poms.reports.models import ReportClass, CustomField

admin.site.register(ReportClass, ClassModelAdmin)


class CustomFieldAdmin(admin.ModelAdmin):
    model = CustomField
    list_display = ['id', 'master_user', 'report_class', 'name', ]
    list_select_related = ['master_user', 'report_class']
    search_fields = ['id', 'name']
    list_filter = ['report_class', ]
    raw_id_fields = ['master_user']


admin.site.register(CustomField, CustomFieldAdmin)
