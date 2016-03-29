from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model

from poms.users.models import BaseGroupObjectPermission, BaseUserObjectPermission


def get_obj_perms_model(obj, base_cls):
    if isinstance(obj, Model):
        obj = obj.__class__
    ctype = ContentType.objects.get_for_model(obj)

    fields = (f for f in obj._meta.get_fields()
              if (f.one_to_many or f.one_to_one) and f.auto_created)

    for attr in fields:
        model = getattr(attr, 'related_model', None)
        if model and issubclass(model, base_cls):
            fk = model._meta.get_field('content_object')
            if ctype == ContentType.objects.get_for_model(fk.rel.to):
                return model
    return None


def get_user_obj_perms_model(obj):
    return get_obj_perms_model(obj, BaseUserObjectPermission)


def get_group_obj_perms_model(obj):
    return get_obj_perms_model(obj, BaseGroupObjectPermission)


class PomsPermissionBackend(object):
    supports_object_permissions = True

    def authenticate(self, username, password):
        return None

    def _to_perms(self, queryset):
        perms = queryset.select_related('content_type').values_list('content_type__app_label', 'codename').order_by()
        return set("%s.%s" % (ct, name) for ct, name in perms)

    def _get_user_permissions(self, user_obj):
        if hasattr(user_obj, 'current_member'):
            perms = user_obj.current_member.permissions.all()
            return self._to_perms(perms)
        return set()

    def _get_group_permissions(self, user_obj):
        if hasattr(user_obj, 'current_member'):
            perms = Permission.objects.filter(group2__in=user_obj.current_member.groups.all())
            return self._to_perms(perms)
        return set()

    def _get_user_object_permissions(self, user_obj, obj):
        if hasattr(user_obj, 'current_member'):
            model = get_user_obj_perms_model(obj)
            if model:
                related_name = model.permission.field.related_query_name()
                perms = Permission.objects.filter(**{
                    'member': user_obj.current_member,
                    '%s__content_object' % related_name: obj,
                })
                # perms = Permission.objects.filter(member=user_obj.current_member,
                #                                   accountuserobjectpermission__content_object=obj)
                return self._to_perms(perms)
        return set()

    def _get_group_object_permissions(self, user_obj, obj):
        if hasattr(user_obj, 'current_member'):
            model = get_group_obj_perms_model(obj)
            if model:
                related_name = model.permission.field.related_query_name()
                perms = Permission.objects.filter(**{
                    'member': user_obj.current_member,
                    '%s__content_object' % related_name: obj,
                    '%s__group__in' % related_name: user_obj.current_member.groups.all()
                })
                # perms = Permission.objects.filter(member=user_obj.current_member,
                #                                   accountgroupobjectpermission__group__in=user_obj.current_member.groups.all())
                return self._to_perms(perms)
        return set()

    def get_all_permissions(self, user_obj, obj=None):
        if not user_obj.is_active or user_obj.is_anonymous():
            return set()

        if obj is None:
            perms = self._get_user_permissions(user_obj)
            perms.update(self._get_group_permissions(user_obj))
        else:
            perms = self._get_user_object_permissions(user_obj, obj)
            perms.update(self._get_group_object_permissions(user_obj, obj))
        print(user_obj, '->', obj, obj._meta.label if obj else None, '->', perms)
        return perms

    def has_perm(self, user_obj, perm, obj=None):
        if not user_obj.is_active:
            return False
        return perm in self.get_all_permissions(user_obj, obj)
