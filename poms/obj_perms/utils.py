import six
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q


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

    return obj_perms


def get_default_owner_permissions(instance):
    ctype = ContentType.objects.get_for_model(instance)
    return [p for p in Permission.objects.filter(content_type=ctype) if not p.codename.startswith('add_')]


def assign_perms(obj, members=None, groups=None, perms=None):
    ctype = ContentType.objects.get_for_model(obj)
    permissions = list(Permission.objects.filter(content_type=ctype))

    user_lookup_name, user_obj_perms_model = get_user_obj_perms_model(obj)
    group_lookup_name, group_obj_perms_model = get_group_obj_perms_model(obj)

    if members and user_obj_perms_model:
        # user_obj_perms_model.objects.filter(content_object=obj, member__in=members).delete()
        user_obj_perms_qs = getattr(obj, user_lookup_name)
        user_obj_perms_qs.all().delete()
        user_perms = []
        for m in members:
            for p in permissions:
                if p.codename in perms:
                    user_perms.append(
                        user_obj_perms_model(content_object=obj, member=m, permission=p)
                    )
        if user_perms:
            user_obj_perms_model.objects.bulk_create(user_perms)

    if groups:
        # group_obj_perms_model.objects.filter(content_object=obj, group__in=groups).delete()
        group_obj_perms_qs = getattr(obj, group_lookup_name)
        group_obj_perms_qs.all().delete()
        group_perms = []
        for g in groups:
            for p in permissions:
                if p.codename in perms:
                    group_perms.append(
                        group_obj_perms_model(content_object=obj, group=g, permission=p)
                    )
        if group_perms:
            group_obj_perms_model.objects.bulk_create(group_perms)


def _assign_perms(obj, perms_lookup_name, perms_model, member_or_group_lookup_name, perm_list):
    obj_perms_qs = getattr(obj, perms_lookup_name)

    cur_perms = {(getattr(p, member_or_group_lookup_name), getattr(p, 'permission')): p for p in obj_perms_qs.all()}
    new_perms = {(p[member_or_group_lookup_name], p['permission']): p for p in perm_list}

    has_changes = False

    for k, v in six.iteritems(new_perms):
        if k not in cur_perms:
            has_changes = True
            # obj_perms_qs.add(perms_model(**{
            #     member_or_group_lookup_name: k[0],
            #     'permission': k[1]
            # }))
            obj_perms_qs.create(**{
                member_or_group_lookup_name: k[0],
                'permission': k[1]
            })

    for k, v in six.iteritems(cur_perms):
        if k not in new_perms:
            has_changes = True
            # obj_perms_qs.remove(v)
            obj_perms_qs.filter(**{
                member_or_group_lookup_name: k[0],
                'permission': k[1]
            }).delete()

    # TODO: invalidate cache for *_object_permission, how prefetch related?
    if has_changes:
        # need only on add and delete operation
        obj_perms_qs.update()
        # setattr(obj, perms_lookup_name, obj_perms_qs.select_related('permission').all()) # called update :(


def assign_perms_from_list(obj, user_object_permissions=None, group_object_permissions=None):
    user_lookup_name, user_obj_perms_model = get_user_obj_perms_model(obj)
    group_lookup_name, group_obj_perms_model = get_group_obj_perms_model(obj)

    if user_object_permissions is not None and user_obj_perms_model:
        _assign_perms(obj, user_lookup_name, user_obj_perms_model, 'member', user_object_permissions)

    if group_object_permissions is not None:
        _assign_perms(obj, group_lookup_name, group_obj_perms_model, 'group', group_object_permissions)


def get_view_perms(model):
    # codename_set = ['view_%(model_name)s', 'change_%(model_name)s', 'manage_%(model_name)s']
    codename_set = ['change_%(model_name)s', ]
    kwargs = {
        'app_label': model._meta.app_label,
        'model_name': model._meta.model_name
    }
    return {perm % kwargs for perm in codename_set}


def has_perms(member, obj, perms):
    if member.is_superuser:
        return True
    obj_perms = get_granted_permissions(member, obj)
    return perms.issubset(obj_perms)


def has_view_perms(member, obj):
    if member.is_superuser:
        return True
    perms = get_view_perms(obj)
    return has_perms(member, obj, perms)


def perms_prefetch(queryset):
    return queryset.prefetch_related(
        'group_object_permissions',
        'group_object_permissions__permission',
    )
