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
    except ZeroDivisionError:
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


def xnpv(rate, values, dates):
    '''Equivalent of Excel's XNPV function.
    https://support.office.com/en-us/article/XNPV-function-1b42bbf6-370f-4532-a0eb-d67c16b664b7

    >>> from datetime import date
    >>> dates = [date(2010, 12, 29), date(2012, 1, 25), date(2012, 3, 8)]
    >>> values = [-10000, 20, 10100]
    >>> xnpv(0.1, values, dates)
    -966.4345...
    '''
    # _l.debug('xnpv > rate=%s', rate)
    try:
        if rate <= -1.0:
            return float('inf')
        d0 = dates[0]  # or min(dates)
        return sum(
            (vi / (1.0 + rate) ** ((di - d0).days / 365.0))
            for vi, di in zip(values, dates)
        )
    finally:
        # _l.debug('xnpv <')
        pass


def xirr(values, dates):
    '''Equivalent of Excel's XIRR function.
    https://support.office.com/en-us/article/XIRR-function-de1242ec-6477-445b-b11b-a303ad9adc9d

    >>> from datetime import date
    >>> dates = [date(2010, 12, 29), date(2012, 1, 25), date(2012, 3, 8)]
    >>> values = [-10000, 20, 10100]
    >>> xirr(values, dates)
    0.0100612...
    '''
    # _l.debug('xirr >')
    try:
        from scipy.optimize import newton, brentq

        # return newton(lambda r: xnpv(r, values, dates), 0.0), \
        #        brentq(lambda r: xnpv(r, values, dates), -1.0, 1e10)
        # return newton(lambda r: xnpv(r, values, dates), 0.0)
        # return brentq(lambda r: xnpv(r, values, dates), -1.0, 1e10)
        try:
            return newton(lambda r: xnpv(r, values, dates), 0.0)
        except RuntimeError:  # Failed to converge?
            return brentq(lambda r: xnpv(r, values, dates), -1.0, 1e10)
    finally:
        # _l.debug('xirr <')
        pass
