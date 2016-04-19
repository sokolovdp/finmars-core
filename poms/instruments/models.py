from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from poms.audit import history
from poms.common.models import NamedModel, ClassModelBase
from poms.currencies.models import Currency
from poms.obj_attrs.models import AttributeTypeBase, AttributeBase, AttributeTypeOptionBase
from poms.obj_perms.models import UserObjectPermissionBase, GroupObjectPermissionBase
from poms.users.models import MasterUser, Member


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
    SKIP = 1
    MANUAL = 2
    BLOOMBERG = 3
    CLASSES = (
        (SKIP, _("Skip")),
        (MANUAL, _("Manual")),
        (BLOOMBERG, _("Bloomberg")),
    )

    class Meta:
        verbose_name = _('daily pricing model')
        verbose_name_plural = _('daily pricing models')


class AccrualCalculationModel(ClassModelBase):
    NONE = 1
    ACT_ACT = 2
    ACT_ACT_ISDA = 3
    ACT_360 = 4
    ACT_365 = 5
    ACT_365_25 = 6
    ACT_365_366 = 7
    ACT_1_365 = 8
    ACT_1_360 = 9
    C_30_ACT = 10
    C_30_360 = 11
    C_30_360_NO_EOM = 12
    C_30E_P_360_ITL = 13
    NL_365 = 14
    NL_365_NO_EOM = 15
    ISMA_30_365 = 16
    ISMA_30_365_NO_EOM = 17
    US_MINI_30_360_EOM = 18
    US_MINI_30_360_NO_EOM = 19
    BUS_DAYS_252 = 20
    GERMAN_30_360_EOM = 21
    GERMAN_30_360_NO_EOM = 22
    REVERSED_ACT_365 = 23

    CLASSES = (
        (NONE, _("none")),
        (ACT_ACT, _("ACT/ACT")),
        (ACT_ACT_ISDA, _("ACT/ACT - ISDA")),
        (ACT_360, _("ACT/360")),
        (ACT_365, _("ACT/365")),
        (ACT_365_25, _("Act/365.25")),
        (ACT_365_366, _("Act/365(366)")),
        (ACT_1_365, _("Act+1/365")),
        (ACT_1_360, _("Act+1/360")),
        (C_30_ACT, _("30/ACT")),
        (C_30_360, _("30/360")),
        (C_30_360_NO_EOM, _("30/360 (NO EOM)")),
        (C_30E_P_360_ITL, _("30E+/360.ITL")),
        (NL_365, _("NL/365")),
        (NL_365_NO_EOM, _("NL/365 (NO-EOM)")),
        (ISMA_30_365, _("ISMA-30/360")),
        (ISMA_30_365_NO_EOM, _("ISMA-30/360 (NO EOM)")),
        (US_MINI_30_360_EOM, _("US MUNI-30/360 (EOM)")),
        (US_MINI_30_360_NO_EOM, _("US MUNI-30/360 (NO EOM)")),
        (BUS_DAYS_252, _("BUS DAYS/252")),
        (GERMAN_30_360_EOM, _("GERMAN-30/360 (EOM)")),
        (GERMAN_30_360_NO_EOM, _("GERMAN-30/360 (NO EOM)")),
        (NONE, _("Reversed ACT/365")),
    )

    class Meta:
        verbose_name = _('accrual calculation model')
        verbose_name_plural = _('accrual calculation models')


# class PaymentFrequency(ClassModelBase):
#     # TODO: add "values"
#     CLASSES = tuple()
#
#     class Meta:
#         verbose_name = _('payment frequency')
#         verbose_name_plural = _('payment frequencies')

class PaymentSizeDetail(ClassModelBase):
    PERCENT = 1
    PER_ANNUM = 2
    PER_QUARTER = 3
    PER_MONTH = 4
    PER_WEEK = 5
    PER_DAY = 6
    CLASSES = (
        (PERCENT, _("% per annum")),
        (PER_ANNUM, _("per annum")),
        (PER_QUARTER, _("per quarter")),
        (PER_MONTH, _("per month")),
        (PER_WEEK, _("per week")),
        (PER_DAY, _("per day")),
    )

    class Meta:
        verbose_name = _('payment size detail')
        verbose_name_plural = _('payment size details')


class PeriodicityPeriod(ClassModelBase):
    DAY = 1
    WEEK = 2
    MONTH = 3
    MONTH_DAY = 4
    YEAR = 5
    YEAR_DAY = 6
    CLASSES = (
        (DAY, _("N Days")),
        (WEEK, _("N Weeks (eobw)")),
        (MONTH, _("N Months (eom)")),
        (MONTH_DAY, _("N Months (same date)")),
        (YEAR, _("N Years (eoy)")),
        (YEAR_DAY, _("N Years (same date)")),
    )

    class Meta:
        verbose_name = _('periodicity period')
        verbose_name_plural = _('periodicity periods')


class CostMethod(ClassModelBase):
    # TODO: add "values"
    AVCO = 1
    FIFO = 2
    LIFO = 3
    CLASSES = (
        (AVCO, _('AVCO')),
        (FIFO, _('FIFO')),
        # (LIFO, _('LIFO')),
    )

    class Meta:
        verbose_name = _('cost method')
        verbose_name_plural = _('cost methods')


