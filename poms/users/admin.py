from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.admin import StackedInline
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group, User, Permission

from poms.users.models import MasterUser, UserProfile, GroupProfile, Member


class MemberInline(admin.TabularInline):
    model = Member
    extra = 0


class MasterUserAdmin(admin.ModelAdmin):
    model = MasterUser
    inlines = [MemberInline]


admin.site.register(MasterUser, MasterUserAdmin)


class UserProfileInline(StackedInline):
    model = UserProfile
    can_delete = False


class UserWithProfileAdmin(UserAdmin):
    inlines = [UserProfileInline]


admin.site.unregister(User)
admin.site.register(User, UserWithProfileAdmin)


class GroupProfileInline(StackedInline):
    model = GroupProfile
    can_delete = False


class GroupWithProfileAdmin(GroupAdmin):
    inlines = [GroupProfileInline]

    def save_model(self, request, obj, form, change):
        profile = getattr(obj, 'profile', None)
        if profile:
            obj.name = profile.group_name
        super(GroupWithProfileAdmin, self).save_model(request, obj, form, change)


admin.site.unregister(Group)
admin.site.register(Group, GroupWithProfileAdmin)

admin.site.register(Permission)
