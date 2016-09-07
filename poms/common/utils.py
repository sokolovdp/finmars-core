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
    # from django.utils import timezone
    # return timezone.now().date()
    return timezone_today()
