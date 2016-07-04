from django.contrib import admin
from django.contrib.contenttypes.models import ContentType

from poms.obj_perms.models import AbstractGroupObjectPermission, AbstractUserObjectPermission
from poms.obj_perms.utils import get_user_obj_perms_model, get_group_obj_perms_model


class AbstractObjectPermissionAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'permission':
            qs = kwargs.get('queryset', db_field.remote_field.model.objects)
            obj_field = self.model._meta.get_field('content_object')
            obj_ctype = ContentType.objects.get_for_model(obj_field.rel.to)
            kwargs['queryset'] = qs.select_related('content_type').filter(content_type=obj_ctype)
            # kwargs['queryset'] = qs.select_related('content_type')
        return super(AbstractObjectPermissionAdmin, self).formfield_for_foreignkey(db_field, request=request, **kwargs)


class UserObjectPermissionAdmin(AbstractObjectPermissionAdmin):
    list_display = ['id', 'member', 'content_object', 'permission', ]
    search_fields = ['content_object__id', 'member__id', 'member__user__username']
    list_select_related = ['member', 'content_object', 'permission', 'permission__content_type']
    fields = ['member', 'content_object', 'permission']
    raw_id_fields = ['member', 'content_object']
    save_as = True
    # list_filter = ['permission']


class GroupObjectPermissionAdmin(AbstractObjectPermissionAdmin):
    list_display = ['id', 'group', 'content_object', 'permission', ]
    search_fields = ['content_object__id', 'group__id', 'group__name']
    list_select_related = ['group', 'content_object', 'permission', 'permission__content_type']
    fields = ['group', 'content_object', 'permission']
    raw_id_fields = ['group', 'content_object']
    save_as = True
    # list_filter = ['permission']


class AbstractObjectPermissionInline(admin.TabularInline):
    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'permission':
            qs = kwargs.get('queryset', db_field.remote_field.model.objects)
            obj_field = self.model._meta.get_field('content_object')
            obj_ctype = ContentType.objects.get_for_model(obj_field.rel.to)
            kwargs['queryset'] = qs.select_related('content_type').filter(content_type=obj_ctype)
            # kwargs['queryset'] = qs.select_related('content_type')
        return super(AbstractObjectPermissionInline, self).formfield_for_foreignkey(db_field, request=request, **kwargs)


class UserObjectPermissionInline(AbstractObjectPermissionInline):
    fields = ['member', 'permission']
    raw_id_fields = ['member', 'content_object']
    model = AbstractUserObjectPermission
    extra = 0

    def __init__(self, parent_model, *args, **kwargs):
        _, self.model = get_user_obj_perms_model(parent_model)
        super(UserObjectPermissionInline, self).__init__(parent_model, *args, **kwargs)


class GroupObjectPermissionInline(AbstractObjectPermissionInline):
    fields = ['group', 'permission']
    raw_id_fields = ['group', 'content_object']
    model = AbstractGroupObjectPermission
    extra = 0

    def __init__(self, parent_model, *args, **kwargs):
        _, self.model = get_group_obj_perms_model(parent_model)
        super(GroupObjectPermissionInline, self).__init__(parent_model, *args, **kwargs)

# class GenericObjectPermissionAdmin(admin.ModelAdmin):
#     list_filter = ['content_type']
#     save_as = True
#     readonly_fields = ('content_object',)
#
#     def get_queryset(self, request):
#         qs = super(GenericObjectPermissionAdmin, self).get_queryset(request)
#         return qs.prefetch_related('content_object')
#
#     def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
#         if db_field.name == 'permission':
#             qs = kwargs.get('queryset', db_field.remote_field.model.objects)
#             kwargs['queryset'] = qs.select_related('content_type')
#         return super(GenericObjectPermissionAdmin, self).formfield_for_foreignkey(db_field, request=request, **kwargs)
#
#
# class GenericUserObjectPermissionAdmin(GenericObjectPermissionAdmin):
#     raw_id_fields = ['member']
#     list_display = ['id', 'member', 'permission', 'content_type', 'object_id', 'content_object']
#     fields = ('member', ('content_type', 'object_id'), 'content_object', 'permission')
#
#
# class GenericGroupObjectPermissionAdmin(GenericObjectPermissionAdmin):
#     raw_id_fields = ['group']
#     list_display = ['id', 'group', 'permission', 'content_type', 'object_id', 'content_object']
#     fields = ('group', ('content_type', 'object_id'), 'content_object', 'permission')


# admin.site.register(UserObjectPermission, GenericUserObjectPermissionAdmin)
# admin.site.register(GroupObjectPermission, GenericGroupObjectPermissionAdmin)
