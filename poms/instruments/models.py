from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeForeignKey, TreeManyToManyField
from mptt.models import MPTTModel

from poms import audit
from poms.currencies.models import Currency
from poms.users.models import MasterUser


@python_2_unicode_compatible
class InstrumentClassifier(MPTTModel):
    master_user = models.ForeignKey(MasterUser, related_name='instrument_classifiers', verbose_name=_('master user'))
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)
    user_code = models.CharField(max_length=25, null=True, blank=True)
    name = models.CharField(max_length=255, verbose_name=_('name'))
    short_name = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('short name'))
    notes = models.TextField(null=True, blank=True)

    class MPTTMeta:
        order_insertion_by = ['master_user', 'name']

    class Meta:
        verbose_name = _('instrument classifier')
        verbose_name_plural = _('instrument classifiers')
        unique_together = [
            ['master_user', 'user_code']
        ]

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Instrument(models.Model):
    master_user = models.ForeignKey(MasterUser, related_name='instruments', verbose_name=_('master user'))
    user_code = models.CharField(max_length=25, null=True, blank=True)
    name = models.CharField(max_length=255, verbose_name=_('name'))
    short_name = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('short name'))
    notes = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    pricing_currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    price_multiplier = models.FloatField(default=1.)
    accrued_currency = models.ForeignKey(Currency, null=True, blank=True, related_name='instruments_accrued',
                                         on_delete=models.PROTECT)
    accrued_multiplier = models.FloatField(default=1.)
    classifiers = TreeManyToManyField(InstrumentClassifier, blank=True)

    class Meta:
        verbose_name = _('instrument')
        verbose_name_plural = _('instruments')
        unique_together = [
            ['master_user', 'user_code']
        ]

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class PriceHistory(models.Model):
    instrument = models.ForeignKey(Instrument, related_name='prices')
    date = models.DateField(null=False, blank=False, db_index=True, default=timezone.now)
    principal_price = models.FloatField(default=0.0)
    accrued_price = models.FloatField(null=True, blank=True)
    factor = models.FloatField(null=True, blank=True)

    # coupon = models.FloatField(null=True, blank=True)
    # delta = models.FloatField(null=True, blank=True)
    class Meta:
        verbose_name = _('price history')
        verbose_name_plural = _('price histories')
        index_together = [
            ['instrument', 'date']
        ]

    def __str__(self):
        return '%s at %s - %s' % (self.instrument, self.date, self.principal_price,)


audit.register(InstrumentClassifier)
audit.register(Instrument)
audit.register(PriceHistory)
