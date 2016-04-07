from django.contrib import admin
from django.contrib.contenttypes.models import ContentType

from poms.obj_perms.models import ThreadUserObjectPermission, ThreadGroupObjectPermission


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


admin.site.register(ThreadUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(ThreadGroupObjectPermission, GroupObjectPermissionAdmin)

