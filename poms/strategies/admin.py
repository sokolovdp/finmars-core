from __future__ import unicode_literals

from django.contrib import admin

from poms.common.admin import ClassifierAdmin
from poms.obj_perms.admin import GroupObjectPermissionAdmin
from poms.strategies.models import Strategy, StrategyGroupObjectPermission, Strategy1, \
    Strategy1GroupObjectPermission, Strategy2, Strategy2GroupObjectPermission, Strategy3, Strategy3GroupObjectPermission

admin.site.register(Strategy, ClassifierAdmin)
# admin.site.register(StrategyUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(StrategyGroupObjectPermission, GroupObjectPermissionAdmin)

admin.site.register(Strategy1, ClassifierAdmin)
# admin.site.register(Strategy1UserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(Strategy1GroupObjectPermission, GroupObjectPermissionAdmin)

admin.site.register(Strategy2, ClassifierAdmin)
# admin.site.register(Strategy2UserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(Strategy2GroupObjectPermission, GroupObjectPermissionAdmin)

admin.site.register(Strategy3, ClassifierAdmin)
# admin.site.register(Strategy3UserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(Strategy3GroupObjectPermission, GroupObjectPermissionAdmin)
