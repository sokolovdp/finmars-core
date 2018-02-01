from django.contrib import admin
from .models import DataImport, DataImportSchema, DataImportSchemaFields, DataImportSchemaMatching


class DataImportAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'created_at')


class DataImportSchemaFieldsAdmin(admin.ModelAdmin):
    list_display = ('num', 'source', 'schema')


admin.site.register(DataImport, DataImportAdmin)
admin.site.register(DataImportSchema)
admin.site.register(DataImportSchemaFields, DataImportSchemaFieldsAdmin)
admin.site.register(DataImportSchemaMatching)
