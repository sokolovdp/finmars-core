from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from poms.audit import history
from poms.common.models import NamedModel
from poms.users.models import MasterUser


@python_2_unicode_compatible
class Strategy(NamedModel, MPTTModel):
    master_user = models.ForeignKey(MasterUser, related_name='strategy_classifiers', verbose_name=_('master user'))
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)

    class MPTTMeta:
        order_insertion_by = ['master_user', 'name']

    class Meta:
        verbose_name = _('strategy')
        verbose_name_plural = _('strategies')
        unique_together = [
            ['master_user', 'user_code']
        ]
        permissions = [
            ('view_strategy', 'Can view strategy')
        ]

    def __str__(self):
        return self.name


history.register(Strategy)
