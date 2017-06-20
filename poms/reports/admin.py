from django.contrib import admin

from poms.common.admin import AbstractModelAdmin
from poms.reports.models import CustomField


class CustomFieldAdmin(AbstractModelAdmin):
    model = CustomField
    master_user_path = 'master_user'
    list_display = ['id', 'master_user', 'name', ]
    list_select_related = ['master_user']
    ordering = ['id']
    search_fields = ['id', 'name']
    raw_id_fields = ['master_user']


admin.site.register(CustomField, CustomFieldAdmin)
