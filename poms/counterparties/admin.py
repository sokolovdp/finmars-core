from __future__ import unicode_literals

from django.contrib import admin

from poms.common.admin import ClassifierAdmin
from poms.counterparties.models import Counterparty, Responsible, CounterpartyAttributeType, ResponsibleAttributeType, \
    CounterpartyGroup, ResponsibleGroup, CounterpartyClassifier, ResponsibleClassifier
from poms.obj_attrs.admin import AbstractAttributeTypeAdmin, AbstractAttributeInline, \
    AbstractAttributeTypeClassifierInline, AbstractAttributeTypeOptionInline
from poms.obj_perms.admin import GenericObjectPermissionInline
from poms.tags.admin import GenericTagLinkInline


class CounterpartyGroupAdmin(admin.ModelAdmin):
    model = CounterpartyGroup
    list_display = ['id', 'master_user', 'user_code', 'name', 'is_deleted', ]
    list_select_related = ['master_user']
    search_fields = ['id', 'user_code', 'name']
    list_filter = ['is_deleted', ]
    raw_id_fields = ['master_user']
    inlines = [
        GenericTagLinkInline,
        GenericObjectPermissionInline,
        # UserObjectPermissionInline,
        # GroupObjectPermissionInline,
    ]


admin.site.register(CounterpartyGroup, CounterpartyGroupAdmin)


class CounterpartyAdmin(admin.ModelAdmin):
    model = Counterparty
    list_display = ['id', 'master_user', 'group', 'user_code', 'name', 'is_deleted', ]
    ordering = ['master_user', 'group', 'user_code']
    search_fields = ['id', 'user_code', 'name']
    list_filter = ['is_deleted', ]
    list_select_related = ['master_user', 'group']
    raw_id_fields = ['master_user', 'group']
    inlines = [
        AbstractAttributeInline,
        GenericTagLinkInline,
        GenericObjectPermissionInline,
        # UserObjectPermissionInline,
        # GroupObjectPermissionInline,
    ]


admin.site.register(Counterparty, CounterpartyAdmin)


class CounterpartyAttributeTypeAdmin(AbstractAttributeTypeAdmin):
    inlines = [
        # CounterpartyAttributeTypeClassifierInline
        AbstractAttributeTypeClassifierInline,
        AbstractAttributeTypeOptionInline,
        GenericObjectPermissionInline,
        # UserObjectPermissionInline,
        # GroupObjectPermissionInline,
    ]


admin.site.register(CounterpartyAttributeType, CounterpartyAttributeTypeAdmin)

admin.site.register(CounterpartyClassifier, ClassifierAdmin)


# ------


class ResponsibleGroupAdmin(admin.ModelAdmin):
    model = ResponsibleGroup
    list_display = ['id', 'master_user', 'user_code', 'name', 'is_deleted', ]
    list_select_related = ['master_user']
    search_fields = ['id', 'user_code', 'name']
    list_filter = ['is_deleted', ]
    raw_id_fields = ['master_user']
    inlines = [
        GenericTagLinkInline,
        GenericObjectPermissionInline,
        # UserObjectPermissionInline,
        # GroupObjectPermissionInline,
    ]


admin.site.register(ResponsibleGroup, ResponsibleGroupAdmin)


class ResponsibleAdmin(admin.ModelAdmin):
    model = Responsible
    list_display = ['id', 'master_user', 'group', 'user_code', 'name', 'is_deleted', ]
    list_select_related = ['master_user', 'group']
    ordering = ['master_user', 'group', 'user_code']
    search_fields = ['id', 'user_code', 'name']
    list_filter = ['is_deleted', ]
    raw_id_fields = ['master_user', 'group']
    inlines = [
        AbstractAttributeInline,
        GenericTagLinkInline,
        GenericObjectPermissionInline,
        # UserObjectPermissionInline,
        # GroupObjectPermissionInline,
    ]


admin.site.register(Responsible, ResponsibleAdmin)


class ResponsibleAttributeTypeAdmin(AbstractAttributeTypeAdmin):
    inlines = [
        # CounterpartyAttributeTypeClassifierInline
        AbstractAttributeTypeClassifierInline,
        AbstractAttributeTypeOptionInline,
        GenericObjectPermissionInline,
        # UserObjectPermissionInline,
        # GroupObjectPermissionInline,
    ]


admin.site.register(ResponsibleAttributeType, ResponsibleAttributeTypeAdmin)

admin.site.register(ResponsibleClassifier, ClassifierAdmin)
