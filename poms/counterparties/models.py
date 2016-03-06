from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeForeignKey, TreeManyToManyField
from mptt.models import MPTTModel

from poms.currencies.models import Currency
from poms.portfolios.models import Portfolio
from poms.users.models import MasterUser


@python_2_unicode_compatible
class CounterpartyClassifier(MPTTModel):
    master_user = models.ForeignKey(MasterUser, related_name='counterparty_classifiers', verbose_name=_('master user'))
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)
    name = models.CharField(max_length=255)

    class MPTTMeta:
        order_insertion_by = ['master_user', 'name']

    class Meta:
        verbose_name = _('counterparty classifier')
        verbose_name_plural = _('counterparty classifiers')

    def __str__(self):
        return '%s (%s)' % (self.name, self.master_user.user.username)


@python_2_unicode_compatible
class Counterparty(models.Model):
    master_user = models.ForeignKey(MasterUser, related_name='counterparties', verbose_name=_('master user'))
    user_code = models.CharField(max_length=25, null=True, blank=True)
    name = models.CharField(max_length=255, verbose_name=_('name'))
    short_name = models.CharField(max_length=50, verbose_name=_('short name'))
    # portfolios = models.ManyToManyField(Portfolio, blank=True)
    # settlement_details = models.TextField(null=True, blank=True)
    classifiers = TreeManyToManyField(CounterpartyClassifier, blank=True)

    class Meta:
        verbose_name = _('counterparty')
        verbose_name_plural = _('counterparties')

    def __str__(self):
        return '%s' % self.legal_name


@python_2_unicode_compatible
class Responsible(models.Model):
    master_user = models.ForeignKey(MasterUser, related_name='responsibles', verbose_name=_('master user'))
    user_code = models.CharField(max_length=25, null=True, blank=True)
    name = models.CharField(max_length=255, verbose_name=_('name'))
    short_name = models.CharField(max_length=50, verbose_name=_('short name'))

    class Meta:
        verbose_name = _('responsible')
        verbose_name_plural = _('responsibles')

    def __str__(self):
        return '%s' % self.name
