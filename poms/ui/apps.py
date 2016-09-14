from django.apps import AppConfig
from django.utils.translation import ugettext_lazy


class UiConfig(AppConfig):
    name = 'poms.ui'
    verbose_name = ugettext_lazy('UI layout')
