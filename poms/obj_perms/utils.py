import six
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils.functional import SimpleLazyObject


def get_rel_model(obj, attr_name, base_cls):
    from django.db.models import Model

    if isinstance(obj, Model):
        obj = obj.__class__
    from django.contrib.contenttypes.models import ContentType
    ctype = ContentType.objects.get_for_model(obj)

    fields = (f for f in obj._meta.get_fields() if (f.one_to_many or f.one_to_one) and f.auto_created)
    for attr in fields:
        model = getattr(attr, 'related_model', None)
        if model and issubclass(model, base_cls):
            fk = model._meta.get_field(attr_name)
            if ctype == ContentType.objects.get_for_model(fk.rel.to):
                return attr.name, model
    return None, None


def get_obj_perms_model(obj, base_cls):
    # from django.db.models import Model
    #
    # if isinstance(obj, Model):
    #     obj = obj.__class__
    # from django.contrib.contenttypes.models import ContentType
    # ctype = ContentType.objects.get_for_model(obj)
    #
    # fields = (f for f in obj._meta.get_fields() if (f.one_to_many or f.one_to_one) and f.auto_created)
    # for attr in fields:
    #     model = getattr(attr, 'related_model', None)
    #     if model and issubclass(model, base_cls):
    #         fk = model._meta.get_field('content_object')
    #         if ctype == ContentType.objects.get_for_model(fk.rel.to):
    #             return attr.name, model
    # return None, None
    return get_rel_model(obj, 'content_object', base_cls)


def get_user_obj_perms_model(obj):
    from poms.obj_perms.models import AbstractUserObjectPermission
    return get_obj_perms_model(obj, AbstractUserObjectPermission)


def get_group_obj_perms_model(obj):
    from poms.obj_perms.models import AbstractGroupObjectPermission
    return get_obj_perms_model(obj, AbstractGroupObjectPermission)


def obj_perms_filter_objects(member, perms, queryset, model_cls=None, prefetch=True):
    if member.is_superuser:
        return queryset

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

        if prefetch:
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


def obj_perms_filter_objects_for_view(member, queryset, model=None, prefetch=True):
    model = model or queryset.model
    perms = get_view_perms(model)
    return obj_perms_filter_objects(member, perms, queryset, prefetch=prefetch)


def obj_perms_filter_object_list(member, perms, objs):
    if member.is_superuser or not objs:
        return objs
    if not isinstance(perms, set):
        perms = set(perms)
    return [obj for obj in objs if has_perms(member, obj, perms)]


def obj_perms_filter_object_list_for_view(member, objs, model=None):
    if not objs:
        return objs
    model = model or objs[0]
    perms = get_view_perms(model)
    return obj_perms_filter_object_list(member, perms, objs)


def get_granted_permissions(member, obj):
    if member.is_superuser:
        return get_all_perms(obj)
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
        groups_id = [g.id for g in member.groups.all()]
        group_obj_perms = getattr(obj, group_lookup_name)
        for po in group_obj_perms.all():
            if po.group_id in groups_id:
                obj_perms.add(po.permission.codename)

    return list(obj_perms)


def assign_perms(obj, members=None, groups=None, perms=None):
    # ctype = ContentType.objects.get_for_model(obj)
    # permissions = list(Permission.objects.filter(content_type=ctype))
    #
    # user_lookup_name, user_obj_perms_model = get_user_obj_perms_model(obj)
    # group_lookup_name, group_obj_perms_model = get_group_obj_perms_model(obj)
    #
    # if members and user_obj_perms_model:
    #     user_perms = []
    #     for m in members:
    #         for p in permissions:
    #             if p.codename in perms:
    #                 user_perms.append(
    #                     user_obj_perms_model(content_object=obj, member=m, permission=p)
    #                 )
    #     getattr(obj, user_lookup_name).filter(member__in=members).delete()
    #     if user_perms:
    #         user_obj_perms_model.objects.bulk_create(user_perms)
    #
    # if groups:
    #     group_perms = []
    #     for g in groups:
    #         for p in permissions:
    #             if p.codename in perms:
    #                 group_perms.append(
    #                     group_obj_perms_model(content_object=obj, group=g, permission=p)
    #                 )
    #     getattr(obj, group_lookup_name).filter(group__in=groups).delete()
    #     if group_perms:
    #         group_obj_perms_model.objects.bulk_create(group_perms)
    members = members or []
    groups = groups or []
    user_perms = []
    group_perms = []
    for p in perms:
        for m in members:
            user_perms.append({'member': m, 'permission': p})
        for g in groups:
            group_perms.append({'group': g, 'permission': p})
    assign_perms2(obj, user_perms=user_perms, group_perms=group_perms)


