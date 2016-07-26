from __future__ import unicode_literals, print_function

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class IntegrationsConfig(AppConfig):
    name = 'poms.integrations'
    verbose_name = _('Integrations')
