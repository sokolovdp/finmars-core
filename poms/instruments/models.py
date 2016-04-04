from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeForeignKey, TreeManyToManyField
from mptt.models import MPTTModel

from poms.audit import history
from poms.common.models import NamedModel
from poms.currencies.models import Currency
from poms.users.models import MasterUser


@python_2_unicode_compatible
class InstrumentClassifier(NamedModel, MPTTModel):
    master_user = models.ForeignKey(MasterUser, related_name='instrument_classifiers', verbose_name=_('master user'))
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)

    class MPTTMeta:
        order_insertion_by = ['master_user', 'name']

    class Meta:
        verbose_name = _('instrument classifier')
        verbose_name_plural = _('instrument classifiers')
        unique_together = [
            ['master_user', 'user_code']
        ]
        permissions = [
            ('view_instrumentclassifier', 'Can view instrument classifier')
        ]

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Instrument(NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='instruments', verbose_name=_('master user'))
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
        permissions = [
            ('view_instrument', 'Can view instrument')
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
        permissions = [
            ('view_pricehistory', 'Can view price history')
        ]

    def __str__(self):
        return '%s at %s - %s' % (self.instrument, self.date, self.principal_price,)


history.register(InstrumentClassifier)
history.register(Instrument)
history.register(PriceHistory)
