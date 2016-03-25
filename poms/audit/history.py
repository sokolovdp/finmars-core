from __future__ import unicode_literals

from threading import local

from django.utils.decorators import ContextDecorator
from django.utils.encoding import force_text
from django.utils.text import get_text_list
from django.utils.translation import ugettext as _
from reversion import revisions as reversion
from reversion.errors import RevisionManagementError

from poms.audit.models import ModelProxy


_active = local()


def activate():
    _active.value = True


def deactivate():
    if hasattr(_active, "value"):
        del _active.value


def is_active():
    return getattr(_active, "value", False)


class enable(ContextDecorator):
    def __enter__(self):
        activate()

    def __exit__(self, exc_type, exc_value, traceback):
        deactivate()


def is_historical_proxy(obj):
    return isinstance(obj, ModelProxy)


def register(model, **kwargs):
    reversion.register(model, **kwargs)


def add_comment(message):
    try:
        comment = reversion.get_comment() or ''
        reversion.set_comment(comment + message)
    except RevisionManagementError:
        pass


def object_added(obj):
    if is_active():
        message = _('Added %(name)s "%(object)s".') % {
            'name': force_text(obj._meta.verbose_name),
            'object': force_text(obj)
        }
        add_comment(message)


def object_changed(obj, fields):
    if is_active():
        message = _('Changed %(list)s for %(name)s "%(object)s".') % {
            'list': get_text_list(fields, _('and')),
            'name': force_text(obj._meta.verbose_name),
            'object': force_text(obj)
        }
        add_comment(message)


def object_deleted(obj):
    if is_active():
        message = _('Deleted %(name)s "%(object)s".') % {
            'name': force_text(obj._meta.verbose_name),
            'object': force_text(obj)
        }
        add_comment(message)
