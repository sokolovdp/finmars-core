from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeForeignKey, TreeManyToManyField
from mptt.models import MPTTModel

from poms.audit import history
from poms.common.models import NamedModel
from poms.users.models import MasterUser


@python_2_unicode_compatible
class CounterpartyClassifier(NamedModel, MPTTModel):
    master_user = models.ForeignKey(MasterUser, related_name='counterparty_classifiers', verbose_name=_('master user'))
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)

    class MPTTMeta:
        order_insertion_by = ['master_user', 'name']

    class Meta:
        verbose_name = _('counterparty classifier')
        verbose_name_plural = _('counterparty classifiers')
        permissions = [
            ('view_counterpartyclassifier', 'Can view counterparty classifier')
        ]

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Counterparty(NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='counterparties', verbose_name=_('master user'))
    # portfolios = models.ManyToManyField(Portfolio, blank=True)
    # settlement_details = models.TextField(null=True, blank=True)
    classifiers = TreeManyToManyField(CounterpartyClassifier, blank=True)

    class Meta:
        verbose_name = _('counterparty')
        verbose_name_plural = _('counterparties')
        unique_together = [
            ['master_user', 'user_code']
        ]
        permissions = [
            ('view_counterparty', 'Can view counterparty')
        ]

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Responsible(NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='responsibles', verbose_name=_('master user'))

    class Meta:
        verbose_name = _('responsible')
        verbose_name_plural = _('responsibles')
        unique_together = [
            ['master_user', 'user_code']
        ]
        permissions = [
            ('view_responsible', 'Can view responsible')
        ]

    def __str__(self):
        return self.name


history.register(CounterpartyClassifier)
history.register(Counterparty)
history.register(Responsible)