def assign_perms2(obj, user_perms=None, group_perms=None):
    ctype = ContentType.objects.get_for_model(obj)
    perms_map = SimpleLazyObject(lambda: {p.codename: p for p in Permission.objects.filter(content_type=ctype)})

    def rebuild_perms(src):
        dst = []
        for p in src:
            p = p.copy()
            if isinstance(p['permission'], six.string_types):
                p['permission'] = perms_map[p['permission']]
            dst.append(p)
        return dst

    user_lookup_name, user_obj_perms_model = get_user_obj_perms_model(obj)
    group_lookup_name, group_obj_perms_model = get_group_obj_perms_model(obj)

    if user_perms is not None and user_obj_perms_model:
        user_perms = rebuild_perms(user_perms)

        member_map = {m['member'].id: m['member'] for m in user_perms}
        perms_map = {m['permission'].codename: m['permission'] for m in user_perms}
        pcur = {(p.member_id, p.permission.codename) for p in getattr(obj, user_lookup_name).all()}
        pnew = {(p['member'].id, p['permission'].codename) for p in user_perms}

        pdelete = pcur - pnew
        if pdelete:
            for member_id, permission in pdelete:
                getattr(obj, user_lookup_name).filter(member=member_id, permission__codename=permission).delete()

        padd = pnew - pcur
        if padd:
            for member_id, permission in padd:
                user_obj_perms_model(content_object=obj,
                                     member=member_map[member_id],
                                     permission=perms_map[permission]).save()

    if group_perms is not None and group_lookup_name:
        group_perms = rebuild_perms(group_perms)
        # getattr(obj, group_lookup_name).all().delete()
        # group_obj_perms_model.objects.bulk_create([group_obj_perms_model(content_object=obj, group=p['group'],
        #                                                                  permission=p['permission'])
        #                                            for p in group_perms])


        group_map = {m['group'].id: m['group'] for m in group_perms}
        perms_map = {m['permission'].codename: m['permission'] for m in group_perms}
        pcur = {(p.group_id, p.permission.codename) for p in getattr(obj, group_lookup_name).all()}
        pnew = {(p['group'].id, p['permission'].codename) for p in group_perms}

        pdelete = pcur - pnew
        if pdelete:
            for group_id, permission in pdelete:
                getattr(obj, group_lookup_name).filter(group=group_id, permission__codename=permission).delete()

        padd = pnew - pcur
        if padd:
            for group_id, permission in padd:
                group_obj_perms_model(content_object=obj,
                                      group=group_map[group_id],
                                      permission=perms_map[permission]).save()


# def _assign_perms(obj, perms_lookup_name, perms_model, member_or_group_lookup_name, perm_list):
#     obj_perms_qs = getattr(obj, perms_lookup_name)
#
#     cur_perms = {(getattr(p, member_or_group_lookup_name), getattr(p, 'permission')): p for p in obj_perms_qs.all()}
#     new_perms = {(p[member_or_group_lookup_name], p['permission']): p for p in perm_list}
#
#     for k, v in six.iteritems(new_perms):
#         if k not in cur_perms:
#             # obj_perms_qs.add(perms_model(**{
#             #     member_or_group_lookup_name: k[0],
#             #     'permission': k[1]
#             # }))
#             obj_perms_qs.create(**{
#                 member_or_group_lookup_name: k[0],
#                 'permission': k[1]
#             })
#
#     for k, v in six.iteritems(cur_perms):
#         if k not in new_perms:
#             # obj_perms_qs.remove(v)
#             obj_perms_qs.filter(**{
#                 member_or_group_lookup_name: k[0],
#                 'permission': k[1]
#             }).delete()


# def assign_perms_from_list(obj, user_object_permissions=None, group_object_permissions=None):
#     user_lookup_name, user_obj_perms_model = get_user_obj_perms_model(obj)
#     group_lookup_name, group_obj_perms_model = get_group_obj_perms_model(obj)
#
#     if user_object_permissions is not None and user_obj_perms_model:
#         _assign_perms(obj, user_lookup_name, user_obj_perms_model, 'member', user_object_permissions)
#
#     if group_object_permissions is not None:
#         _assign_perms(obj, group_lookup_name, group_obj_perms_model, 'group', group_object_permissions)


def get_perms_codename(model, actions):
    params = {
        'action': None,
        'app_label': model._meta.app_label,
        'model_name': model._meta.model_name
    }
    ret = []
    for action in actions:
        params['action'] = action
        ret.append('%(action)s_%(model_name)s' % params)
    return ret


def get_view_perms(model):
    return get_perms_codename(model, ['change', 'view'])


def get_manage_perms(model):
    return get_perms_codename(model, ['manage'])


def get_all_perms(model):
    return get_perms_codename(model, ['change', 'delete', 'view'])


# def get_default_owner_permissions(instance):
#     # view_perms = get_perms_codename(instance, ['change', 'view', 'delete'])
#     # ctype = ContentType.objects.get_for_model(instance)
#     # return [p for p in Permission.objects.filter(content_type=ctype) if p.codename in view_perms]
#     return get_perms_codename(instance, ['change', 'view', 'delete'])


def has_perms(member, obj, perms):
    if member.is_superuser:
        return True
    obj_perms = get_granted_permissions(member, obj)
    return bool(set(perms) & set(obj_perms))


def has_perm(member, obj, perm):
    if member.is_superuser:
        return True
    obj_perms = get_granted_permissions(member, obj)
    return perm in obj_perms


def has_view_perms(member, obj):
    if member.is_superuser:
        return True
    perms = get_view_perms(obj)
    return has_perms(member, obj, perms)


def has_manage_perm(member, obj):
    if member.is_superuser:
        return True
    perms = get_manage_perms(obj)
    return has_perms(member, obj, perms)


_perms_lookups = [
    'user_object_permissions',
    'user_object_permissions__permission',
    'group_object_permissions',
    'group_object_permissions__permission',
]


def obj_perms_prefetch(queryset, my=True, lookups_related=None):
    # return queryset.prefetch_related(
    #     'user_object_permissions', 'user_object_permissions__permission',
    #     'group_object_permissions', 'group_object_permissions__permission',
    # )
    lookups = []
    if my:
        lookups += _perms_lookups
    if lookups_related:
        for name in lookups_related:
            # lookups.append('%s__user_object_permissions' % name)
            # # lookups.append('%s__user_object_permissions_member' % name)
            # lookups.append('%s__user_object_permissions__permission' % name)
            # lookups.append('%s__group_object_permissions' % name)
            # # lookups.append('%s__group_object_permissions__group' % name)
            # lookups.append('%s__group_object_permissions__permission' % name)
            for lookup in _perms_lookups:
                lookups.append('%s__%s' % (name, lookup))
    return queryset.prefetch_related(*lookups)
