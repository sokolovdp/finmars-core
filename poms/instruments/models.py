from __future__ import unicode_literals

from datetime import date

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from poms.common.models import NamedModel, AbstractClassModel
from poms.common.utils import date_now
from poms.obj_attrs.models import AbstractAttributeType, AbstractAttribute, AbstractAttributeTypeOption, \
    AbstractClassifier
from poms.obj_perms.models import AbstractGroupObjectPermission, AbstractUserObjectPermission
from poms.users.models import MasterUser, Member


class InstrumentClass(AbstractClassModel):
    GENERAL = 1
    EVENT_AT_MATURITY = 2
    REGULAR_EVENT_AT_MATURITY = 3
    PERPETUAL_REGULAR_EVENT = 4
    CONTRACT_FOR_DIFFERENCE = 5

    CLASSES = (
        (GENERAL, 'GENERAL', "General Class"),
        (EVENT_AT_MATURITY, 'EVENT_AT_MATURITY', "Event at Maturity"),
        (REGULAR_EVENT_AT_MATURITY, 'REGULAR_EVENT_AT_MATURITY', "Regular Event with Maturity"),
        (PERPETUAL_REGULAR_EVENT, 'PERPETUAL_REGULAR_EVENT', "Perpetual Regular Event"),
        (CONTRACT_FOR_DIFFERENCE, 'CONTRACT_FOR_DIFFERENCE', "Contract for Difference"),
    )

    class Meta(AbstractClassModel.Meta):
        verbose_name = _('instrument class')
        verbose_name_plural = _('instrument classes')


class DailyPricingModel(AbstractClassModel):
    SKIP = 1
    FORMULA_ALWAYS = 2
    FORMULA_IF_OPEN = 3
    PROVIDER_ALWAYS = 4
    PROVIDER_IF_OPEN = 5
    CLASSES = (
        (SKIP, 'SKIP', _("Skip")),
        (FORMULA_ALWAYS, 'FORMULA_ALWAYS', _("Formula (always)")),
        (FORMULA_IF_OPEN, 'FORMULA_IF_OPEN', _("Formula (if open)")),
        (PROVIDER_ALWAYS, 'PROVIDER_ALWAYS', _("Provider (always)")),
        (PROVIDER_IF_OPEN, 'PROVIDER_IF_OPEN', _("Provider (if open)")),
    )

    class Meta(AbstractClassModel.Meta):
        verbose_name = _('daily pricing model')
        verbose_name_plural = _('daily pricing models')


class AccrualCalculationModel(AbstractClassModel):
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
        (NONE, 'NONE', _("none")),
        (ACT_ACT, 'ACT_ACT', _("ACT/ACT")),
        (ACT_ACT_ISDA, 'ACT_ACT_ISDA', _("ACT/ACT - ISDA")),
        (ACT_360, 'ACT_360', _("ACT/360")),
        (ACT_365, 'ACT_365', _("ACT/365")),
        (ACT_365_25, 'ACT_365_25', _("Act/365.25")),
        (ACT_365_366, 'ACT_365_366', _("Act/365(366)")),
        (ACT_1_365, 'ACT_1_365', _("Act+1/365")),
        (ACT_1_360, 'ACT_1_360', _("Act+1/360")),
        (C_30_ACT, 'C_30_ACT', _("30/ACT")),
        (C_30_360, 'C_30_360', _("30/360")),
        (C_30_360_NO_EOM, 'C_30_360_NO_EOM', _("30/360 (NO EOM)")),
        (C_30E_P_360_ITL, 'C_30E_P_360_ITL', _("30E+/360.ITL")),
        (NL_365, 'NL_365', _("NL/365")),
        (NL_365_NO_EOM, 'NL_365_NO_EOM', _("NL/365 (NO-EOM)")),
        (ISMA_30_365, 'ISMA_30_365', _("ISMA-30/360")),
        (ISMA_30_365_NO_EOM, 'ISMA_30_365_NO_EOM', _("ISMA-30/360 (NO EOM)")),
        (US_MINI_30_360_EOM, 'US_MINI_30_360_EOM', _("US MUNI-30/360 (EOM)")),
        (US_MINI_30_360_NO_EOM, 'US_MINI_30_360_NO_EOM', _("US MUNI-30/360 (NO EOM)")),
        (BUS_DAYS_252, 'BUS_DAYS_252', _("BUS DAYS/252")),
        (GERMAN_30_360_EOM, 'GERMAN_30_360_EOM', _("GERMAN-30/360 (EOM)")),
        (GERMAN_30_360_NO_EOM, 'GERMAN_30_360_NO_EOM', _("GERMAN-30/360 (NO EOM)")),
        (REVERSED_ACT_365, 'REVERSED_ACT_365', _("Reversed ACT/365")),
    )

    class Meta(AbstractClassModel.Meta):
        verbose_name = _('accrual calculation model')
        verbose_name_plural = _('accrual calculation models')


