from django.contrib import admin
from .models import DataImport, DataImportSchema, DataImportSchemaFields


class DataImportAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'created_at')


admin.site.register(DataImport, DataImportAdmin)
admin.site.register(DataImportSchema)
admin.site.register(DataImportSchemaFields)
