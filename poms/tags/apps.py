from __future__ import unicode_literals

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class TagsConfig(AppConfig):
    name = 'poms.tags'
    verbose_name = _('Tags')