# class PaymentFrequency(ClassModelBase):
#     # TODO: add "values"
#     CLASSES = tuple()
#
#     class Meta:
#         verbose_name = _('payment frequency')
#         verbose_name_plural = _('payment frequencies')

class PaymentSizeDetail(AbstractClassModel):
    PERCENT = 1
    PER_ANNUM = 2
    PER_QUARTER = 3
    PER_MONTH = 4
    PER_WEEK = 5
    PER_DAY = 6
    CLASSES = (
        (PERCENT, 'PERCENT', _("% per annum")),
        (PER_ANNUM, 'PER_ANNUM', _("per annum")),
        (PER_QUARTER, 'PER_QUARTER', _("per quarter")),
        (PER_MONTH, 'PER_MONTH', _("per month")),
        (PER_WEEK, 'PER_WEEK', _("per week")),
        (PER_DAY, 'PER_DAY', _("per day")),
    )

    class Meta(AbstractClassModel.Meta):
        verbose_name = _('payment size detail')
        verbose_name_plural = _('payment size details')


class Periodicity(AbstractClassModel):
    N_DAY = 1
    N_WEEK = 2
    N_MONTH = 3
    N_MONTH_DAY = 4
    N_YEAR = 5
    N_YEAR_DAY = 6

    WEEKLY = 7
    MONTHLY = 8
    QUARTERLY = 9
    SEMI_ANNUALLY = 10
    ANNUALLY = 11

    CLASSES = (
        (N_DAY, 'N_DAY', _("N Days")),
        (N_WEEK, 'N_WEEK', _("N Weeks (eobw)")),
        (N_MONTH, 'N_MONTH', _("N Months (eom)")),
        (N_MONTH_DAY, 'N_MONTH_DAY', _("N Months (same date)")),
        (N_YEAR, 'N_YEAR', _("N Years (eoy)")),
        (N_YEAR_DAY, 'N_YEAR_DAY', _("N Years (same date)")),

        (WEEKLY, 'WEEKLY', _('Weekly')),
        (MONTHLY, 'MONTHLY', _('Monthly')),
        (QUARTERLY, 'QUARTERLY', _('Quarterly')),
        (SEMI_ANNUALLY, 'SEMI_ANNUALLY', _('Semi-annually')),
        (ANNUALLY, 'ANNUALLY', _('Annually')),
    )

    class Meta(AbstractClassModel.Meta):
        verbose_name = _('periodicity')
        verbose_name_plural = _('periodicities')


class CostMethod(AbstractClassModel):
    # TODO: add "values"
    AVCO = 1
    FIFO = 2
    LIFO = 3
    CLASSES = (
        (AVCO, 'AVCO', _('AVCO')),
        (FIFO, 'FIFO', _('FIFO')),
        # (LIFO, _('LIFO')),
    )

    class Meta(AbstractClassModel.Meta):
        verbose_name = _('cost method')
        verbose_name_plural = _('cost methods')


class PricingPolicy(NamedModel):
    # DISABLED = 0
    # BLOOMBERG = 1
    # TYPES = (
    #     (DISABLED, _('Disabled')),
    #     (BLOOMBERG, _('Bloomberg')),
    # )

    master_user = models.ForeignKey(MasterUser, related_name='pricing_policies',
                                    verbose_name=_('master user'))
    # type = models.PositiveIntegerField(default=DISABLED, choices=TYPES)
    expr = models.TextField(default='',
                            verbose_name=_('expression'))

    class Meta(AbstractClassModel.Meta):
        verbose_name = _('pricing policy')
        verbose_name_plural = _('pricing policies')
        unique_together = [
            ['master_user', 'user_code']
        ]


