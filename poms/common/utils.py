def db_class_check_data(model, verbosity, using):
    from django.db import IntegrityError

    exists = set(model.objects.using(using).values_list('pk', flat=True))
    if verbosity >= 2:
        print('existed transaction classes -> %s' % exists)
    for id, name in model.CLASSES:
        if id not in exists:
            if verbosity >= 2:
                print('create %s class -> %s:%s' % (model._meta.verbose_name, id, name))
            try:
                model.objects.using(using).create(pk=id, system_code=name, name=name, description=name)
            except IntegrityError:
                pass


def date_now():
    from django.utils import timezone
    return timezone.now().date()
