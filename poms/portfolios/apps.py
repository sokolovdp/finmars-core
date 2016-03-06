from __future__ import unicode_literals

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class PortfoliosConfig(AppConfig):
    name = 'poms.portfolios'
    # label = 'poms'
    verbose_name = _('Portfolios')
