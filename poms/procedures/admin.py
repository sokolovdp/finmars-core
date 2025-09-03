from django.contrib import admin

from poms.procedures.models import (
    ExpressionProcedure,
    ExpressionProcedureContextVariable,
    PricingParentProcedureInstance,
    PricingProcedure,
    PricingProcedureInstance,
    RequestDataFileProcedure,
    RequestDataFileProcedureInstance,
)


class PricingProcedureAdmin(admin.ModelAdmin):
    model = PricingProcedure
    list_display = [
        "id",
        "name",
        "master_user",
        "type",
        "notes",
        "notes_for_users",
        "price_date_from",
        "price_date_to",
    ]


admin.site.register(PricingProcedure, PricingProcedureAdmin)


class PricingParentProcedureInstanceAdmin(admin.ModelAdmin):
    model = PricingParentProcedureInstance
    list_display = ["id", "master_user", "procedure", "created_at", "modified_at"]
    raw_id_fields = ["master_user", "procedure"]


admin.site.register(PricingParentProcedureInstance, PricingParentProcedureInstanceAdmin)


class PricingProcedureInstanceAdmin(admin.ModelAdmin):
    model = PricingProcedureInstance
    list_display = ["id", "procedure", "master_user", "status"]
    raw_id_fields = ["procedure", "master_user"]


admin.site.register(PricingProcedureInstance, PricingProcedureInstanceAdmin)


class RequestDataFileProcedureAdmin(admin.ModelAdmin):
    model = RequestDataFileProcedure
    list_display = [
        "id",
        "master_user",
        "name",
        "user_code",
        "provider",
        "scheme_user_code",
        "date_from",
        "date_from_expr",
        "date_to",
        "date_to_expr",
    ]
    raw_id_fields = ["master_user"]


admin.site.register(RequestDataFileProcedure, RequestDataFileProcedureAdmin)


class RequestDataFileProcedureInstanceAdmin(admin.ModelAdmin):
    model = RequestDataFileProcedureInstance
    list_display = [
        "id",
        "master_user",
        "procedure",
        "created_at",
        "modified_at",
        "status",
    ]
    raw_id_fields = ["master_user"]


admin.site.register(RequestDataFileProcedureInstance, RequestDataFileProcedureInstanceAdmin)


class ExpressionProcedureContextVariableInline(admin.TabularInline):
    model = ExpressionProcedureContextVariable
    fields = ["id", "order", "name", "expression"]


class ExpressionProcedureAdmin(admin.ModelAdmin):
    model = ExpressionProcedure
    list_display = ["id", "master_user", "name", "user_code"]
    raw_id_fields = ["master_user"]
    inlines = [ExpressionProcedureContextVariableInline]


admin.site.register(ExpressionProcedure, ExpressionProcedureAdmin)
