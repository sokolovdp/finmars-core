from __future__ import unicode_literals

from django import forms
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from reversion.admin import VersionAdmin

from poms.audit.models import AuthLogEntry, ObjectHistoryEntry
from poms.users.models import MasterUser, Member


class AuthLogEntryAdmin(admin.ModelAdmin):
    model = AuthLogEntry
    list_display = ['id', 'date', 'user', 'is_success', 'user_ip', 'user_agent']
    list_select_related = ['user']
    date_hierarchy = 'date'
    ordering = ('-date',)
    fields = ['id', 'date', 'user', 'is_success', 'user_ip', 'user_agent']
    readonly_fields = ['id', 'date', 'is_success', 'user', 'user_ip', 'user_agent', ]

    def has_add_permission(self, request):
        return False


admin.site.register(AuthLogEntry, AuthLogEntryAdmin)


class HistoricalAdmin(VersionAdmin):
    history_latest_first = True
    ignore_duplicate_revisions = True


# class HistoryEntryForm(forms.ModelForm):
#     # id = forms.IntegerField(widget=forms.TextInput())
#     master_user = forms.ModelChoiceField(queryset=MasterUser.objects)
#     member = forms.ModelChoiceField(queryset=Member.objects)
#     action_flag = forms.ChoiceField(choices=HistoryEntry.FLAG_CHOICES)
#
#     class Meta:
#         model = HistoryEntry
#         fields = [
#             # 'id',
#             'master_user',
#             'member',
#             # 'created',
#             'action_flag',
#             'content_type',
#             'object_id',
#             # 'content_object',
#             'message',
#             'json',
#         ]
#         readonly_fields = ('id', 'created', 'content_object')
#         raw_id_fields = ('master_user', 'member')
#
#
# class ContentTypeFilter(admin.SimpleListFilter):
#     title = _('content type')
#     parameter_name = 'content_type'
#
#     def lookups(self, request, model_admin):
#         qs = ContentType.objects.order_by('app_label', 'model').exclude(model__endswith="objectpermission")
#         # return [(ctype.id, '%s.%s' % (ctype.app_label, ctype.model)) for ctype in qs]
#         return [(ctype.id, '%s.%s' % (ctype.app_label, ctype.model)) for ctype in qs]
#
#     def queryset(self, request, queryset):
#         if self.value():
#             return queryset.filter(content_type=int(self.value()))
#         else:
#             return queryset


class ObjectHistoryEntryAdmin(admin.ModelAdmin):
    model = ObjectHistoryEntry
    # form = HistoryEntryForm
    list_display = ('id', 'created', 'master_user', 'member', 'action_flag', 'content_type', 'object_id',
                    'message',)
    list_select_related = ('master_user', 'member',)
    fields = (
        'id',
        ('master_user', 'member'),
        ('created', 'action_flag'),
        ('content_type', 'object_id', 'content_object'),
        'message'
    )
    list_filter = ('action_flag', )
    date_hierarchy = 'created'
    search_fields = ('object_id',)
    readonly_fields = ('id', 'created', 'content_object', 'master_user', 'member', 'created', 'action_flag',
                       'content_type', 'object_id', 'content_object', 'message')
    raw_id_fields = ('master_user', 'member',)
    # list_filter = ('action_flag', ContentTypeFilter)

    def get_queryset(self, request):
        qs = super(ObjectHistoryEntryAdmin, self).get_queryset(request)
        qs = qs.prefetch_related('content_object')
        return qs

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'content_type':
            qs = kwargs.get('queryset', db_field.remote_field.model.objects)
            kwargs['queryset'] = qs.order_by('model')
        return super(ObjectHistoryEntryAdmin, self).formfield_for_foreignkey(db_field, request=request, **kwargs)

        # def has_add_permission(self, request):
        #     return False

        # def has_delete_permission(self, request, obj=None):
        #     return False

    def has_add_permission(self, request):
        return False



admin.site.register(ObjectHistoryEntry, ObjectHistoryEntryAdmin)
