from __future__ import unicode_literals

from django.contrib import admin

from poms.common.admin import AbstractModelAdmin
from poms.counterparties.models import Counterparty, Responsible,  CounterpartyGroup, ResponsibleGroup
from poms.obj_attrs.admin import GenericAttributeInline
from poms.obj_perms.admin import GenericObjectPermissionInline
from poms.tags.admin import GenericTagLinkInline


class CounterpartyGroupAdmin(AbstractModelAdmin):
    model = CounterpartyGroup
    master_user_path = 'master_user'
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


class CounterpartyAdmin(AbstractModelAdmin):
    model = Counterparty
    master_user_path = 'master_user'
    list_display = ['id', 'master_user', 'group', 'user_code', 'name', 'is_deleted', ]
    ordering = ['master_user', 'group', 'user_code']
    search_fields = ['id', 'user_code', 'name']
    list_filter = ['is_deleted', ]
    list_select_related = ['master_user', 'group']
    raw_id_fields = ['master_user', 'group']
    inlines = [
        # AbstractAttributeInline,
        GenericAttributeInline,
        GenericTagLinkInline,
        GenericObjectPermissionInline,
        # UserObjectPermissionInline,
        # GroupObjectPermissionInline,
    ]


admin.site.register(Counterparty, CounterpartyAdmin)


# class CounterpartyAttributeTypeAdmin(AbstractAttributeTypeAdmin):
#     inlines = [
#         # CounterpartyAttributeTypeClassifierInline
#         AbstractAttributeTypeClassifierInline,
#         AbstractAttributeTypeOptionInline,
#         GenericObjectPermissionInline,
#         # UserObjectPermissionInline,
#         # GroupObjectPermissionInline,
#     ]
#
#
# admin.site.register(CounterpartyAttributeType, CounterpartyAttributeTypeAdmin)
#
# admin.site.register(CounterpartyClassifier, ClassifierAdmin)


# ------


class ResponsibleGroupAdmin(AbstractModelAdmin):
    model = ResponsibleGroup
    master_user_path = 'master_user'
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


class ResponsibleAdmin(AbstractModelAdmin):
    model = Responsible
    master_user_path = 'master_user'
    list_display = ['id', 'master_user', 'group', 'user_code', 'name', 'is_deleted', ]
    list_select_related = ['master_user', 'group']
    ordering = ['master_user', 'group', 'user_code']
    search_fields = ['id', 'user_code', 'name']
    list_filter = ['is_deleted', ]
    raw_id_fields = ['master_user', 'group']
    inlines = [
        # AbstractAttributeInline,
        GenericAttributeInline,
        GenericTagLinkInline,
        GenericObjectPermissionInline,
        # UserObjectPermissionInline,
        # GroupObjectPermissionInline,
    ]


admin.site.register(Responsible, ResponsibleAdmin)


# class ResponsibleAttributeTypeAdmin(AbstractAttributeTypeAdmin):
#     inlines = [
#         # CounterpartyAttributeTypeClassifierInline
#         AbstractAttributeTypeClassifierInline,
#         AbstractAttributeTypeOptionInline,
#         GenericObjectPermissionInline,
#         # UserObjectPermissionInline,
#         # GroupObjectPermissionInline,
#     ]
#
#
# admin.site.register(ResponsibleAttributeType, ResponsibleAttributeTypeAdmin)
#
# admin.site.register(ResponsibleClassifier, ClassifierAdmin)
