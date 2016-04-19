from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q


# def register_model(model):
#     from django.db import models
#     from django.utils.translation import ugettext_lazy as _
#     from poms.obj_perms.models import UserObjectPermissionBase, GroupObjectPermissionBase
#
#     app_module = '%s.models' % model._meta.app_label
#
#     u_name = '%sUserObjectPermission' % model._meta.object_name
#     u_attrs = {
#         '__module__': app_module,
#         'content_object': models.ForeignKey(model, related_name='user_object_permissions'),
#         'Meta': type(str('Meta'), (), {
#             'app_label': model._meta.app_label,
#             'verbose_name': _('%(name)s - user permission') % {
#                 'name': model._meta.verbose_name_plural
#             },
#             'verbose_name_plural': _('%(name)s - user permissions') % {
#                 'name': model._meta.verbose_name_plural
#             },
#         })
#     }
#     u_perms = type(str(u_name), (UserObjectPermissionBase,), u_attrs)
#
#     g_name = '%sGroupObjectPermission' % model._meta.object_name
#     g_attrs = {
#         '__module__': app_module,
#         'content_object': models.ForeignKey(model, related_name='group_object_permissions'),
#         'Meta': type(str('Meta'), (), {
#             'app_label': model._meta.app_label,
#             'verbose_name': _('%(name)s - group permission') % {
#                 'name': model._meta.verbose_name_plural
#             },
#             'verbose_name_plural': _('%(name)s - group permissions') % {
#                 'name': model._meta.verbose_name_plural
#             },
#         })
#     }
#     g_perms = type(str(g_name), (GroupObjectPermissionBase,), g_attrs)
#
#     from poms.obj_perms.models import UserObjectPermission, GroupObjectPermission
#     GenericRelation(UserObjectPermission).contribute_to_class(model, 'generic_user_object_permissions')
#     GenericRelation(GroupObjectPermission).contribute_to_class(model, 'generic_user_object_permissions')
#
#     return u_perms, g_perms


# def register_admin(*args):
#     from django.contrib import admin
#     from poms.obj_perms.models import UserObjectPermissionBase, GroupObjectPermissionBase
#     from poms.obj_perms.admin import UserObjectPermissionAdmin, GroupObjectPermissionAdmin
#
#     for model in args:
#         fields = (f for f in model._meta.get_fields() if (f.one_to_many or f.one_to_one) and f.auto_created)
#         for attr in fields:
#             model = getattr(attr, 'related_model', None)
#             if model and issubclass(model, UserObjectPermissionBase):
#                 admin.site.register(model, UserObjectPermissionAdmin)
#             elif model and issubclass(model, GroupObjectPermissionBase):
#                 admin.site.register(model, GroupObjectPermissionAdmin)


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
    from poms.obj_perms.models import UserObjectPermissionBase
    return get_obj_perms_model(obj, UserObjectPermissionBase)


def get_group_obj_perms_model(obj):
    from poms.obj_perms.models import GroupObjectPermissionBase
    return get_obj_perms_model(obj, GroupObjectPermissionBase)


def obj_perms_filter_objects(member, perms, queryset, model_cls=None):
    model = model_cls or queryset.model
    user_lookup_name, user_obj_perms_model = get_user_obj_perms_model(model)
    group_lookup_name, group_obj_perms_model = get_group_obj_perms_model(model)
    ctype = ContentType.objects.get_for_model(model)

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
            lookups.append('%s__member' % user_lookup_name)
            lookups.append('%s__permission' % user_lookup_name)
            lookups.append('%s__permission__content_type' % user_lookup_name)
        if group_lookup_name:
            lookups.append(group_lookup_name)
            lookups.append('%s__group' % group_lookup_name)
            lookups.append('%s__permission' % group_lookup_name)
            lookups.append('%s__permission__content_type' % group_lookup_name)
        if lookups:
            queryset = queryset.prefetch_related(*lookups)

        return queryset
    else:
        return queryset.none()


