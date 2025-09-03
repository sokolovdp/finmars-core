from django.contrib import admin

from poms.common.admin import AbstractModelAdmin
from poms.ui.filters import LayoutContentTypeFilter
from poms.ui.models import (
    Bookmark,
    ColorPalette,
    ColorPaletteColor,
    ComplexTransactionUserField,
    ContextMenuLayout,
    CrossEntityAttributeExtension,
    DashboardLayout,
    EditLayout,
    EntityTooltip,
    InstrumentUserField,
    ListLayout,
    MemberLayout,
    PortalInterfaceAccessModel,
    TemplateLayout,
    TransactionUserField,
)


class PortalInterfaceAccessModelAdmin(AbstractModelAdmin):
    model = PortalInterfaceAccessModel
    list_display = ["id", "user_code", "name", "value"]
    search_fields = ["id", "user_code", "name", "value"]


admin.site.register(PortalInterfaceAccessModel, PortalInterfaceAccessModelAdmin)


class BaseLayoutAdmin(AbstractModelAdmin):
    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == "content_type":
            qs = kwargs.get("queryset", db_field.remote_field.model.objects)
            kwargs["queryset"] = LayoutContentTypeFilter().filter_queryset(request, qs, None)
        return super().formfield_for_foreignkey(db_field, request=request, **kwargs)


class ColorPaletteColorAdmin(BaseLayoutAdmin):
    model = ColorPaletteColor
    list_display = ["id", "color_palette", "name", "order", "value", "tooltip"]
    list_select_related = ["color_palette"]
    search_fields = ["id", "name", "value"]
    raw_id_fields = ["color_palette"]


admin.site.register(ColorPaletteColor, ColorPaletteColorAdmin)


class ColorPaletteColorInline(admin.TabularInline):
    model = ColorPaletteColor
    fields = ["id", "name", "value", "order", "tooltip"]


class ColorPaletteAdmin(BaseLayoutAdmin):
    model = ColorPalette
    master_user_path = "master_user"
    list_display = ["id", "master_user", "name", "user_code", "is_default"]
    list_select_related = ["master_user"]
    search_fields = ["id", "name", "user_code"]
    raw_id_fields = ["master_user"]
    inlines = [ColorPaletteColorInline]


admin.site.register(ColorPalette, ColorPaletteAdmin)


class EntityTooltipAdmin(BaseLayoutAdmin):
    model = EntityTooltip
    master_user_path = "master_user"
    list_display = ["id", "master_user", "text", "name", "key"]
    list_select_related = ["master_user"]
    search_fields = ["id", "name", "text"]
    raw_id_fields = ["master_user"]


admin.site.register(EntityTooltip, EntityTooltipAdmin)


class CrossEntityAttributeExtensionAdmin(BaseLayoutAdmin):
    model = CrossEntityAttributeExtension
    master_user_path = "master_user"
    list_display = [
        "id",
        "master_user",
        "context_content_type",
        "content_type_from",
        "content_type_to",
        "key_from",
        "key_to",
        "value_to",
    ]
    list_select_related = ["master_user"]
    search_fields = ["id", "key_from", "key_to", "value_to"]
    raw_id_fields = ["master_user"]


admin.site.register(CrossEntityAttributeExtension, CrossEntityAttributeExtensionAdmin)


class TransactionUserFieldModelAdmin(BaseLayoutAdmin):
    model = TransactionUserField
    master_user_path = "master_user"
    list_display = ["id", "master_user", "name", "key"]
    list_select_related = ["master_user"]
    search_fields = ["id", "name", "key"]
    raw_id_fields = ["master_user"]


admin.site.register(TransactionUserField, TransactionUserFieldModelAdmin)


class InstrumentUserFieldModelAdmin(BaseLayoutAdmin):
    model = InstrumentUserField
    master_user_path = "master_user"
    list_display = ["id", "master_user", "name", "key"]
    list_select_related = ["master_user"]
    search_fields = ["id", "name", "key"]
    raw_id_fields = ["master_user"]


admin.site.register(InstrumentUserField, InstrumentUserFieldModelAdmin)