@python_2_unicode_compatible
class InstrumentType(NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='instrument_types', verbose_name=_('master user'))
    instrument_class = models.ForeignKey(InstrumentClass, related_name='instrument_types',
                                         verbose_name=_('instrument class'))

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


class InstrumentTypeUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(InstrumentType, related_name='user_object_permissions')

    class Meta:
        verbose_name = _('instrument types - user permission')
        verbose_name_plural = _('instrument types - user permissions')


class InstrumentTypeGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(InstrumentType, related_name='group_object_permissions')

    class Meta:
        verbose_name = _('instrument types - group permission')
        verbose_name_plural = _('instrument types - group permissions')


@python_2_unicode_compatible
class InstrumentClassifier(MPTTModel, NamedModel):
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


class InstrumentClassifierUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(InstrumentClassifier, related_name='user_object_permissions')

    class Meta:
        verbose_name = _('instrument classifiers - user permission')
        verbose_name_plural = _('instrument classifiers - user permissions')


class InstrumentClassifierGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(InstrumentClassifier, related_name='group_object_permissions')

    class Meta:
        verbose_name = _('instrument classifiers - group permission')
        verbose_name_plural = _('instrument classifiers - group permissions')


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

    daily_pricing_model = models.ForeignKey(DailyPricingModel, null=True, blank=True)
    payment_size_detail = models.ForeignKey(PaymentSizeDetail, null=True, blank=True)
    default_price = models.FloatField(default=0.)
    default_accrued = models.FloatField(default=0.)

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


class InstrumentUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(Instrument, related_name='user_object_permissions')

    class Meta:
        verbose_name = _('instruments - user permission')
        verbose_name_plural = _('instruments - user permissions')


class InstrumentGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(Instrument, related_name='group_object_permissions')

    class Meta:
        verbose_name = _('instruments - group permission')
        verbose_name_plural = _('instruments - group permissions')


class InstrumentAttributeType(AttributeTypeBase):
    classifier_root = models.ForeignKey(InstrumentClassifier, null=True, blank=True)

    class Meta:
        verbose_name = _('instrument attribute type')
        verbose_name_plural = _('instrument attribute types')


class InstrumentAttributeTypeOption(AttributeTypeOptionBase):
    member = models.ForeignKey(Member, related_name='instrument_attribute_type_options')
    attribute_type = models.ForeignKey(InstrumentAttributeType, related_name='attribute_type_options')

    class Meta:
        verbose_name = _('instrument attribute types - option')
        verbose_name_plural = _('instrument attribute types - options')


class InstrumentAttributeTypeUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(InstrumentAttributeType, related_name='user_object_permissions')

    class Meta:
        verbose_name = _('instrument attribute types - user permission')
        verbose_name_plural = _('instrument attribute types - user permissions')


class InstrumentAttributeTypeGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(InstrumentAttributeType, related_name='group_object_permissions')

    class Meta:
        verbose_name = _('instrument attribute types - group permission')
        verbose_name_plural = _('instrument attribute types - group permissions')


class InstrumentAttribute(AttributeBase):
    attribute_type = models.ForeignKey(InstrumentAttributeType, related_name='attributes')
    content_object = models.ForeignKey(Instrument)
    classifier = models.ForeignKey(InstrumentClassifier, null=True, blank=True)

    class Meta(AttributeBase.Meta):
        verbose_name = _('instrument attribute')
        verbose_name_plural = _('instrument attributes')


# @python_2_unicode_compatible
class ManualPricingFormula(models.Model):
    instrument = models.ForeignKey(Instrument)
    pricing_policy = models.ForeignKey('integrations.PricingPolicy')
    expr = models.CharField(max_length=255, blank=True, default='')
    notes = models.TextField(blank=True, default='', verbose_name=_('notes'))

    class Meta:
        verbose_name = _('manual pricing formula')
        verbose_name_plural = _('manual pricing formulas')
        unique_together = [
            ['instrument', 'pricing_policy']
        ]
        permissions = [
            ('view_manualpricingformula', 'Can view manual pricing formula')
        ]

    def __str__(self):
        return '%s - %s' % (self.instrument, self.pricing_policy)


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


class AccrualCalculationSchedule(models.Model):
    instrument = models.ForeignKey(Instrument, related_name='accrual_calculation_schedules')
    accrual_start_date = models.DateField(default=timezone.now)
    first_payment_date = models.DateField(default=timezone.now)
    accrual_size = models.FloatField(default=0.)
    accrual_calculation_model = models.ForeignKey(AccrualCalculationModel)
    periodicity_period = models.ForeignKey(PeriodicityPeriod, null=True, blank=True)
    notes = models.TextField(null=True, blank=True, verbose_name=_('notes'))


class InstrumentFactorSchedule(models.Model):
    instrument = models.ForeignKey(Instrument, related_name='factor_schedules')
    effective_date = models.DateField(default=timezone.now)
    factor_value = models.FloatField(default=0.)


class EventSchedule(NamedModel):
    instrument = models.ForeignKey(Instrument)
    transaction_types = models.ManyToManyField('transactions.TransactionType', blank=True)
    event_class = models.ForeignKey('transactions.EventClass')

    notification_class = models.ForeignKey('transactions.NotificationClass')
    notification_date = models.DateField(null=True, blank=True)

    effective_date = models.DateField(null=True, blank=True)


history.register(InstrumentClassifier)
history.register(InstrumentType)
history.register(Instrument)
history.register(PriceHistory)
