from django.contrib import admin
from .models import DataImport, DataImportSchema


class DataImportSchemaInline(admin.TabularInline):
    model = DataImportSchema
    extra = 0


class DataImportAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'created_at')
    inlines = [DataImportSchemaInline]

admin.site.register(DataImport, DataImportAdmin)
