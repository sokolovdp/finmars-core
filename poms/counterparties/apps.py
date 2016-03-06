from __future__ import unicode_literals

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class CounterpartiesConfig(AppConfig):
    name = 'poms.counterparties'
    # label = 'poms'
    verbose_name = _('Counterparties')
