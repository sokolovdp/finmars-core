from django.contrib import admin
from .models import DataImport, DataImportSchema


class DataImportAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'created_at')


admin.site.register(DataImport, DataImportAdmin)
admin.site.register(DataImportSchema)
