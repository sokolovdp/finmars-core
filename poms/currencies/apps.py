from __future__ import unicode_literals

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy


class CurrenciesConfig(AppConfig):
    name = 'poms.currencies'
    # label = 'poms_currencies'
    verbose_name = ugettext_lazy('Currencies')
