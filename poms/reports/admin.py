from django.contrib import admin

from poms.common.admin import ClassModelAdmin
from poms.reports.models import CustomField

# admin.site.register(ReportClass, ClassModelAdmin)


class CustomFieldAdmin(admin.ModelAdmin):
    model = CustomField
    list_display = ['id', 'master_user', 'name', ]
    list_select_related = ['master_user']
    search_fields = ['id', 'name']
    raw_id_fields = ['master_user']


admin.site.register(CustomField, CustomFieldAdmin)
