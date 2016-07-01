def get_attr_type_model(obj):
    from django.db.models import Model
    from django.contrib.contenttypes.models import ContentType
    from poms.obj_attrs.models import AbstractAttribute

    if isinstance(obj, Model):
        obj = obj.__class__
    ctype = ContentType.objects.get_for_model(obj)
    base_cls = AbstractAttribute

    fields = (f for f in obj._meta.get_fields() if (f.one_to_many or f.one_to_one) and f.auto_created)
    for attr in fields:
        model = getattr(attr, 'related_model', None)
        if model and issubclass(model, base_cls):
            fk = model._meta.get_field('content_object')
            if ctype == ContentType.objects.get_for_model(fk.rel.to):
                return model._meta.get_field('attribute_type').related_model
    return None


def get_attr_model(obj):
    from django.db.models import Model
    from django.contrib.contenttypes.models import ContentType
    from poms.obj_attrs.models import AbstractAttribute

    if isinstance(obj, Model):
        obj = obj.__class__
    ctype = ContentType.objects.get_for_model(obj)
    base_cls = AbstractAttribute

    fields = (f for f in obj._meta.get_fields() if (f.one_to_many or f.one_to_one) and f.auto_created)
    for attr in fields:
        model = getattr(attr, 'related_model', None)
        if model and issubclass(model, base_cls):
            return model
    return None


def get_attr_type_view_perms(model_cls):
    codename_set = ['view_%(model_name)s', 'change_%(model_name)s', 'manage_%(model_name)s']
    kwargs = {
        'app_label': model_cls._meta.app_label,
        'model_name': model_cls._meta.model_name
    }
    return {perm % kwargs for perm in codename_set}
