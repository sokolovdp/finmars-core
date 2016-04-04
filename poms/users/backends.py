from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model, Q

from poms.users.models import GroupObjectPermissionBase, UserObjectPermissionBase

_obj_perms_model_cache = {}


def _obj_perms_model_cache_key(obj_ctype, base_cls):
    return obj_ctype, base_cls


def get_obj_perms_model(obj, base_cls):
    if isinstance(obj, Model):
        obj = obj.__class__
    ctype = ContentType.objects.get_for_model(obj)

    key = _obj_perms_model_cache_key(ctype, base_cls)
    if key in _obj_perms_model_cache:
        return _obj_perms_model_cache[key]

    fields = (f for f in obj._meta.get_fields() if (f.one_to_many or f.one_to_one) and f.auto_created)
    for attr in fields:
        model = getattr(attr, 'related_model', None)
        if model and issubclass(model, base_cls):
            fk = model._meta.get_field('content_object')
            if ctype == ContentType.objects.get_for_model(fk.rel.to):
                _obj_perms_model_cache[key] = model
                return model
    _obj_perms_model_cache[key] = None
    return None


def get_user_obj_perms_model(obj):
    return get_obj_perms_model(obj, UserObjectPermissionBase)


def get_group_obj_perms_model(obj):
    return get_obj_perms_model(obj, GroupObjectPermissionBase)


def filter_objects_for_user(user_obj, perms, queryset):
    if not hasattr(user_obj, 'current_member'):
        return queryset.none()

    model = queryset.model
    ctype = ContentType.objects.get_for_model(model)
    user_obj_perms_model = get_user_obj_perms_model(model)
    group_obj_perms_model = get_group_obj_perms_model(model)
    member = user_obj.current_member

    codenames = set()
    for perm in perms:
        if '.' in perm:
            app_label, codename = perm.split('.', 1)
            if app_label != ctype.app_label:
                raise ValueError('Invalid perm %s ' % perm)
        else:
            codename = perm
        codenames.add(codename)

    if codenames and (user_obj_perms_model or group_obj_perms_model):
        f = Q()
        if user_obj_perms_model:
            user_obj_perms_qs = user_obj_perms_model.objects.filter(
                member=member,
                permission__content_type=ctype,
                permission__codename__in=codenames
            )
            f |= Q(pk__in=user_obj_perms_qs.values_list('content_object__id', flat=True))
        if group_obj_perms_model:
            group_obj_perms_qs = group_obj_perms_model.objects.filter(
                group__in=member.groups.all(),
                permission__content_type=ctype,
                permission__codename__in=codenames
            )
            f |= Q(pk__in=group_obj_perms_qs.values_list('content_object__id', flat=True))
        return queryset.filter(f)
    else:
        return queryset.none()


class PomsPermissionBackend(object):
    supports_object_permissions = True

    def authenticate(self, username, password):
        return None

    def _to_perms(self, queryset):
        perms = queryset.values_list('content_type__app_label', 'codename').order_by()
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
                    '%s__member' % related_name: user_obj.current_member,
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
                    '%s__group__in' % related_name: user_obj.current_member.groups.all(),
                    '%s__content_object' % related_name: obj,
                })
                # perms = Permission.objects.filter(member=user_obj.current_member,
                #                                   accountgroupobjectpermission__group__in=user_obj.current_member.groups.all())
                return self._to_perms(perms)
        return set()

    def get_all_permissions(self, user_obj, obj=None):
        if not user_obj.is_active or user_obj.is_anonymous():
            return set()

        if hasattr(user_obj, '_poms_perms_cache'):
            _poms_perms_cache = user_obj._poms_perms_cache
        else:
            _poms_perms_cache = user_obj._poms_perms_cache = {}

        cache_key = 'all' if obj is None else '%s:%s' % (obj._meta.label, obj.pk)
        if cache_key in _poms_perms_cache:
            return _poms_perms_cache[cache_key]

        if obj is None:
            perms = self._get_user_permissions(user_obj)
            perms.update(self._get_group_permissions(user_obj))
        else:
            perms = self._get_user_object_permissions(user_obj, obj)
            perms.update(self._get_group_object_permissions(user_obj, obj))

        _poms_perms_cache[cache_key] = perms.copy()
        return perms

    def has_perm(self, user_obj, perm, obj=None):
        if not user_obj.is_active:
            return False
        return perm in self.get_all_permissions(user_obj, obj)
