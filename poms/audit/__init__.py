from __future__ import unicode_literals

default_app_config = 'poms.audit.apps.AuditConfig'


def register(model, **kwargs):
    from reversion import revisions as reversion
    reversion.register(model, **kwargs)
