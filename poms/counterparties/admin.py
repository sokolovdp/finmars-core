from __future__ import unicode_literals

from django.contrib import admin

from poms.audit.admin import HistoricalAdmin
from poms.common.admin import ClassifierAdmin
from poms.counterparties.models import Counterparty, Responsible, CounterpartyClassifier, ResponsibleClassifier, \
    CounterpartyGroupObjectPermission, ResponsibleGroupObjectPermission, \
    CounterpartyAttributeType, CounterpartyAttributeTypeOption, CounterpartyAttributeTypeGroupObjectPermission, \
    ResponsibleAttributeType, ResponsibleAttributeTypeOption, \
    ResponsibleAttributeTypeGroupObjectPermission, CounterpartyAttribute, \
    ResponsibleAttribute
from poms.obj_attrs.admin import AttributeTypeAdminBase, AttributeTypeOptionInlineBase, AttributeInlineBase
from poms.obj_perms.admin import GroupObjectPermissionAdmin

admin.site.register(CounterpartyClassifier, ClassifierAdmin)
# admin.site.register(CounterpartyClassifierUserObjectPermission, UserObjectPermissionAdmin)
# admin.site.register(CounterpartyClassifierGroupObjectPermission, GroupObjectPermissionAdmin)


class CounterpartyAttributeInline(AttributeInlineBase):
    model = CounterpartyAttribute


class CounterpartyAdmin(HistoricalAdmin):
    model = Counterparty
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']
    raw_id_fields = ['master_user']
    inlines = [CounterpartyAttributeInline]


admin.site.register(Counterparty, CounterpartyAdmin)
# admin.site.register(CounterpartyUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(CounterpartyGroupObjectPermission, GroupObjectPermissionAdmin)

admin.site.register(ResponsibleClassifier, ClassifierAdmin)
# admin.site.register(ResponsibleClassifierUserObjectPermission, UserObjectPermissionAdmin)
# admin.site.register(ResponsibleClassifierGroupObjectPermission, GroupObjectPermissionAdmin)


class ResponsibleAttributeInline(AttributeInlineBase):
    model = ResponsibleAttribute


class ResponsibleAdmin(HistoricalAdmin):
    model = Responsible
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']
    raw_id_fields = ['master_user']
    inlines = [ResponsibleAttributeInline]


admin.site.register(Responsible, ResponsibleAdmin)
# admin.site.register(ResponsibleUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(ResponsibleGroupObjectPermission, GroupObjectPermissionAdmin)

admin.site.register(CounterpartyAttributeType, AttributeTypeAdminBase)
admin.site.register(CounterpartyAttributeTypeOption, AttributeTypeOptionInlineBase)
# admin.site.register(CounterpartyAttributeTypeUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(CounterpartyAttributeTypeGroupObjectPermission, GroupObjectPermissionAdmin)

admin.site.register(ResponsibleAttributeType, AttributeTypeAdminBase)
admin.site.register(ResponsibleAttributeTypeOption, AttributeTypeOptionInlineBase)
# admin.site.register(ResponsibleAttributeTypeUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(ResponsibleAttributeTypeGroupObjectPermission, GroupObjectPermissionAdmin)
