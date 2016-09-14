from __future__ import unicode_literals

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy


class ObjAttrsConfig(AppConfig):
    name = 'poms.obj_attrs'
    verbose_name = ugettext_lazy('Attributes')
