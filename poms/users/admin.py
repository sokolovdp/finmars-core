from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.admin import StackedInline
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group, User

from poms.users.models import MasterUser, UserProfile, GroupProfile


# class PrivateGroupInline(StackedInline):
#     model = PrivateGroup


# class PatchedGroupAdmin(GroupAdmin):
#     pass
#     # list_display = ['name']
#     # list_display_links = ['name']
#     # inlines = (PrivateGroupInline,)
#
#     # def save_model(self, request, obj, form, change):
#     #     super(PatchedGroupAdmin, self).save_model(request, obj, form, change)
#     #     if hasattr(obj, 'owner'):
#     #         obj.name = '%s:%s' % (obj.owner.master_user_id, obj.owner.name)
#     #         # import uuid
#     #         # obj.name = uuid.uuid4().hex
#     #         # obj.save(update_fields=['name'])
#
#     # def get_queryset(self, request):
#     #     qs = super(PatchedGroupAdmin, self).get_queryset(request)
#     #     qs = qs.exclude(pk__in=PrivateGroup.objects.values('group_id'))
#     #     return qs
#
#
# admin.site.unregister(Group)
# admin.site.register(Group, PatchedGroupAdmin)


# class PrivateGroupForm(forms.ModelForm):
#     permissions = forms.ModelMultipleChoiceField(queryset=Permission.objects.all(),
#                                                  widget=FilteredSelectMultiple(_('permissions'), False))
#
#     class Meta:
#         model = PrivateGroup
#         # exclude = []
#         fields = ['master_user', 'name', 'permissions']
#
#     def __init__(self, *args, **kwargs):
#         if kwargs.get('instance'):
#             initial = kwargs.setdefault('initial', {})
#             initial['permissions'] = [p.pk for p in kwargs['instance'].group.permissions.all()]
#         super(PrivateGroupForm, self).__init__(*args, **kwargs)
#
#     def save(self, commit=True):
#         permissions = self.cleaned_data.get('permissions', None)
#         if self.instance.master_user_id:
#             name = '%s (%s)' % (self.instance.name, self.instance.master_user.user.username)
#         else:
#             name = '%s (%s)' % (self.instance.name, "Global")
#         if self.instance.group_id is None:
#             self.instance.group = Group.objects.create(name=name)
#         instance = super(PrivateGroupForm, self).save(commit=commit)
#         instance.group.permissions = permissions
#         instance.group.name = name
#         instance.group.save(update_fields=['name'])
#         return instance
#
#
# class PrivateGroupAdmin(admin.ModelAdmin):
#     model = PrivateGroup
#     form = PrivateGroupForm
#     list_display = ['name', 'master_user']
#
#
# admin.site.register(PrivateGroup, PrivateGroupAdmin)




# class UserProfileInline(StackedInline):
#     model = UserProfile
#     extra = 0


class MasterUserAdmin(admin.ModelAdmin):
    model = MasterUser
    # inlines = [UserProfileInline]


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
            obj.name = '%s (%s)' % (profile.name, profile.master_user,)
        super(GroupWithProfileAdmin, self).save_model(request, obj, form, change)


admin.site.unregister(Group)
admin.site.register(Group, GroupWithProfileAdmin)


# class UserCreationForm1(UserCreationForm):
#     type = forms.ChoiceField(required=True,
#                              choices=[['0', _('System user')], ['1', _('Master user')], ['2', _('Employee user')]])
#     master_user = forms.ModelChoiceField(queryset=MasterUser.objects.all(), required=False,
#                                          help_text=_("Required for employee"))
#
#     class Meta:
#         model = User
#         fields = ("type", "username",)\
#
#     # def clean_master_user(self):
#     #     type = self.cleaned_data.get("type")
#     #     master_user = self.cleaned_data.get("master_user")
#     #     if type == "2" and master_user is None:
#     #         raise forms.ValidationError(
#     #             self.error_messages['password_mismatch'],
#     #             code='password_mismatch',
#     #         )
#     #     return master_user
#
#     def save(self, commit=True):
#         user = super(UserCreationForm1, self).save(commit=True)
#         type = self.cleaned_data.get("type")
#         if type == "1":
#             MasterUser.objects.create(user=user)
#         elif type == "2":
#             Employee.objects.create(user=user, master_user=self.cleaned_data.get("master_user"))
#         return user
#

# class MasterUserInline(StackedInline):
#     model = MasterUser
#
#     # extra = 1
#     # can_delete = False
#
#     def has_add_permission(self, request):
#         return False
#
#     def has_change_permission(self, request, obj=None):
#         return obj is None and hasattr(obj, 'master_user')
#
#     def has_delete_permission(self, request, obj=None):
#         return obj is not None and hasattr(obj, 'master_user')
#
#
# class EmployeeInline1(StackedInline):
#     model = Employee
#
#     # extra = 1
#     # can_delete = False
#
#     def has_add_permission(self, request):
#         return False
#
#     def has_change_permission(self, request, obj=None):
#         # return obj is not None and hasattr(obj, 'employee')
#         return obj is None and hasattr(obj, 'employee')
#
#     def has_delete_permission(self, request, obj=None):
#         return obj is not None and hasattr(obj, 'employee')
#
#
# class UserAdmin1(UserAdmin):
#     add_form = UserCreationForm1
#     add_fieldsets = (
#         (None, {
#             'classes': ('wide',),
#             'fields': ('username', 'password1', 'password2', 'type', 'master_user'),
#         }),
#     )
#     inlines = [MasterUserInline, EmployeeInline1]
#
#
# admin.site.unregister(User)
# admin.site.register(User, UserAdmin1)

# ----------------------

# class GroupProfileInline(StackedInline):
#     model = GroupProfile
#
#
# class GroupAdmin1(GroupAdmin):
#     inlines = [GroupProfileInline]
#
#
# admin.site.unregister(Group)
# admin.site.register(Group, GroupAdmin1)
#
#
# # class UserProfileInline(StackedInline):
# #     model = UserProfile
# #     can_delete = False
#
#
# class MasterUser2Inline(StackedInline):
#     model = MasterUser2
#     can_delete = False
#
#
# class Employee2Inline(StackedInline):
#     model = Employee2
#     can_delete = False
#
#
# class UserAdmin1(UserAdmin):
#     inlines = [MasterUser2Inline, Employee2Inline]
#
#
# admin.site.unregister(User)
# admin.site.register(User, UserAdmin1)
#
#
# class Employee21Inline(StackedInline):
#     model = Employee2
#     extra = 0
#     fk_name = 'master_user'
#
#
# class MasterUser2Admin(admin.ModelAdmin):
#     model = MasterUser2
#     inlines = [Employee21Inline]
#
#
# admin.site.register(MasterUser2, MasterUser2Admin)
#
#
# class Employee2Admin(admin.ModelAdmin):
#     model = Employee2
#
#
# admin.site.register(Employee2, Employee2Admin)
#
#
# class GroupProfileAdmin(admin.ModelAdmin):
#     model = GroupProfile
#
# admin.site.register(GroupProfile, GroupProfileAdmin)
