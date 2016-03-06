from __future__ import unicode_literals

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class StrategiesConfig(AppConfig):
    name = 'poms.strategies'
    # label = 'poms'
    verbose_name = _('Strategies')
