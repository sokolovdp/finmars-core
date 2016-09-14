from __future__ import unicode_literals

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy


class ReportsConfig(AppConfig):
    name = 'poms.reports'
    # label = 'poms_reports'
    verbose_name = ugettext_lazy('Reports')
