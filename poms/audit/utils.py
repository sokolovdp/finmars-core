from __future__ import unicode_literals

from reversion import revisions as reversion
from reversion.errors import RevisionManagementError

from poms.audit.models import ModelProxy


def set_comment_safe(message):
    try:
        comment = reversion.get_comment() or ''
        reversion.set_comment(comment + message)
    except RevisionManagementError:
        pass


def register(model=None):
    reversion.register(model)


def is_historical_proxy(obj):
    return isinstance(obj, ModelProxy)
