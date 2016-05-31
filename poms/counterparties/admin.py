from __future__ import unicode_literals

from django.contrib import admin

from poms.audit.admin import HistoricalAdmin
from poms.common.admin import ClassifierAdmin
from poms.counterparties.models import Counterparty, Responsible, CounterpartyClassifier, ResponsibleClassifier, \
    CounterpartyGroupObjectPermission, ResponsibleGroupObjectPermission, \
    CounterpartyAttributeType, CounterpartyAttributeTypeOption, CounterpartyAttributeTypeGroupObjectPermission, \
    ResponsibleAttributeType, ResponsibleAttributeTypeOption, \
    ResponsibleAttributeTypeGroupObjectPermission, CounterpartyAttribute, \
    ResponsibleAttribute, CounterpartyUserObjectPermission, CounterpartyAttributeTypeUserObjectPermission, \
    ResponsibleUserObjectPermission, ResponsibleAttributeTypeUserObjectPermission
from poms.obj_attrs.admin import AttributeTypeAdminBase, AttributeTypeOptionAdminBase, AttributeInlineBase, \
    AttributeTypeClassifierInlineBase
from poms.obj_perms.admin import GroupObjectPermissionAdmin, UserObjectPermissionAdmin


class CounterpartyAttributeInline(AttributeInlineBase):
    model = CounterpartyAttribute


class CounterpartyAdmin(HistoricalAdmin):
    model = Counterparty
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']
    raw_id_fields = ['master_user']
    inlines = [CounterpartyAttributeInline]


admin.site.register(Counterparty, CounterpartyAdmin)
admin.site.register(CounterpartyUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(CounterpartyGroupObjectPermission, GroupObjectPermissionAdmin)


class CounterpartyAttributeTypeClassifierInline(AttributeTypeClassifierInlineBase):
    model = CounterpartyClassifier


class CounterpartyAttributeTypeAdmin(AttributeTypeAdminBase):
    inlines = [CounterpartyAttributeTypeClassifierInline]


admin.site.register(CounterpartyAttributeType, CounterpartyAttributeTypeAdmin)
admin.site.register(CounterpartyAttributeTypeOption, AttributeTypeOptionAdminBase)
admin.site.register(CounterpartyAttributeTypeUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(CounterpartyAttributeTypeGroupObjectPermission, GroupObjectPermissionAdmin)

admin.site.register(CounterpartyClassifier, ClassifierAdmin)


# admin.site.register(CounterpartyClassifierUserObjectPermission, UserObjectPermissionAdmin)
# admin.site.register(CounterpartyClassifierGroupObjectPermission, GroupObjectPermissionAdmin)


class ResponsibleAttributeInline(AttributeInlineBase):
    model = ResponsibleAttribute


class ResponsibleAdmin(HistoricalAdmin):
    model = Responsible
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']
    raw_id_fields = ['master_user']
    inlines = [ResponsibleAttributeInline]


admin.site.register(Responsible, ResponsibleAdmin)
admin.site.register(ResponsibleUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(ResponsibleGroupObjectPermission, GroupObjectPermissionAdmin)


class ResponsibleAttributeTypeClassifierInline(AttributeTypeClassifierInlineBase):
    model = ResponsibleClassifier


class ResponsibleAttributeTypeAdmin(AttributeTypeAdminBase):
    inlines = [ResponsibleAttributeTypeClassifierInline]


admin.site.register(ResponsibleAttributeType, ResponsibleAttributeTypeAdmin)
admin.site.register(ResponsibleAttributeTypeOption, AttributeTypeOptionAdminBase)
admin.site.register(ResponsibleAttributeTypeUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(ResponsibleAttributeTypeGroupObjectPermission, GroupObjectPermissionAdmin)

admin.site.register(ResponsibleClassifier, ClassifierAdmin)
# admin.site.register(ResponsibleClassifierUserObjectPermission, UserObjectPermissionAdmin)
# admin.site.register(ResponsibleClassifierGroupObjectPermission, GroupObjectPermissionAdmin)