def get_granted_permissions(member, obj):
    model = obj
    user_lookup_name, user_obj_perms_model = get_user_obj_perms_model(model)
    group_lookup_name, group_obj_perms_model = get_group_obj_perms_model(model)

    obj_perms = set()
    if user_lookup_name:
        user_obj_perms = getattr(obj, user_lookup_name)
        for po in user_obj_perms.all():
            if po.member_id == member.id:
                obj_perms.add(po.permission.codename)

    if group_lookup_name:
        group_obj_perms = getattr(obj, group_lookup_name)
        for po in group_obj_perms.all():
            if po.group in member.groups.all():
                obj_perms.add(po.permission.codename)

    return obj_perms


def assign_perms_to_new_obj(obj, owner, owner_perms, members=None, groups=None, perms=None):
    ctype = ContentType.objects.get_for_model(obj)
    permissions = list(Permission.objects.filter(content_type=ctype))

    user_lookup_name, user_obj_perms_model = get_user_obj_perms_model(obj)
    group_lookup_name, group_obj_perms_model = get_group_obj_perms_model(obj)

    user_perms = []
    group_perms = []

    for p in permissions:
        if owner_perms:
            if p.codename in owner_perms:
                user_perms.append(
                    user_obj_perms_model(content_object=obj, member=owner, permission=p)
                )
        else:
            user_perms.append(
                user_obj_perms_model(content_object=obj, member=owner, permission=p)
            )

    if members:
        for m in members:
            if m.id == owner.id:
                continue
            for p in permissions:
                if p.codename in perms:
                    user_perms.append(
                        user_obj_perms_model(content_object=obj, member=m, permission=p)
                    )

    if groups:
        for g in groups:
            for p in permissions:
                if p.codename in perms:
                    group_perms.append(
                        group_obj_perms_model(content_object=obj, group=g, permission=p)
                    )

    if user_perms:
        user_obj_perms_model.objects.bulk_create(user_perms)
    if group_perms:
        group_obj_perms_model.objects.bulk_create(group_perms)


def assign_perms(obj, members=None, groups=None, perms=None):
    ctype = ContentType.objects.get_for_model(obj)
    permissions = list(Permission.objects.filter(content_type=ctype))

    user_lookup_name, user_obj_perms_model = get_user_obj_perms_model(obj)
    group_lookup_name, group_obj_perms_model = get_group_obj_perms_model(obj)

    if members:
        user_perms = []
        user_obj_perms_model.objects.filter(content_object=obj, member__in=members).delete()
        for m in members:
            for p in permissions:
                if p.codename in perms:
                    user_perms.append(
                        user_obj_perms_model(content_object=obj, member=m, permission=p)
                    )
        if user_perms:
            user_obj_perms_model.objects.bulk_create(user_perms)

    if groups:
        group_perms = []
        group_obj_perms_model.objects.filter(content_object=obj, group__in=groups).delete()
        for g in groups:
            for p in permissions:
                if p.codename in perms:
                    group_perms.append(
                        group_obj_perms_model(content_object=obj, group=g, permission=p)
                    )
        if group_perms:
            group_obj_perms_model.objects.bulk_create(group_perms)

