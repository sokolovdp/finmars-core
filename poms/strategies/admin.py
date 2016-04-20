from __future__ import unicode_literals

from django.contrib import admin

from poms.common.admin import ClassifierAdmin
from poms.obj_perms.admin import UserObjectPermissionAdmin, GroupObjectPermissionAdmin
from poms.strategies.models import Strategy, StrategyUserObjectPermission, StrategyGroupObjectPermission


admin.site.register(Strategy, ClassifierAdmin)
admin.site.register(StrategyUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(StrategyGroupObjectPermission, GroupObjectPermissionAdmin)
