from __future__ import unicode_literals

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy


class ApiConfig(AppConfig):
    name = 'poms.api'
    # label = 'poms_api'
    verbose_name = ugettext_lazy('Rest API')
