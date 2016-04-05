def register_model(model):
    from django.db import models
    from django.utils.translation import ugettext_lazy as _
    from poms.users.models import UserObjectPermissionBase, GroupObjectPermissionBase

    app_module = '%s.models' % model._meta.app_label

    u_name = '%sUserObjectPermission' % model._meta.object_name
    u_attrs = {
        '__module__': app_module,
        'content_object': models.ForeignKey(model, related_name='user_object_permissions'),
        'Meta': type(str('Meta'), (), {
            'app_label': model._meta.app_label,
            'verbose_name': _('%(name)s - user permission') % {
                'name': model._meta.verbose_name_plural
            },
            'verbose_name_plural': _('%(name)s - user permissions') % {
                'name': model._meta.verbose_name_plural
            },
        })
    }
    u_perms = type(str(u_name), (UserObjectPermissionBase,), u_attrs)

    g_name = '%sGroupObjectPermission' % model._meta.object_name
    g_attrs = {
        '__module__': app_module,
        'content_object': models.ForeignKey(model, related_name='group_object_permissions'),
        'Meta': type(str('Meta'), (), {
            'app_label': model._meta.app_label,
            'verbose_name': _('%(name)s - group permission') % {
                'name': model._meta.verbose_name_plural
            },
            'verbose_name_plural': _('%(name)s - group permissions') % {
                'name': model._meta.verbose_name_plural
            },
        })
    }
    g_perms = type(str(g_name), (GroupObjectPermissionBase,), g_attrs)
    return u_perms, g_perms


def register_admin(*args):
    from django.contrib import admin
    from poms.users.models import UserObjectPermissionBase, GroupObjectPermissionBase
    from poms.users.admin import UserObjectPermissionAdmin, GroupObjectPermissionAdmin

    for model in args:
        if issubclass(model, UserObjectPermissionBase):
            admin.site.register(model, UserObjectPermissionAdmin)
        elif issubclass(model, GroupObjectPermissionBase):
            admin.site.register(model, GroupObjectPermissionAdmin)


def get_obj_perms_model(obj, base_cls):
    from django.db.models import Model

    if isinstance(obj, Model):
        obj = obj.__class__
    from django.contrib.contenttypes.models import ContentType
    ctype = ContentType.objects.get_for_model(obj)

    fields = (f for f in obj._meta.get_fields() if (f.one_to_many or f.one_to_one) and f.auto_created)
    for attr in fields:
        model = getattr(attr, 'related_model', None)
        if model and issubclass(model, base_cls):
            fk = model._meta.get_field('content_object')
            if ctype == ContentType.objects.get_for_model(fk.rel.to):
                return attr.name, model
    return None, None


def get_user_obj_perms_model(obj):
    from poms.users.obj_perms.models import UserObjectPermissionBase
    return get_obj_perms_model(obj, UserObjectPermissionBase)


def get_group_obj_perms_model(obj):
    from poms.users.obj_perms.models import GroupObjectPermissionBase
    return get_obj_perms_model(obj, GroupObjectPermissionBase)


def filter_objects_for_user(user_obj, perms, queryset):
    from django.contrib.contenttypes.models import ContentType
    from django.db.models import Q

    if not hasattr(user_obj, 'current_member'):
        return queryset.none()
    member = user_obj.current_member

    model = queryset.model
    ctype = ContentType.objects.get_for_model(model)
    user_lookup_name, user_obj_perms_model = get_user_obj_perms_model(model)
    group_lookup_name, group_obj_perms_model = get_group_obj_perms_model(model)

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
        if f:
            queryset = queryset.filter(f)

        lookups = []
        if user_lookup_name:
            lookups.append(user_lookup_name)
            lookups.append('%s__content_type' % user_lookup_name)
        if group_lookup_name:
            lookups.append(group_lookup_name)
            lookups.append('%s__content_type' % group_lookup_name)
        if lookups:
            queryset = queryset.prefetch_related(*lookups)

        return queryset
    else:
        return queryset.none()


def get_granted_permissions(user_obj, obj):
    user_lookup_name, user_obj_perms_model = get_user_obj_perms_model(obj)
    group_lookup_name, group_obj_perms_model = get_group_obj_perms_model(obj)

    user_perms = getattr(obj, user_lookup_name, []) if user_lookup_name else []
    group_perms = getattr(obj, group_lookup_name, []) if group_lookup_name else []

    if not hasattr(user_obj, 'current_member'):
        return []
    member = user_obj.current_member
    groups = {g.id for g in member.groups.all()}

    perms = {'%s.%s' % (p.content_type.app_label, p.code) for p in user_perms if p.member_id == member.id}
    perms.update('%s.%s' % (p.content_type.app_label, p.code) for p in group_perms if p.group_id == groups)
    return perms
