# Register your models here.

from django.contrib import admin

from poms.complex_import.models import (
    ComplexImport,
    ComplexImportScheme,
    ComplexImportSchemeAction,
)


class ComplexImportAdmin(admin.ModelAdmin):
    list_display = ("id", "complex_import_scheme")


class ComplexSchemeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user_code",
    )


class ComplexImportSchemeActionAdmin(admin.ModelAdmin):
    list_display = ("id", "complex_import_scheme", "order", "action_notes")


admin.site.register(ComplexImport, ComplexImportAdmin)
admin.site.register(ComplexImportScheme, ComplexSchemeAdmin)
admin.site.register(ComplexImportSchemeAction, ComplexImportSchemeActionAdmin)
