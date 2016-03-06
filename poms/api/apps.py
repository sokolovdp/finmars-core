from __future__ import unicode_literals

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class ApiConfig(AppConfig):
    name = 'poms.api'
    # label = 'poms_api'
    verbose_name = _('Rest API')