class ComplexTransactionUserFieldModelAdmin(BaseLayoutAdmin):
    model = ComplexTransactionUserField
    master_user_path = "master_user"
    list_display = ["id", "master_user", "name", "key"]
    list_select_related = ["master_user"]
    search_fields = ["id", "name", "key"]
    raw_id_fields = ["master_user"]


admin.site.register(ComplexTransactionUserField, ComplexTransactionUserFieldModelAdmin)


class ListLayoutAdmin(BaseLayoutAdmin):
    model = ListLayout
    master_user_path = "member__master_user"
    list_display = ["id", "master_user", "member", "content_type", "name", "user_code"]
    list_select_related = ["member__master_user", "member", "content_type"]
    search_fields = ["id", "name"]
    raw_id_fields = ["member"]

    def master_user(self, obj):
        return obj.member.master_user

    master_user.admin_order_field = "member__master_user"


admin.site.register(ListLayout, ListLayoutAdmin)


class DashboardLayoutAdmin(BaseLayoutAdmin):
    model = DashboardLayout
    master_user_path = "member__master_user"
    list_display = ["id", "master_user", "member", "name", "user_code"]
    list_select_related = ["member__master_user", "member"]
    search_fields = ["id", "name"]
    raw_id_fields = ["member"]

    def master_user(self, obj):
        return obj.member.master_user

    master_user.admin_order_field = "member__master_user"


admin.site.register(DashboardLayout, DashboardLayoutAdmin)


class MemberLayoutAdmin(BaseLayoutAdmin):
    model = MemberLayout
    master_user_path = "member__master_user"
    list_display = ["id", "master_user", "member", "name", "user_code"]
    list_select_related = ["member__master_user", "member"]
    search_fields = ["id", "name"]
    raw_id_fields = ["member"]

    def master_user(self, obj):
        return obj.member.master_user

    master_user.admin_order_field = "member__master_user"


admin.site.register(MemberLayout, MemberLayoutAdmin)


class ContextMenuLayoutAdmin(BaseLayoutAdmin):
    model = ContextMenuLayout
    master_user_path = "member__master_user"
    list_display = ["id", "master_user", "member", "name", "user_code"]
    list_select_related = ["member__master_user", "member"]
    search_fields = ["id", "name"]
    raw_id_fields = ["member"]

    def master_user(self, obj):
        return obj.member.master_user

    master_user.admin_order_field = "member__master_user"


admin.site.register(ContextMenuLayout, ContextMenuLayoutAdmin)


class TemplateLayoutAdmin(BaseLayoutAdmin):
    model = TemplateLayout
    master_user_path = "member__master_user"
    list_display = ["id", "master_user", "member", "name", "user_code"]
    list_select_related = ["member__master_user", "member"]
    search_fields = ["id", "name"]
    raw_id_fields = ["member"]

    def master_user(self, obj):
        return obj.member.master_user

    master_user.admin_order_field = "member__master_user"


admin.site.register(TemplateLayout, TemplateLayoutAdmin)


class EditLayoutAdmin(BaseLayoutAdmin):
    model = EditLayout
    master_user_path = "member__master_user"
    list_display = ["id", "master_user", "member", "content_type"]
    list_select_related = ["member", "content_type"]
    search_fields = ["id"]
    raw_id_fields = ["member"]

    def master_user(self, obj):
        return obj.member.master_user

    master_user.admin_order_field = "member__master_user"


admin.site.register(EditLayout, EditLayoutAdmin)


class BookmarkAdmin(AbstractModelAdmin):
    model = Bookmark
    master_user_path = "member__master_user"
    list_display = [
        "id",
        "master_user",
        "member",
        "tree_id",
        "level",
        "parent",
        "name",
    ]
    list_select_related = ["member", "member__master_user", "parent"]
    # ordering = ['member', 'tree_id', 'level', ]
    raw_id_fields = ["member", "parent", "list_layout"]
    save_as = True

    def master_user(self, obj):
        return obj.member.master_user

    master_user.admin_order_field = "member__master_user"


admin.site.register(Bookmark, BookmarkAdmin)
