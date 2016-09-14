from __future__ import unicode_literals

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy


class UsersConfig(AppConfig):
    name = 'poms.users'
    verbose_name = ugettext_lazy('Poms users')

    def ready(self):
        # noinspection PyUnresolvedReferences
        import poms.users.signals
