from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class UiConfig(AppConfig):
    name = 'poms.ui'
    verbose_name = _('UI layout')
