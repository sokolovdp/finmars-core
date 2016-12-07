from __future__ import unicode_literals

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy


class HttpSessionsConfig(AppConfig):
    name = 'poms.http_sessions'
    # label = 'poms_sessions'
    verbose_name = ugettext_lazy('Sessions')