# def obj_perms_filter_objects(member, perms, queryset, model_cls=None):
#     from poms.obj_perms.models import UserObjectPermission, GroupObjectPermission
#     model = model_cls or queryset.model
#     ctype = ContentType.objects.get_for_model(model)
#
#     codenames = set()
#     for perm in perms:
#         if '.' in perm:
#             app_label, codename = perm.split('.', 1)
#             if app_label != ctype.app_label:
#                 raise ValueError('Invalid perm %s ' % perm)
#         else:
#             codename = perm
#         codenames.add(codename)
#
#     u_pemrs = Q(pk__in=UserObjectPermission.objects.filter(
#         member=member, content_type=ctype, permission__content_type=ctype, permission__codename__in=codenames
#     ).values_list('object_id', flat=True))
#     g_pemrs = Q(pk__in=GroupObjectPermission.objects.filter(
#         group__in=member.groups.all(), content_type=ctype, permission__content_type=ctype,
#         permission__codename__in=codenames
#     ).values_list('object_id', flat=True))
#
#     queryset = queryset.filter(u_pemrs | g_pemrs)
#
#     queryset = queryset.prefetch_related(
#         Prefetch(
#             'user_object_permissions',
#             queryset=UserObjectPermission.objects.filter(member=member, content_type=ctype)
#         )
#     )
#
#     return queryset
#
#
# def get_granted_permissions(member, obj):
#     from poms.obj_perms.models import UserObjectPermission, GroupObjectPermission
#     ctype = ContentType.objects.get_for_model(obj)
#
#     obj_perms = set()
#     for po in UserObjectPermission.objects.prefetch_related('permission', 'permission__content_type'). \
#             filter(member=member, content_type=ctype, object_id=obj.id).all():
#         obj_perms.add(po.permission.codename)
#
#     for po in GroupObjectPermission.objects.prefetch_related('permission', 'permission__content_type'). \
#             filter(group__in=member.groups.all(), content_type=ctype, object_id=obj.id).all():
#         obj_perms.add(po.permission.codename)
#
#     return obj_perms
#
#
# def assign_perms_to_new_obj(obj, owner, owner_perms, members, groups, perms):
#     from poms.obj_perms.models import UserObjectPermission, GroupObjectPermission
#     ctype = ContentType.objects.get_for_model(obj)
#     permissions = list(Permission.objects.filter(content_type=ctype))
#
#     user_perms = []
#     group_perms = []
#
#     for p in permissions:
#         if owner_perms:
#             if p.codename in owner_perms:
#                 user_perms.append(
#                     UserObjectPermission(content_object=obj, member=owner, permission=p)
#                 )
#         else:
#             user_perms.append(
#                 UserObjectPermission(content_object=obj, member=owner, permission=p)
#             )
#
#     if members:
#         for m in members:
#             if m.id == owner.id:
#                 continue
#             for p in permissions:
#                 if p.codename in perms:
#                     user_perms.append(
#                         UserObjectPermission(content_object=obj, member=m, permission=p)
#                     )
#
#     if groups:
#         for g in groups:
#             for p in permissions:
#                 if p.codename in perms:
#                     group_perms.append(
#                         GroupObjectPermission(content_object=obj, group=g, permission=p)
#                     )
#
#     if user_perms:
#         UserObjectPermission.objects.bulk_create(user_perms)
#     if group_perms:
#         GroupObjectPermission.objects.bulk_create(group_perms)


# def get_perms(ctype, perms):
#     if perms:
#         if isinstance(perms[0], Permission):
#             return perms
#         return list(Permission.objects.filter(content_type=ctype, codename__in=perms))
#     return None
#
#
# def assign_member_perm(obj, members, perms):
#     ctype = ContentType.objects.get_for_model(obj)
#     user_lookup_name, user_obj_perms_model = get_user_obj_perms_model(obj)
#
#     user_obj_perms_model.objects.filter(member__in=members).delete()
#     if perms:
#         perms = get_perms(ctype, perms)
#         user_perms = []
#         for m in members:
#             for p in perms:
#                 user_perms.append(
#                     user_obj_perms_model(content_object=obj, member=m, permission=p)
#                 )
#         user_obj_perms_model.objects.bulk_create(user_perms)
#
#
# def assign_group_perm(obj, groups, perms):
#     ctype = ContentType.objects.get_for_model(obj)
#     group_lookup_name, group_obj_perms_model = get_group_obj_perms_model(obj)
#
#     group_obj_perms_model.objects.filter(group__in=groups).delete()
#     if perms:
#         perms = get_perms(ctype, perms)
#         group_perms = []
#         for g in groups:
#             for p in perms:
#                 group_perms.append(
#                     group_obj_perms_model(content_object=obj, group=g, permission=p)
#                 )
#         group_obj_perms_model.objects.bulk_create(group_perms)
