from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeForeignKey, TreeManyToManyField
from mptt.models import MPTTModel

from poms.audit import history
from poms.common.models import NamedModel, TagModelBase, ClassModelBase
from poms.currencies.models import Currency
from poms.users.models import MasterUser, AttrBase, AttrValueBase


class InstrumentClass(ClassModelBase):
    GENERAL = 1
    EVENT_AT_MATURITY = 2
    REGULAR_EVENT_AT_MATURITY = 3
    PERPETUAL_REGULAR_EVENT = 4
    CONTRACT_FOR_DIFFERENCE = 5

    CLASSES = (
        (GENERAL, "General Class"),
        (EVENT_AT_MATURITY, "Event at Maturity"),
        (REGULAR_EVENT_AT_MATURITY, "Regular Event with Maturity"),
        (PERPETUAL_REGULAR_EVENT, "Perpetual Regular Event"),
        (CONTRACT_FOR_DIFFERENCE, "Contract for Difference"),
    )

    class Meta:
        verbose_name = _('instrument class')
        verbose_name_plural = _('instrument classes')


class DailyPricingModel(ClassModelBase):
    # TODO: add "values"
    CLASSES = tuple()

    class Meta:
        verbose_name = _('daily pricing model')
        verbose_name_plural = _('daily pricing models')


class AccrualCalculationModel(ClassModelBase):
    # TODO: add "values"
    CLASSES = tuple()

    class Meta:
        verbose_name = _('accrual calculation model')
        verbose_name_plural = _('accrual calculation models')


class PaymentFrequency(ClassModelBase):
    # TODO: add "values"
    CLASSES = tuple()

    class Meta:
        verbose_name = _('payment frequency')
        verbose_name_plural = _('payment frequencies')


class CostMethod(ClassModelBase):
    # TODO: add "values"
    CLASSES = tuple()

    class Meta:
        verbose_name = _('cost method')
        verbose_name_plural = _('cost methods')


class InstrumentTypeTag(TagModelBase):
    master_user = models.ForeignKey(MasterUser, related_name='instrumenttype_tags', verbose_name=_('master user'))

    class Meta:
        verbose_name = _('instrument type tag')
        verbose_name_plural = _('instrument type tags')
        unique_together = [
            ['master_user', 'user_code'],
            ['master_user', 'name'],
        ]
        permissions = [
            ('view_instrumenttypetag', 'Can view instrument type tag')
        ]


@python_2_unicode_compatible
class InstrumentType(NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='instrument_types', verbose_name=_('master user'))
    instrument_class = models.ForeignKey(InstrumentClass, related_name='instrument_types',
                                         verbose_name=_('instrument class'))
    tags = models.ManyToManyField(InstrumentTypeTag, blank=True)

    class Meta:
        verbose_name = _('instrument type')
        verbose_name_plural = _('instrument types')
        unique_together = [
            ['master_user', 'user_code']
        ]
        permissions = [
            ('view_instrumenttype', 'Can view instrument type')
        ]

    def __str__(self):
        return self.name


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


class InstrumentTag(TagModelBase):
    master_user = models.ForeignKey(MasterUser, related_name='instrument_tags', verbose_name=_('master user'))

    class Meta:
        verbose_name = _('instrument tag')
        verbose_name_plural = _('instrument tags')
        unique_together = [
            ['master_user', 'user_code'],
            ['master_user', 'name'],
        ]
        permissions = [
            ('view_instrumenttag', 'Can view instrument tag')
        ]


@python_2_unicode_compatible
class ManualPricingFormula(NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='manual_pricing_formulas', verbose_name=_('master user'))
    expr = models.TextField(default='0.')

    class Meta:
        verbose_name = _('manual pricing formula')
        verbose_name_plural = _('manual pricing formulas')
        unique_together = [
            ['master_user', 'user_code']
        ]
        permissions = [
            ('view_manualpricingformula', 'Can view manual pricing formula')
        ]

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Instrument(NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='instruments', verbose_name=_('master user'))
    type = models.ForeignKey(InstrumentType, verbose_name=_('type'))
    is_active = models.BooleanField(default=True)
    pricing_currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    price_multiplier = models.FloatField(default=1.)
    accrued_currency = models.ForeignKey(Currency, null=True, blank=True, related_name='instruments_accrued',
                                         on_delete=models.PROTECT)
    accrued_multiplier = models.FloatField(default=1.)
    # classifiers = TreeManyToManyField(InstrumentClassifier, blank=True)
    tags = models.ManyToManyField(InstrumentTag, blank=True)

    daily_pricing_model = models.ForeignKey(DailyPricingModel, null=True, blank=True)
    accrual_calculation_model = models.ForeignKey(AccrualCalculationModel, null=True, blank=True)
    payment_frequency = models.ForeignKey(PaymentFrequency, null=True, blank=True)
    manual_pricing_formula = models.ForeignKey(ManualPricingFormula, null=True, blank=True)

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
    pricing_policy = models.ForeignKey('integrations.PricingPolicy', null=True, blank=True)
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


class AccrualCalculationSchedule(NamedModel):
    instrument = models.ForeignKey(Instrument, related_name='accrual_calculation_schedule')
    new_accrual_start_date = models.DateField(default=timezone.now)
    new_first_payment_date = models.DateField(default=timezone.now)
    new_accrual_size = models.FloatField(default=0.)
    payment_frequency = models.ForeignKey(PaymentFrequency)
    accrual_calculation_model = models.ForeignKey(AccrualCalculationModel)


class InstrumentAttr(AttrBase):
    # scheme = models.ForeignKey(AttrScheme, verbose_name=_('attribute scheme'))
    classifier = TreeForeignKey(InstrumentClassifier, null=True, blank=True)

    class Meta:
        pass


class InstrumentAttrValue(AttrValueBase):
    instrument = models.ForeignKey(Instrument)
    attr = models.ForeignKey(InstrumentAttr)
    classifier = TreeForeignKey(InstrumentClassifier, null=True, blank=True)

    class Meta:
        unique_together = [
            ['instrument', 'attr']
        ]


history.register(InstrumentClassifier)
history.register(InstrumentType)
history.register(InstrumentTypeTag)
history.register(InstrumentTag)
history.register(Instrument)
history.register(PriceHistory)
