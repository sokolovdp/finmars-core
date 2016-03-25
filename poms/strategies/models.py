from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel
from poms.audit import utils as history

from poms.users.models import MasterUser


@python_2_unicode_compatible
class Strategy(MPTTModel):
    master_user = models.ForeignKey(MasterUser, related_name='strategy_classifiers', verbose_name=_('master user'))
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)
    user_code = models.CharField(max_length=25, null=True, blank=True)
    name = models.CharField(max_length=255, verbose_name=_('name'))
    short_name = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('short name'))
    notes = models.TextField(null=True, blank=True)

    class MPTTMeta:
        order_insertion_by = ['master_user', 'name']

    class Meta:
        verbose_name = _('strategy')
        verbose_name_plural = _('strategies')
        unique_together = [
            ['master_user', 'user_code']
        ]

    def __str__(self):
        return self.name


history.register(Strategy)
