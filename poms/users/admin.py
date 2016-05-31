from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Permission

from poms.audit.admin import HistoricalAdmin
from poms.users.models import MasterUser, UserProfile, Member, Group, TIMEZONE_CHOICES


class MemberInline(admin.StackedInline):
    model = Member
    extra = 0
    raw_id_fields = ['master_user', 'user']
    filter_horizontal = ('groups',)

    # def formfield_for_manytomany(self, db_field, request=None, **kwargs):
    #     if db_field.name == 'permissions':
    #         qs = kwargs.get('queryset', db_field.remote_field.model.objects)
    #         kwargs['queryset'] = qs.select_related('content_type')
    #     return super(MemberInline, self).formfield_for_manytomany(db_field, request=request, **kwargs)


class MasterUserAdmin(HistoricalAdmin):
    model = MasterUser
    inlines = [MemberInline]
    list_display = ['id', '__str__']


admin.site.register(MasterUser, MasterUserAdmin)


class MemberAdmin(admin.ModelAdmin):
    model = Member
    list_display = ['id', 'master_user', 'user', 'is_owner', 'is_admin']
    list_select_related = ['master_user', 'user']
    filter_horizontal = ('groups',)
    ordering = ['user', 'master_user']
    raw_id_fields = ['master_user', 'user']

    # def formfield_for_manytomany(self, db_field, request=None, **kwargs):
    #     if db_field.name == 'permissions':
    #         qs = kwargs.get('queryset', db_field.remote_field.model.objects)
    #         kwargs['queryset'] = qs.select_related('content_type')
    #     return super(MemberAdmin, self).formfield_for_manytomany(db_field, request=request, **kwargs)


admin.site.register(Member, MemberAdmin)


class UserProfileForm(forms.ModelForm):
    language = forms.ChoiceField(choices=settings.LANGUAGES, initial=settings.LANGUAGE_CODE)
    timezone = forms.ChoiceField(choices=TIMEZONE_CHOICES)

    class Meta:
        model = UserProfile
        fields = ['language', 'timezone']


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    form = UserProfileForm
    can_delete = False


class UserWithProfileAdmin(HistoricalAdmin, UserAdmin):
    inlines = [UserProfileInline]


admin.site.unregister(User)
admin.site.register(User, UserWithProfileAdmin)


class PermissionAdmin(admin.ModelAdmin):
    model = Permission
    list_select_related = ['content_type']
    list_display = ['id', 'content_type', 'codename']
    search_fields = ['codename', 'content_type__app_label', 'content_type__model']

    def has_add_permission(self, request):
        return False


admin.site.register(Permission, PermissionAdmin)


class GroupAdmin(HistoricalAdmin, admin.ModelAdmin):
    model = Group
    list_display = ['id', 'name', 'master_user']
    list_select_related = ['master_user']
    # filter_horizontal = ['permissions']
    raw_id_fields = ['master_user']

    # def formfield_for_manytomany(self, db_field, request=None, **kwargs):
    #     if db_field.name == 'permissions':
    #         qs = kwargs.get('queryset', db_field.remote_field.model.objects)
    #         kwargs['queryset'] = qs.select_related('content_type')
    #     return super(GroupAdmin, self).formfield_for_manytomany(db_field, request=request, **kwargs)


admin.site.register(Group, GroupAdmin)
