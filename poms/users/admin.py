from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.admin import StackedInline
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group, User, Permission

from poms.audit.admin import HistoricalAdmin
from poms.users.models import MasterUser, UserProfile, GroupProfile, Member, Group2


class MemberInline(admin.StackedInline):
    model = Member
    extra = 0
    filter_horizontal = ('groups', 'permissions',)

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == 'permissions':
            qs = kwargs.get('queryset', db_field.remote_field.model.objects)
            kwargs['queryset'] = qs.select_related('content_type')
        return super(MemberInline, self).formfield_for_manytomany(db_field, request=request, **kwargs)


class MasterUserAdmin(HistoricalAdmin):
    model = MasterUser
    # inlines = [MemberInline]
    list_display = ['id', '__str__']


admin.site.register(MasterUser, MasterUserAdmin)


class MemberAdmin(admin.ModelAdmin):
    model = Member
    list_display = ['id', 'user', 'master_user', 'is_owner', 'is_admin']
    filter_horizontal = ('groups', 'permissions',)
    ordering = ['user', 'master_user']

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == 'permissions':
            qs = kwargs.get('queryset', db_field.remote_field.model.objects)
            kwargs['queryset'] = qs.select_related('content_type')
        return super(MemberAdmin, self).formfield_for_manytomany(db_field, request=request, **kwargs)


admin.site.register(Member, MemberAdmin)


class UserProfileInline(StackedInline):
    model = UserProfile
    can_delete = False


class UserWithProfileAdmin(HistoricalAdmin, UserAdmin):
    inlines = [UserProfileInline]


admin.site.unregister(User)
admin.site.register(User, UserWithProfileAdmin)


class GroupProfileInline(StackedInline):
    model = GroupProfile
    can_delete = False


class GroupWithProfileAdmin(HistoricalAdmin, GroupAdmin):
    inlines = [GroupProfileInline]

    def save_model(self, request, obj, form, change):
        profile = getattr(obj, 'profile', None)
        if profile:
            obj.name = profile.group_name
        super(GroupWithProfileAdmin, self).save_model(request, obj, form, change)


admin.site.unregister(Group)
admin.site.register(Group, GroupWithProfileAdmin)

admin.site.register(Permission)


class Group2Admin(HistoricalAdmin, admin.ModelAdmin):
    model = Group2
    filter_horizontal = ('permissions',)

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == 'permissions':
            qs = kwargs.get('queryset', db_field.remote_field.model.objects)
            kwargs['queryset'] = qs.select_related('content_type')
        return super(Group2Admin, self).formfield_for_manytomany(db_field, request=request, **kwargs)


admin.site.register(Group2, Group2Admin)
