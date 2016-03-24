from __future__ import unicode_literals

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class UsersConfig(AppConfig):
    name = 'poms.users'
    verbose_name = _('Poms users')

    def ready(self):
        # noinspection PyUnresolvedReferences
        import poms.users.signals

