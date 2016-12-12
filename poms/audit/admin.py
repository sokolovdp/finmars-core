from __future__ import unicode_literals

from django.contrib import admin

from poms.audit.models import AuthLogEntry, ObjectHistory4Entry
from poms.common.admin import AbstractModelAdmin


class AuthLogEntryAdmin(admin.ModelAdmin):
    model = AuthLogEntry
    list_display = ['id', 'user', 'date', 'is_success', 'user_ip', 'human_user_agent']
    list_select_related = ['user']
    list_filter = ['is_success', 'date']
    ordering = ['-date']
    date_hierarchy = 'date'
    search_fields = ['id', 'user__username']
    fields = ['id', 'date', 'user', 'is_success', 'user_ip', 'user_agent']
    readonly_fields = ['id', 'date', 'is_success', 'user', 'user_ip', 'user_agent', ]

    def has_add_permission(self, request):
        return False


admin.site.register(AuthLogEntry, AuthLogEntryAdmin)


class ObjectHistory4EntryAdmin(AbstractModelAdmin):
    model = ObjectHistory4Entry
    master_user_path = 'master_user'
    list_display = ['id', 'master_user', 'member', 'created', 'group_id',
                    'actor_content_type', 'actor_object_repr',
                    'action_flag',
                    'content_type', 'object_repr',
                    'field_name', 'value', 'old_value']
    list_filter = ['created', 'action_flag', 'actor_content_type']
    ordering = ['-created']
    date_hierarchy = 'created'
    list_select_related = ['master_user', 'member', 'actor_content_type', 'content_type', 'value_content_type',
                           'old_value_content_type']
    raw_id_fields = ['master_user', 'member']
    search_fields = ['group_id', 'actor_object_repr', 'object_repr', 'field_name', 'value', 'old_value']

    readonly_fields = [
        'id', 'master_user', 'member',
        'group_id', 'created',
        'actor_content_type', 'actor_object_id', 'actor_content_object', 'actor_object_repr',
        'action_flag',
        'content_type', 'object_id', 'content_object', 'object_repr',
        'field_name',
        'value', 'value_content_type', 'value_object_id', 'value_content_object',
        'old_value', 'old_value_content_type', 'old_value_object_id', 'old_value_content_object',
    ]

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'content_type':
            qs = kwargs.get('queryset', db_field.remote_field.model.objects)
            kwargs['queryset'] = qs.order_by('model')
        return super(ObjectHistory4EntryAdmin, self).formfield_for_foreignkey(db_field, request=request, **kwargs)

    def has_add_permission(self, request):
        return False

    def save_model(self, request, obj, form, change):
        pass


admin.site.register(ObjectHistory4Entry, ObjectHistory4EntryAdmin)
