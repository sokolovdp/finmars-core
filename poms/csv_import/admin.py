# Register your models here.

from django.contrib import admin

from .models import CsvDataImport, CsvField, CsvImportScheme, EntityField


class EntityFieldInline(admin.TabularInline):
    model = EntityField
    extra = 0

    fields = ("name", "expression")
    readonly_fields = ("id",)


class CsvFieldInline(admin.TabularInline):
    model = CsvField
    extra = 0

    fields = ("column", "name", "name_expr")
    readonly_fields = ("id",)


class CsvImportAdmin(admin.ModelAdmin):
    list_display = ("id", "scheme")


class CsvSchemeAdmin(admin.ModelAdmin):
    model = CsvImportScheme
    master_user_path = "master_user"
    list_display = [
        "id",
        "master_user",
        "user_code",
        "content_type",
    ]
    search_fields = [
        "id",
        "user_code",
        "content_type",
    ]
    raw_id_fields = [
        "master_user",
        "content_type",
    ]
    inlines = [EntityFieldInline, CsvFieldInline]


admin.site.register(CsvDataImport, CsvImportAdmin)
admin.site.register(CsvImportScheme, CsvSchemeAdmin)
