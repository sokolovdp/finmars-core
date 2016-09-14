from __future__ import unicode_literals

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy


class ObjPermsConfig(AppConfig):
    name = 'poms.obj_perms'
    verbose_name = ugettext_lazy('Object permissions')
