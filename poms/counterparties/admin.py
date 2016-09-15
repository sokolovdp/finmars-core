from __future__ import unicode_literals

from django.contrib import admin

from poms.audit.admin import HistoricalAdmin
from poms.common.admin import ClassifierAdmin
from poms.counterparties.models import Counterparty, Responsible, CounterpartyAttributeType, ResponsibleAttributeType, \
    CounterpartyGroup, ResponsibleGroup, CounterpartyClassifier, ResponsibleClassifier
from poms.obj_attrs.admin import AbstractAttributeTypeAdmin, AbstractAttributeInline, \
    AbstractAttributeTypeClassifierInline, AbstractAttributeTypeOptionInline
from poms.obj_perms.admin import UserObjectPermissionInline, \
    GroupObjectPermissionInline


class CounterpartyGroupAdmin(HistoricalAdmin):
    model = CounterpartyGroup
    list_display = ['id', 'master_user', 'name', 'is_deleted', ]
    list_select_related = ['master_user']
    search_fields = ['id', 'user_code', 'name']
    list_filter = ['is_deleted', ]
    raw_id_fields = ['master_user']
    inlines = [
        UserObjectPermissionInline,
        GroupObjectPermissionInline,
    ]


admin.site.register(CounterpartyGroup, CounterpartyGroupAdmin)


class CounterpartyAdmin(HistoricalAdmin):
    model = Counterparty
    list_display = ['id', 'master_user', 'group', 'name', 'is_deleted', ]
    search_fields = ['id', 'user_code', 'name']
    list_filter = ['is_deleted', ]
    list_select_related = ['master_user', 'group']
    raw_id_fields = ['master_user', 'group']
    inlines = [
        AbstractAttributeInline,
        UserObjectPermissionInline,
        GroupObjectPermissionInline,
    ]


admin.site.register(Counterparty, CounterpartyAdmin)


class CounterpartyAttributeTypeAdmin(AbstractAttributeTypeAdmin):
    inlines = [
        # CounterpartyAttributeTypeClassifierInline
        AbstractAttributeTypeClassifierInline,
        AbstractAttributeTypeOptionInline,
        UserObjectPermissionInline,
        GroupObjectPermissionInline,
    ]


admin.site.register(CounterpartyAttributeType, CounterpartyAttributeTypeAdmin)

admin.site.register(CounterpartyClassifier, ClassifierAdmin)


# ------


class ResponsibleGroupAdmin(HistoricalAdmin):
    model = ResponsibleGroup
    list_display = ['id', 'master_user', 'name', 'is_deleted', ]
    list_select_related = ['master_user']
    search_fields = ['id', 'user_code', 'name']
    list_filter = ['is_deleted', ]
    raw_id_fields = ['master_user']
    inlines = [
        UserObjectPermissionInline,
        GroupObjectPermissionInline,
    ]


admin.site.register(ResponsibleGroup, ResponsibleGroupAdmin)


class ResponsibleAdmin(HistoricalAdmin):
    model = Responsible
    list_display = ['id', 'master_user', 'group', 'name', 'is_deleted', ]
    list_select_related = ['master_user', 'group']
    search_fields = ['id', 'user_code', 'name']
    list_filter = ['is_deleted', ]
    raw_id_fields = ['master_user', 'group']
    inlines = [
        AbstractAttributeInline,
        UserObjectPermissionInline,
        GroupObjectPermissionInline,
    ]


admin.site.register(Responsible, ResponsibleAdmin)


class ResponsibleAttributeTypeAdmin(AbstractAttributeTypeAdmin):
    inlines = [
        # CounterpartyAttributeTypeClassifierInline
        AbstractAttributeTypeClassifierInline,
        AbstractAttributeTypeOptionInline,
        UserObjectPermissionInline,
        GroupObjectPermissionInline,
    ]


admin.site.register(ResponsibleAttributeType, ResponsibleAttributeTypeAdmin)

admin.site.register(ResponsibleClassifier, ClassifierAdmin)
