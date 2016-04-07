from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.admin import StackedInline
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType

from poms.audit.admin import HistoricalAdmin
from poms.users.models import MasterUser, UserProfile, Member, Group


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
    inlines = [MemberInline]
    list_display = ['id', '__str__']


admin.site.register(MasterUser, MasterUserAdmin)


class MemberAdmin(admin.ModelAdmin):
    model = Member
    list_display = ['id', 'master_user', 'user', 'is_owner', 'is_admin']
    list_select_related = ['master_user', 'user']
    filter_horizontal = ('groups', 'permissions',)
    ordering = ['user', 'master_user']
    raw_id_fields = ['master_user', 'user']

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

admin.site.register(Permission)


class GroupAdmin(HistoricalAdmin, admin.ModelAdmin):
    model = Group
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']
    filter_horizontal = ['permissions']
    raw_id_fields = ['master_user']

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == 'permissions':
            qs = kwargs.get('queryset', db_field.remote_field.model.objects)
            kwargs['queryset'] = qs.select_related('content_type')
        return super(GroupAdmin, self).formfield_for_manytomany(db_field, request=request, **kwargs)


admin.site.register(Group, GroupAdmin)


class UserObjectPermissionAdminBase(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'permission':
            qs = kwargs.get('queryset', db_field.remote_field.model.objects)
            obj_field = self.model._meta.get_field('content_object')
            obj_ctype = ContentType.objects.get_for_model(obj_field.rel.to)
            kwargs['queryset'] = qs.select_related('content_type').filter(content_type=obj_ctype)
            # kwargs['queryset'] = qs.select_related('content_type')
        return super(UserObjectPermissionAdminBase, self).formfield_for_foreignkey(db_field, request=request, **kwargs)


class UserObjectPermissionAdmin(UserObjectPermissionAdminBase):
    raw_id_fields = ['member', 'content_object']
    list_display = ['id', 'member', 'permission', 'content_object']
    search_fields = ['content_object__id', 'member__id', 'member__user__username']
    # list_filter = ['permission']


class GroupObjectPermissionAdmin(UserObjectPermissionAdminBase):
    raw_id_fields = ['group', 'content_object']
    list_display = ['id', 'group', 'permission', 'content_object']
    search_fields = ['content_object__id', 'group__id', 'group__name']
    # list_filter = ['permission']
