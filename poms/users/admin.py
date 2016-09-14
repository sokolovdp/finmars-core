from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Permission

from poms.audit.admin import HistoricalAdmin
from poms.instruments.models import EventScheduleConfig
from poms.integrations.models import PricingAutomatedSchedule
from poms.users.models import MasterUser, UserProfile, Member, Group, TIMEZONE_CHOICES, FakeSequence


class MemberInline(admin.TabularInline):
    model = Member
    extra = 0
    raw_id_fields = ['user', 'groups', ]


class PricingAutomatedScheduleInline(admin.StackedInline):
    model = PricingAutomatedSchedule
    can_delete = False
    # readonly_fields = ['latest_running', 'latest_task']


class EventScheduleConfigInline(admin.StackedInline):
    model = EventScheduleConfig
    can_delete = False


class MasterUserAdmin(HistoricalAdmin):
    model = MasterUser
    inlines = [
        PricingAutomatedScheduleInline,
        EventScheduleConfigInline,
        MemberInline,
    ]
    list_display = ['id', 'name']
    raw_id_fields = ['currency',
                     'account_type', 'account',
                     'counterparty_group', 'counterparty',
                     'responsible_group', 'responsible',
                     'instrument_type',
                     'portfolio',
                     'strategy1_group', 'strategy1_subgroup', 'strategy1',
                     'strategy2_group', 'strategy2_subgroup', 'strategy2',
                     'strategy3_group', 'strategy3_subgroup', 'strategy3',
                     'thread_group',
                     ]
    fieldsets = (
        (None, {
            'fields': ('name', 'currency', 'language', 'timezone', 'notification_business_days',)
        }),
        ('Defaults', {
            'fields': ('account_type', 'account',
                       'counterparty_group', 'counterparty', 'responsible_group', 'responsible', 'instrument_type',
                       'portfolio', 'strategy1_group', 'strategy1_subgroup', 'strategy1',
                       'strategy2_group', 'strategy2_subgroup', 'strategy2',
                       'strategy3_group', 'strategy3_subgroup', 'strategy3',
                       'thread_group',),
        }),
    )


admin.site.register(MasterUser, MasterUserAdmin)


class MemberAdmin(admin.ModelAdmin):
    model = Member
    list_display = ['id', 'master_user', 'user', 'is_deleted', 'is_owner', 'is_admin']
    list_select_related = ['master_user', 'user']
    list_filter = ['is_deleted', 'is_owner', 'is_admin']
    ordering = ['user', 'master_user']
    raw_id_fields = ['master_user', 'user', 'groups']

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

    def get_inline_instances(self, request, obj=None):
        if obj:
            return super(UserWithProfileAdmin, self).get_inline_instances(request, obj=obj)
        else:
            return []


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


class FakeSequenceAdmin(admin.ModelAdmin):
    model = Group
    list_display = ['id', 'master_user', 'name', 'value']
    list_select_related = ['master_user']
    raw_id_fields = ['master_user']
    readonly_fields = ['master_user', 'name', 'value']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(FakeSequence, FakeSequenceAdmin)
