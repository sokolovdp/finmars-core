import math

from django.views.generic.dates import timezone_today


def db_class_check_data(model, verbosity, using):
    from django.db import IntegrityError, ProgrammingError

    try:
        exists = set(model.objects.using(using).values_list('pk', flat=True))
    except ProgrammingError:
        return
    if verbosity >= 2:
        print('existed transaction classes -> %s' % exists)
    for id, code, name in model.CLASSES:
        if id not in exists:
            if verbosity >= 2:
                print('create %s class -> %s:%s' % (model._meta.verbose_name, id, name))
            try:
                model.objects.using(using).create(pk=id, system_code=code,
                                                  name_en=name, description_en=name)
            except (IntegrityError, ProgrammingError):
                pass
        else:
            obj = model.objects.using(using).get(pk=id)
            obj.system_code = code
            if not obj.name_en:
                obj.name_en = name
            if not obj.description_en:
                obj.description_en = name
            obj.save()


def date_now():
    return timezone_today()


try:
    isclose = math.isclose
except AttributeError:
    def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
        return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


def safe_div(a, b, default=0.0):
    try:
        return a / b
    except (ZeroDivisionError, TypeError):
        return default


def add_view_and_manage_permissions():
    from django.contrib.contenttypes.models import ContentType
    from django.contrib.auth.models import Permission

    existed = {(p.content_type_id, p.codename) for p in Permission.objects.all()}
    for content_type in ContentType.objects.all():
        codename = "view_%s" % content_type.model
        if (content_type.id, codename) not in existed:
            Permission.objects.update_or_create(
                content_type=content_type, codename=codename,
                defaults={
                    'name': 'Can view %s' % content_type.name
                }
            )

        codename = "manage_%s" % content_type.model
        if (content_type.id, codename) not in existed:
            Permission.objects.update_or_create(
                content_type=content_type, codename=codename,
                defaults={
                    'name': 'Can manage %s' % content_type.name
                }
            )
