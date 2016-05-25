from __future__ import unicode_literals

from django.contrib import admin

from poms.audit.admin import HistoricalAdmin
from poms.common.admin import TreeModelAdmin
from poms.obj_perms.admin import GroupObjectPermissionAdmin
from poms.strategies.models import Strategy, StrategyGroupObjectPermission, Strategy1, \
    Strategy1GroupObjectPermission, Strategy2, Strategy2GroupObjectPermission, Strategy3, Strategy3GroupObjectPermission


class StrategyAdmin(HistoricalAdmin, TreeModelAdmin):
    list_display = ['id', 'master_user', 'formatted_name', 'parent', ]
    list_select_related = ['master_user', 'parent']
    raw_id_fields = ['master_user', 'parent']
    fields = ['master_user', 'parent', 'user_code', 'name', 'short_name', 'notes']


# admin.site.register(Strategy, StrategyAdmin)
# # admin.site.register(StrategyUserObjectPermission, UserObjectPermissionAdmin)
# admin.site.register(StrategyGroupObjectPermission, GroupObjectPermissionAdmin)

admin.site.register(Strategy1, StrategyAdmin)
# admin.site.register(Strategy1UserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(Strategy1GroupObjectPermission, GroupObjectPermissionAdmin)

admin.site.register(Strategy2, StrategyAdmin)
# admin.site.register(Strategy2UserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(Strategy2GroupObjectPermission, GroupObjectPermissionAdmin)

admin.site.register(Strategy3, StrategyAdmin)
# admin.site.register(Strategy3UserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(Strategy3GroupObjectPermission, GroupObjectPermissionAdmin)