@python_2_unicode_compatible
class InstrumentType(NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='instrument_types',
                                    verbose_name=_('master user'))
    instrument_class = models.ForeignKey(InstrumentClass, related_name='instrument_types', on_delete=models.PROTECT,
                                         verbose_name=_('instrument class'))

    one_off_event = models.ForeignKey('transactions.TransactionType', null=True, blank=True, on_delete=models.PROTECT,
                                      related_name='instrument_types_one_off_event', verbose_name=_('one-off event'))
    regular_event = models.ForeignKey('transactions.TransactionType', null=True, blank=True, on_delete=models.PROTECT,
                                      related_name='instrument_types_regular_event', verbose_name=_('regular event'))

    class Meta(NamedModel.Meta):
        verbose_name = _('instrument type')
        verbose_name_plural = _('instrument types')
        permissions = [
            ('view_instrumenttype', 'Can view instrument type'),
            ('manage_instrumenttype', 'Can manage instrument type'),
        ]

    def __str__(self):
        return self.name

    @property
    def is_default(self):
        return self.master_user.instrument_type_id == self.id if self.master_user_id else False


class InstrumentTypeUserObjectPermission(AbstractUserObjectPermission):
    content_object = models.ForeignKey(InstrumentType, related_name='user_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractUserObjectPermission.Meta):
        verbose_name = _('instrument types - user permission')
        verbose_name_plural = _('instrument types - user permissions')


class InstrumentTypeGroupObjectPermission(AbstractGroupObjectPermission):
    content_object = models.ForeignKey(InstrumentType, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractGroupObjectPermission.Meta):
        verbose_name = _('instrument types - group permission')
        verbose_name_plural = _('instrument types - group permissions')


@python_2_unicode_compatible
class Instrument(NamedModel):
    master_user = models.ForeignKey(MasterUser, related_name='instruments', verbose_name=_('master user'))

    instrument_type = models.ForeignKey(InstrumentType, on_delete=models.PROTECT,
                                        verbose_name=_('instrument type'))
    is_active = models.BooleanField(default=True, verbose_name=_('is active'))
    pricing_currency = models.ForeignKey('currencies.Currency', on_delete=models.PROTECT,
                                         verbose_name=_('pricing currency'))
    price_multiplier = models.FloatField(default=1.0, verbose_name=_('price multiplier'))
    accrued_currency = models.ForeignKey('currencies.Currency', related_name='instruments_accrued',
                                         on_delete=models.PROTECT, verbose_name=_('accrued currency'))
    accrued_multiplier = models.FloatField(default=1.0, verbose_name=_('accrued multiplier'))

    payment_size_detail = models.ForeignKey(PaymentSizeDetail, on_delete=models.PROTECT, null=True, blank=True,
                                            verbose_name=_('payment size detail'))

    default_price = models.FloatField(default=0.0, verbose_name=_('default price'))
    default_accrued = models.FloatField(default=0.0, verbose_name=_('default accrued'))

    user_text_1 = models.CharField(max_length=255, null=True, blank=True, help_text=_('User specified field 1'))
    user_text_2 = models.CharField(max_length=255, null=True, blank=True, help_text=_('User specified field 2'))
    user_text_3 = models.CharField(max_length=255, null=True, blank=True, help_text=_('User specified field 3'))

    reference_for_pricing = models.CharField(max_length=100, blank=True, default='',
                                             verbose_name=_('reference for pricing'))
    daily_pricing_model = models.ForeignKey(DailyPricingModel, null=True, blank=True,
                                            verbose_name=_('daily pricing model'))
    price_download_scheme = models.ForeignKey('integrations.PriceDownloadScheme', on_delete=models.PROTECT, null=True,
                                              blank=True, verbose_name=_('price download scheme'))
    maturity_date = models.DateField(default=date.max, verbose_name=_('maturity date'))

    class Meta(NamedModel.Meta):
        verbose_name = _('instrument')
        verbose_name_plural = _('instruments')
        permissions = [
            ('view_instrument', 'Can view instrument'),
            ('manage_instrument', 'Can manage instrument'),
        ]

    def __str__(self):
        return self.name


class InstrumentUserObjectPermission(AbstractUserObjectPermission):
    content_object = models.ForeignKey(Instrument, related_name='user_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractUserObjectPermission.Meta):
        verbose_name = _('instruments - user permission')
        verbose_name_plural = _('instruments - user permissions')


class InstrumentGroupObjectPermission(AbstractGroupObjectPermission):
    content_object = models.ForeignKey(Instrument, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractGroupObjectPermission.Meta):
        verbose_name = _('instruments - group permission')
        verbose_name_plural = _('instruments - group permissions')


class InstrumentAttributeType(AbstractAttributeType):
    # classifier_root = models.OneToOneField(
    #     InstrumentClassifier,
    #     on_delete=models.PROTECT,
    #     null=True,
    #     blank=True,
    #     verbose_name=_('classifier')
    # )

    class Meta(AbstractAttributeType.Meta):
        verbose_name = _('instrument attribute type')
        verbose_name_plural = _('instrument attribute types')
        permissions = [
            ('view_instrumentattributetype', 'Can view instrument attribute type'),
            ('manage_instrumentattributetype', 'Can manage instrument attribute type'),
        ]


class InstrumentAttributeTypeUserObjectPermission(AbstractUserObjectPermission):
    content_object = models.ForeignKey(InstrumentAttributeType, related_name='user_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractUserObjectPermission.Meta):
        verbose_name = _('instrument attribute types - user permission')
        verbose_name_plural = _('instrument attribute types - user permissions')


class InstrumentAttributeTypeGroupObjectPermission(AbstractGroupObjectPermission):
    content_object = models.ForeignKey(InstrumentAttributeType, related_name='group_object_permissions',
                                       verbose_name=_('content object'))

    class Meta(AbstractGroupObjectPermission.Meta):
        verbose_name = _('instrument attribute types - group permission')
        verbose_name_plural = _('instrument attribute types - group permissions')


@python_2_unicode_compatible
class InstrumentClassifier(AbstractClassifier):
    attribute_type = models.ForeignKey(
        InstrumentAttributeType,
        null=True,
        blank=True,
        related_name='classifiers',
        verbose_name=_('attribute type')
    )
    parent = TreeForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='children',
        db_index=True,
        verbose_name=_('parent')
    )

    class Meta(AbstractClassifier.Meta):
        verbose_name = _('instrument classifier')
        verbose_name_plural = _('instrument classifiers')


class InstrumentAttributeTypeOption(AbstractAttributeTypeOption):
    member = models.ForeignKey(Member, related_name='instrument_attribute_type_options',
                               verbose_name=_('member'))
    attribute_type = models.ForeignKey(InstrumentAttributeType, related_name='options',
                                       verbose_name=_('attribute type'))

    class Meta(AbstractAttributeTypeOption.Meta):
        verbose_name = _('instrument attribute types - option')
        verbose_name_plural = _('instrument attribute types - options')


class InstrumentAttribute(AbstractAttribute):
    attribute_type = models.ForeignKey(InstrumentAttributeType, related_name='attributes', on_delete=models.PROTECT,
                                       verbose_name=_('attribute type'))
    content_object = models.ForeignKey(Instrument, related_name='attributes',
                                       verbose_name=_('content object'))
    classifier = models.ForeignKey(InstrumentClassifier, on_delete=models.PROTECT, null=True, blank=True,
                                   verbose_name=_('classifier'))

    class Meta(AbstractAttribute.Meta):
        verbose_name = _('instrument attribute')
        verbose_name_plural = _('instrument attributes')


@python_2_unicode_compatible
class ManualPricingFormula(models.Model):
    instrument = models.ForeignKey(Instrument, related_name='manual_pricing_formulas',
                                   verbose_name=_('instrument'))
    pricing_policy = models.ForeignKey(PricingPolicy, on_delete=models.PROTECT,
                                       related_name='manual_pricing_formulas',
                                       verbose_name=_('pricing policy'))
    expr = models.CharField(max_length=255, blank=True, default='',
                            verbose_name=_('expression'))
    notes = models.TextField(blank=True, default='',
                             verbose_name=_('notes'))

    class Meta:
        verbose_name = _('manual pricing formula')
        verbose_name_plural = _('manual pricing formulas')
        unique_together = [
            ['instrument', 'pricing_policy']
        ]

    def __str__(self):
        return '%s' % (self.id,)


@python_2_unicode_compatible
class PriceHistory(models.Model):
    instrument = models.ForeignKey(Instrument, related_name='prices', verbose_name=_('instrument'))
    pricing_policy = models.ForeignKey(PricingPolicy, on_delete=models.PROTECT, null=True, blank=True,
                                       verbose_name=_('pricing policy'))
    date = models.DateField(db_index=True, default=date_now, verbose_name=_('date'))
    principal_price = models.FloatField(default=0.0, verbose_name=_('principal price'))
    accrued_price = models.FloatField(default=0.0, verbose_name=_('accrued price'))

    class Meta:
        verbose_name = _('price history')
        verbose_name_plural = _('price histories')
        unique_together = (
            ('instrument', 'pricing_policy', 'date',)
        )

    def __str__(self):
        return '%s/%s@%s,%s,%s' % (
            self.instrument, self.pricing_policy, self.date, self.principal_price, self.accrued_price)


@python_2_unicode_compatible
class AccrualCalculationSchedule(models.Model):
    instrument = models.ForeignKey(Instrument, related_name='accrual_calculation_schedules',
                                   verbose_name=_('instrument'))
    accrual_start_date = models.DateField(default=date_now, verbose_name=_('accrual start date'))
    first_payment_date = models.DateField(default=date_now, verbose_name=_('first payment date'))
    accrual_size = models.FloatField(default=0.0, verbose_name=_('accrual size'))
    accrual_calculation_model = models.ForeignKey(AccrualCalculationModel, on_delete=models.PROTECT,
                                                  verbose_name=_('accrual calculation model'))
    periodicity = models.ForeignKey(Periodicity, on_delete=models.PROTECT, null=True, blank=True,
                                    verbose_name=_('periodicity'))
    periodicity_n = models.IntegerField(default=0, verbose_name=_('periodicity n'))
    notes = models.TextField(blank=True, default='', verbose_name=_('notes'))

    class Meta:
        verbose_name = _('accrual calculation schedule')
        verbose_name_plural = _('accrual calculation schedules')

    def __str__(self):
        return '%s' % (self.id,)


@python_2_unicode_compatible
class InstrumentFactorSchedule(models.Model):
    instrument = models.ForeignKey(Instrument, related_name='factor_schedules', verbose_name=_('instrument'))
    effective_date = models.DateField(default=date_now, verbose_name=_('effective date'))
    factor_value = models.FloatField(default=0., verbose_name=_('factor value'))

    class Meta:
        verbose_name = _('instrument factor schedule')
        verbose_name_plural = _('instrument factor schedules')

    def __str__(self):
        return '%s' % (self.id,)


class EventSchedule(models.Model):
    instrument = models.ForeignKey(Instrument, related_name='event_schedules', verbose_name=_('instrument'))
    name = models.CharField(max_length=255, verbose_name=_('name'))
    description = models.TextField(blank=True, default='', verbose_name=_('description'))

    event_class = models.ForeignKey('transactions.EventClass', on_delete=models.PROTECT, verbose_name=_('event class'))
    notification_class = models.ForeignKey('transactions.NotificationClass', on_delete=models.PROTECT,
                                           verbose_name=_('notification class'))

    effective_date = models.DateField(null=True, blank=True, verbose_name=_('effective date'))
    notify_in_n_days = models.IntegerField(default=0)
    # notification_date = models.DateField(null=True, blank=True, verbose_name=_('notification date'))

    # initial_date -> effective_date
    periodicity = models.ForeignKey(Periodicity, null=True, blank=True, on_delete=models.PROTECT)
    periodicity_n = models.IntegerField(default=0)
    final_date = models.DateField(default=date.max)

    class Meta:
        verbose_name = _('event schedule')
        verbose_name_plural = _('event schedules')

    def __str__(self):
        return self.name


class EventScheduleAction(models.Model):
    event_schedule = models.ForeignKey(EventSchedule, related_name='actions', verbose_name=_('event schedule'))
    transaction_type = models.ForeignKey('transactions.TransactionType', on_delete=models.PROTECT)
    text = models.CharField(max_length=100, blank=True, default='')
    is_sent_to_pending = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    button_position = models.IntegerField(default=0)

    class Meta:
        verbose_name = _('event schedule action')
        verbose_name_plural = _('event schedule actions')

    def __str__(self):
        return self.text
