from __future__ import unicode_literals

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class ObjPermsConfig(AppConfig):
    name = 'poms.obj_perms'
    verbose_name = _('Object permissions')
