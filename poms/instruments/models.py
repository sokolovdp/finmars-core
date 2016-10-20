from __future__ import unicode_literals

from datetime import date

from dateutil import relativedelta, rrule
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext, ugettext_lazy
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from poms.common.models import NamedModel, AbstractClassModel, FakeDeletableModel
from poms.common.utils import date_now, isclose
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
        (GENERAL, 'GENERAL', ugettext_lazy("General Class")),
        (EVENT_AT_MATURITY, 'EVENT_AT_MATURITY', ugettext_lazy("Event at Maturity")),
        (REGULAR_EVENT_AT_MATURITY, 'REGULAR_EVENT_AT_MATURITY', ugettext_lazy("Regular Event with Maturity")),
        (PERPETUAL_REGULAR_EVENT, 'PERPETUAL_REGULAR_EVENT', ugettext_lazy("Perpetual Regular Event")),
        (CONTRACT_FOR_DIFFERENCE, 'CONTRACT_FOR_DIFFERENCE', ugettext_lazy("Contract for Difference")),
    )

    class Meta(AbstractClassModel.Meta):
        verbose_name = ugettext_lazy('instrument class')
        verbose_name_plural = ugettext_lazy('instrument classes')

    @property
    def has_one_off_event(self):
        return self.id in [self.EVENT_AT_MATURITY, self.REGULAR_EVENT_AT_MATURITY]

    @property
    def has_regular_event(self):
        return self.id in [self.REGULAR_EVENT_AT_MATURITY, self.PERPETUAL_REGULAR_EVENT]


class DailyPricingModel(AbstractClassModel):
    SKIP = 1
    FORMULA_ALWAYS = 2
    FORMULA_IF_OPEN = 3
    PROVIDER_ALWAYS = 4
    PROVIDER_IF_OPEN = 5
    CLASSES = (
        (SKIP, 'SKIP', ugettext_lazy("Skip")),
        (FORMULA_ALWAYS, 'FORMULA_ALWAYS', ugettext_lazy("Formula (always)")),
        (FORMULA_IF_OPEN, 'FORMULA_IF_OPEN', ugettext_lazy("Formula (if open)")),
        (PROVIDER_ALWAYS, 'PROVIDER_ALWAYS', ugettext_lazy("Provider (always)")),
        (PROVIDER_IF_OPEN, 'PROVIDER_IF_OPEN', ugettext_lazy("Provider (if open)")),
    )

    class Meta(AbstractClassModel.Meta):
        verbose_name = ugettext_lazy('daily pricing model')
        verbose_name_plural = ugettext_lazy('daily pricing models')


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
    # C_30_ACT = 10
    C_30_360 = 11
    C_30_360_NO_EOM = 12
    C_30E_P_360 = 24
    C_30E_P_360_ITL = 13
    NL_365 = 14
    NL_365_NO_EOM = 15
    ISMA_30_360 = 16
    ISMA_30_360_NO_EOM = 17
    US_MINI_30_360_EOM = 18
    US_MINI_30_360_NO_EOM = 19
    BUS_DAYS_252 = 20
    GERMAN_30_360_EOM = 21
    GERMAN_30_360_NO_EOM = 22
    REVERSED_ACT_365 = 23

    CLASSES = (
        (NONE, 'NONE', ugettext_lazy("none")),
        (ACT_ACT, 'ACT_ACT', ugettext_lazy("ACT/ACT")),
        (ACT_ACT_ISDA, 'ACT_ACT_ISDA', ugettext_lazy("ACT/ACT - ISDA")),
        (ACT_360, 'ACT_360', ugettext_lazy("ACT/360")),
        (ACT_365, 'ACT_365', ugettext_lazy("ACT/365")),
        (ACT_365_25, 'ACT_365_25', ugettext_lazy("Act/365.25")),
        (ACT_365_366, 'ACT_365_366', ugettext_lazy("Act/365(366)")),
        (ACT_1_365, 'ACT_1_365', ugettext_lazy("Act+1/365")),
        (ACT_1_360, 'ACT_1_360', ugettext_lazy("Act+1/360")),
        # (C_30_ACT, 'C_30_ACT', ugettext_lazy("30/ACT")),
        (C_30_360, 'C_30_360', ugettext_lazy("30/360")),
        (C_30_360_NO_EOM, 'C_30_360_NO_EOM', ugettext_lazy("30/360 (NO EOM)")),
        (C_30E_P_360_ITL, 'C_30E_P_360_ITL', ugettext_lazy("30E+/360.ITL")),
        (NL_365, 'NL_365', ugettext_lazy("NL/365")),
        (NL_365_NO_EOM, 'NL_365_NO_EOM', ugettext_lazy("NL/365 (NO-EOM)")),
        (ISMA_30_360, 'ISMA_30_360', ugettext_lazy("ISMA-30/360")),
        (ISMA_30_360_NO_EOM, 'ISMA_30_360_NO_EOM', ugettext_lazy("ISMA-30/360 (NO EOM)")),
        (US_MINI_30_360_EOM, 'US_MINI_30_360_EOM', ugettext_lazy("US MUNI-30/360 (EOM)")),
        (US_MINI_30_360_NO_EOM, 'US_MINI_30_360_NO_EOM', ugettext_lazy("US MUNI-30/360 (NO EOM)")),
        (BUS_DAYS_252, 'BUS_DAYS_252', ugettext_lazy("BUS DAYS/252")),
        (GERMAN_30_360_EOM, 'GERMAN_30_360_EOM', ugettext_lazy("GERMAN-30/360 (EOM)")),
        (GERMAN_30_360_NO_EOM, 'GERMAN_30_360_NO_EOM', ugettext_lazy("GERMAN-30/360 (NO EOM)")),
        (REVERSED_ACT_365, 'REVERSED_ACT_365', ugettext_lazy("Reversed ACT/365")),
        (C_30E_P_360, 'C_30E_P_360', ugettext_lazy('30E+/360'))
    )

    class Meta(AbstractClassModel.Meta):
        verbose_name = ugettext_lazy('accrual calculation model')
        verbose_name_plural = ugettext_lazy('accrual calculation models')


class PaymentSizeDetail(AbstractClassModel):
    PERCENT = 1
    PER_ANNUM = 2
    PER_QUARTER = 3
    PER_MONTH = 4
    PER_WEEK = 5
    PER_DAY = 6
    CLASSES = (
        (PERCENT, 'PERCENT', ugettext_lazy("% per annum")),
        (PER_ANNUM, 'PER_ANNUM', ugettext_lazy("per annum")),
        (PER_QUARTER, 'PER_QUARTER', ugettext_lazy("per quarter")),
        (PER_MONTH, 'PER_MONTH', ugettext_lazy("per month")),
        (PER_WEEK, 'PER_WEEK', ugettext_lazy("per week")),
        (PER_DAY, 'PER_DAY', ugettext_lazy("per day")),
    )

    class Meta(AbstractClassModel.Meta):
        verbose_name = ugettext_lazy('payment size detail')
        verbose_name_plural = ugettext_lazy('payment size details')


class Periodicity(AbstractClassModel):
    N_DAY = 1
    N_WEEK_EOBW = 2
    N_MONTH_EOM = 3
    N_MONTH_SAME_DAY = 4
    N_YEAR_EOY = 5
    N_YEAR_SAME_DAY = 6

    WEEKLY = 7
    MONTHLY = 8
    QUARTERLY = 9
    SEMI_ANNUALLY = 10
    ANNUALLY = 11
    BIMONTHLY = 12

    CLASSES = (
        (N_DAY, 'N_DAY', ugettext_lazy("N Days")),
        (N_WEEK_EOBW, 'N_WEEK_EOBW', ugettext_lazy("N Weeks (eobw)")),
        (N_MONTH_EOM, 'N_MONTH_EOM', ugettext_lazy("N Months (eom)")),
        (N_MONTH_SAME_DAY, 'N_MONTH_SAME_DAY', ugettext_lazy("N Months (same date)")),
        (N_YEAR_EOY, 'N_YEAR_EOY', ugettext_lazy("N Years (eoy)")),
        (N_YEAR_SAME_DAY, 'N_YEAR_SAME_DAY', ugettext_lazy("N Years (same date)")),

        (WEEKLY, 'WEEKLY', ugettext_lazy('Weekly')),
        (MONTHLY, 'MONTHLY', ugettext_lazy('Monthly')),
        (BIMONTHLY, 'BIMONTHLY', ugettext_lazy('Bimonthly')),
        (QUARTERLY, 'QUARTERLY', ugettext_lazy('Quarterly')),
        (SEMI_ANNUALLY, 'SEMI_ANNUALLY', ugettext_lazy('Semi-annually')),
        (ANNUALLY, 'ANNUALLY', ugettext_lazy('Annually')),
    )

    class Meta(AbstractClassModel.Meta):
        verbose_name = ugettext_lazy('periodicity')
        verbose_name_plural = ugettext_lazy('periodicities')

    def to_timedelta(self, delta=1, same_date=None):
        if delta is None:
            delta = 1

        if self.id == Periodicity.N_DAY:
            return relativedelta.relativedelta(days=delta)
        elif self.id == Periodicity.N_WEEK_EOBW:
            # return relativedelta.relativedelta(days=7 * delta, weekday=relativedelta.FR)
            return relativedelta.relativedelta(weeks=delta, weekday=relativedelta.FR)
        elif self.id == Periodicity.N_MONTH_EOM:
            return relativedelta.relativedelta(months=delta, day=31)
        elif self.id == Periodicity.N_MONTH_SAME_DAY:
            return relativedelta.relativedelta(months=delta, day=same_date.day)
        elif self.id == Periodicity.N_YEAR_EOY:
            return relativedelta.relativedelta(years=delta, month=12, day=31)
        elif self.id == Periodicity.N_YEAR_SAME_DAY:
            return relativedelta.relativedelta(years=delta, month=same_date.month, day=same_date.day)
        elif self.id == Periodicity.WEEKLY:
            return relativedelta.relativedelta(weeks=1 * delta)
        elif self.id == Periodicity.MONTHLY:
            return relativedelta.relativedelta(months=1 * delta)
        elif self.id == Periodicity.BIMONTHLY:
            return relativedelta.relativedelta(months=2 * delta)
        elif self.id == Periodicity.QUARTERLY:
            return relativedelta.relativedelta(months=3 * delta)
        elif self.id == Periodicity.SEMI_ANNUALLY:
            return relativedelta.relativedelta(months=6 * delta)
        elif self.id == Periodicity.ANNUALLY:
            return relativedelta.relativedelta(years=1 * delta)
        return None

    # @staticmethod
    # def to_rrule(periodicity, dtstart=None, count=None, until=None):
    #     if isinstance(periodicity, Periodicity):
    #         periodicity = periodicity.id
    #
    #     if periodicity == Periodicity.N_DAY:
    #         return rrule.rrule(dtstart=dtstart, count=count, until=until, freq=rrule.DAILY)
    #     elif periodicity == Periodicity.N_WEEK_EOBW:
    #         return rrule.rrule(dtstart=dtstart, count=count, until=until, freq=rrule.WEEKLY,
    #                            byweekday=[rrule.FR])
    #     elif periodicity == Periodicity.N_MONTH_EOM:
    #         return rrule.rrule(dtstart=dtstart, count=count, until=until, freq=rrule.MONTHLY,
    #                            bymonthday=[31])
    #     elif periodicity == Periodicity.N_MONTH_SAME_DAY:
    #         return rrule.rrule(dtstart=dtstart, count=count, until=until, freq=rrule.MONTHLY,
    #                            bymonthday=[dtstart.day])
    #     elif periodicity == Periodicity.N_YEAR_EOY:
    #         return rrule.rrule(dtstart=dtstart, count=count, until=until, freq=rrule.YEARLY,
    #                            bymonth=[12], bymonthday=[31])
    #     elif periodicity == Periodicity.N_YEAR_SAME_DAY:
    #         return rrule.rrule(dtstart=dtstart, count=count, until=until, freq=rrule.WEEKLY)
    #     elif periodicity == Periodicity.WEEKLY:
    #         return rrule.rrule(dtstart=dtstart, count=count, until=until, freq=rrule.WEEKLY)
    #     elif periodicity == Periodicity.MONTHLY:
    #         return rrule.rrule(dtstart=dtstart, count=count, until=until, freq=rrule.MONTHLY)
    #     elif periodicity == Periodicity.BIMONTHLY:
    #         return rrule.rrule(dtstart=dtstart, count=count, interval=2, until=until, freq=rrule.MONTHLY)
    #     elif periodicity == Periodicity.QUARTERLY:
    #         return rrule.rrule(dtstart=dtstart, count=count, interval=3, until=until, freq=rrule.MONTHLY)
    #     elif periodicity == Periodicity.SEMI_ANNUALLY:
    #         return rrule.rrule(dtstart=dtstart, count=count, interval=6, until=until, freq=rrule.MONTHLY)
    #     elif periodicity == Periodicity.ANNUALLY:
    #         return rrule.rrule(dtstart=dtstart, count=count, until=until, freq=rrule.YEARLY)
    #     return None

    def to_freq(self):
        if self.id == Periodicity.N_DAY:
            return 0
        elif self.id == Periodicity.N_WEEK_EOBW:
            return 0
        elif self.id == Periodicity.N_MONTH_EOM:
            return 0
        elif self.id == Periodicity.N_MONTH_SAME_DAY:
            return 0
        elif self.id == Periodicity.N_YEAR_EOY:
            return 0
        elif self.id == Periodicity.N_YEAR_SAME_DAY:
            return 0
        elif self.id == Periodicity.WEEKLY:
            return 52
        elif self.id == Periodicity.MONTHLY:
            return 12
        elif self.id == Periodicity.BIMONTHLY:
            return 6
        elif self.id == Periodicity.QUARTERLY:
            return 4
        elif self.id == Periodicity.SEMI_ANNUALLY:
            return 2
        elif self.id == Periodicity.ANNUALLY:
            return 1
        return 0


class CostMethod(AbstractClassModel):
    AVCO = 1
    FIFO = 2
    LIFO = 3
    CLASSES = (
        (AVCO, 'AVCO', ugettext_lazy('AVCO')),
        (FIFO, 'FIFO', ugettext_lazy('FIFO')),
        # (LIFO, ugettext_lazy('LIFO')),
    )

    class Meta(AbstractClassModel.Meta):
        verbose_name = ugettext_lazy('cost method')
        verbose_name_plural = ugettext_lazy('cost methods')


class PricingPolicy(NamedModel):
    # DISABLED = 0
    # BLOOMBERG = 1
    # TYPES = (
    #     (DISABLED, ugettext_lazy('Disabled')),
    #     (BLOOMBERG, ugettext_lazy('Bloomberg')),
    # )

    master_user = models.ForeignKey(MasterUser, related_name='pricing_policies',
                                    verbose_name=ugettext_lazy('master user'))
    # type = models.PositiveIntegerField(default=DISABLED, choices=TYPES)
    expr = models.CharField(max_length=255, default='', blank=True, verbose_name=ugettext_lazy('expression'))

    class Meta(AbstractClassModel.Meta):
        verbose_name = ugettext_lazy('pricing policy')
        verbose_name_plural = ugettext_lazy('pricing policies')


@python_2_unicode_compatible
class InstrumentType(NamedModel, FakeDeletableModel):
    master_user = models.ForeignKey(MasterUser, related_name='instrument_types',
                                    verbose_name=ugettext_lazy('master user'))
    instrument_class = models.ForeignKey(InstrumentClass, related_name='instrument_types', on_delete=models.PROTECT,
                                         verbose_name=ugettext_lazy('instrument class'))

    one_off_event = models.ForeignKey('transactions.TransactionType', null=True, blank=True, on_delete=models.PROTECT,
                                      related_name='+', verbose_name=ugettext_lazy('one-off event'))
    regular_event = models.ForeignKey('transactions.TransactionType', null=True, blank=True, on_delete=models.PROTECT,
                                      related_name='+', verbose_name=ugettext_lazy('regular event'))

    factor_same = models.ForeignKey('transactions.TransactionType', null=True, blank=True, on_delete=models.PROTECT,
                                    related_name='+', verbose_name=ugettext_lazy('factor same'))
    factor_up = models.ForeignKey('transactions.TransactionType', null=True, blank=True, on_delete=models.PROTECT,
                                  related_name='+', verbose_name=ugettext_lazy('factor up'))
    factor_down = models.ForeignKey('transactions.TransactionType', null=True, blank=True, on_delete=models.PROTECT,
                                    related_name='+', verbose_name=ugettext_lazy('factor down'))

    class Meta(NamedModel.Meta, FakeDeletableModel.Meta):
        verbose_name = ugettext_lazy('instrument type')
        verbose_name_plural = ugettext_lazy('instrument types')
        permissions = [
            ('view_instrumenttype', 'Can view instrument type'),
            ('manage_instrumenttype', 'Can manage instrument type'),
        ]

    def __str__(self):
        return self.user_code

    @property
    def is_default(self):
        return self.master_user.instrument_type_id == self.id if self.master_user_id else False


class InstrumentTypeUserObjectPermission(AbstractUserObjectPermission):
    content_object = models.ForeignKey(InstrumentType, related_name='user_object_permissions',
                                       verbose_name=ugettext_lazy('content object'))

    class Meta(AbstractUserObjectPermission.Meta):
        verbose_name = ugettext_lazy('instrument types - user permission')
        verbose_name_plural = ugettext_lazy('instrument types - user permissions')


class InstrumentTypeGroupObjectPermission(AbstractGroupObjectPermission):
    content_object = models.ForeignKey(InstrumentType, related_name='group_object_permissions',
                                       verbose_name=ugettext_lazy('content object'))

    class Meta(AbstractGroupObjectPermission.Meta):
        verbose_name = ugettext_lazy('instrument types - group permission')
        verbose_name_plural = ugettext_lazy('instrument types - group permissions')


@python_2_unicode_compatible
class Instrument(NamedModel, FakeDeletableModel):
    master_user = models.ForeignKey(MasterUser, related_name='instruments', verbose_name=ugettext_lazy('master user'))

    instrument_type = models.ForeignKey(InstrumentType, on_delete=models.PROTECT,
                                        verbose_name=ugettext_lazy('instrument type'))
    is_active = models.BooleanField(default=True, verbose_name=ugettext_lazy('is active'))
    pricing_currency = models.ForeignKey('currencies.Currency', on_delete=models.PROTECT,
                                         verbose_name=ugettext_lazy('pricing currency'))
    price_multiplier = models.FloatField(default=1.0, verbose_name=ugettext_lazy('price multiplier'))
    accrued_currency = models.ForeignKey('currencies.Currency', related_name='instruments_accrued',
                                         on_delete=models.PROTECT, verbose_name=ugettext_lazy('accrued currency'))
    accrued_multiplier = models.FloatField(default=1.0, verbose_name=ugettext_lazy('accrued multiplier'))

    payment_size_detail = models.ForeignKey(PaymentSizeDetail, on_delete=models.PROTECT, null=True, blank=True,
                                            verbose_name=ugettext_lazy('payment size detail'))

    default_price = models.FloatField(default=0.0, verbose_name=ugettext_lazy('default price'))
    default_accrued = models.FloatField(default=0.0, verbose_name=ugettext_lazy('default accrued'))

    user_text_1 = models.CharField(max_length=255, null=True, blank=True,
                                   help_text=ugettext_lazy('User specified field 1'))
    user_text_2 = models.CharField(max_length=255, null=True, blank=True,
                                   help_text=ugettext_lazy('User specified field 2'))
    user_text_3 = models.CharField(max_length=255, null=True, blank=True,
                                   help_text=ugettext_lazy('User specified field 3'))

    reference_for_pricing = models.CharField(max_length=100, blank=True, default='',
                                             verbose_name=ugettext_lazy('reference for pricing'))
    daily_pricing_model = models.ForeignKey(DailyPricingModel, null=True, blank=True,
                                            verbose_name=ugettext_lazy('daily pricing model'))
    price_download_scheme = models.ForeignKey('integrations.PriceDownloadScheme', on_delete=models.PROTECT, null=True,
                                              blank=True, verbose_name=ugettext_lazy('price download scheme'))
    maturity_date = models.DateField(default=date.max, verbose_name=ugettext_lazy('maturity date'))

    class Meta(NamedModel.Meta, FakeDeletableModel.Meta):
        verbose_name = ugettext_lazy('instrument')
        verbose_name_plural = ugettext_lazy('instruments')
        permissions = [
            ('view_instrument', 'Can view instrument'),
            ('manage_instrument', 'Can manage instrument'),
        ]
        ordering = ['user_code']

    # def __str__(self):
    #     return self.user_code

    def rebuild_event_schedules(self):
        from poms.transactions.models import EventClass
        # TODO: add validate equality before process

        # self.event_schedules.filter(is_auto_generated=True).delete()

        master_user = self.master_user
        instrument_type = self.instrument_type
        instrument_class = instrument_type.instrument_class
        try:
            event_schedule_config = master_user.instrument_event_schedule_config
        except ObjectDoesNotExist:
            event_schedule_config = EventScheduleConfig.create_default(master_user=master_user)

        events = list(self.event_schedules.prefetch_related('actions').filter(is_auto_generated=True))
        events_by_accrual = {e.accrual_calculation_schedule_id: e for e in events
                             if e.accrual_calculation_schedule_id is not None}
        events_by_factor = {e.factor_schedule_id: e for e in events
                            if e.factor_schedule_id is not None}

        processed = []

        # process accruals
        accruals = list(self.accrual_calculation_schedules.order_by('accrual_start_date'))
        for i, accrual in enumerate(accruals):
            try:
                accrual_next = accruals[i + 1]
            except IndexError:
                accrual_next = None

            if instrument_class.has_regular_event:
                if instrument_type.regular_event:
                    e = EventSchedule()
                    e.instrument = self
                    e.accrual_calculation_schedule = accrual
                    e.is_auto_generated = True
                    e.name = event_schedule_config.name
                    e.description = event_schedule_config.description
                    e.event_class_id = EventClass.REGULAR
                    e.notification_class = event_schedule_config.notification_class
                    e.effective_date = accrual.first_payment_date
                    e.notify_in_n_days = event_schedule_config.notify_in_n_days
                    e.periodicity = accrual.periodicity
                    e.periodicity_n = accrual.periodicity_n
                    e.final_date = accrual_next.accrual_start_date if accrual_next else self.maturity_date

                    a = EventScheduleAction()
                    a.text = event_schedule_config.action_text
                    a.transaction_type = instrument_type.regular_event
                    a.is_sent_to_pending = event_schedule_config.action_is_sent_to_pending
                    a.is_book_automatic = event_schedule_config.action_is_book_automatic
                    a.button_position = 1

                    eold = events_by_accrual.get(accrual.id, None)
                    self._event_save(processed, e, a, eold)
                else:
                    raise ValueError('Field regular event in instrument type "%s" must be set' % instrument_type)

        if instrument_class.has_one_off_event:
            if instrument_type.one_off_event:
                e = EventSchedule()
                e.instrument = self
                e.is_auto_generated = True
                e.name = event_schedule_config.name
                e.description = event_schedule_config.description
                e.event_class_id = EventClass.ONE_OFF
                e.notification_class = event_schedule_config.notification_class
                e.effective_date = self.maturity_date
                e.notify_in_n_days = event_schedule_config.notify_in_n_days
                e.final_date = self.maturity_date

                a = EventScheduleAction()
                a.text = event_schedule_config.action_text
                a.transaction_type = instrument_type.one_off_event
                a.is_sent_to_pending = event_schedule_config.action_is_sent_to_pending
                a.is_book_automatic = event_schedule_config.action_is_book_automatic
                a.button_position = 1

                eold = None
                for e0 in events:
                    if e0.is_auto_generated and e0.event_class_id == EventClass.ONE_OFF and \
                                    e0.accrual_calculation_schedule_id is None and e0.factor_schedule_id is None:
                        eold = e0
                        break
                self._event_save(processed, e, a, eold)
            else:
                raise ValueError('Field one-off event in instrument type "%s" must be set' % instrument_type)

        # process factors
        factors = list(self.factor_schedules.order_by('effective_date'))
        for i, f in enumerate(factors):
            if i == 0:
                continue
            try:
                fprev = factors[i - 1]
            except IndexError:
                fprev = None

            if isclose(f.factor_value, fprev.factor_value):
                transaction_type = instrument_type.factor_same
                if transaction_type is None:
                    continue
                    # raise ValueError('Field "factor same"  in instrument type "%s" must be set' % instrument_type)
            elif f.factor_value > fprev.factor_value:
                transaction_type = instrument_type.factor_up
                if transaction_type is None:
                    continue
                    # raise ValueError('Fields "factor up" in instrument type "%s" must be set' % instrument_type)
            else:
                transaction_type = instrument_type.factor_down
                if transaction_type is None:
                    continue
                    # raise ValueError('Fields "factor down" in instrument type "%s" must be set' % instrument_type)

            e = EventSchedule()
            e.instrument = self
            e.is_auto_generated = True
            e.factor_schedule = f
            e.name = event_schedule_config.name
            e.description = event_schedule_config.description
            e.event_class_id = EventClass.ONE_OFF
            e.notification_class = event_schedule_config.notification_class
            e.effective_date = f.effective_date
            e.notify_in_n_days = event_schedule_config.notify_in_n_days
            e.final_date = f.effective_date

            a = EventScheduleAction()
            a.text = event_schedule_config.action_text
            a.transaction_type = transaction_type
            a.is_sent_to_pending = event_schedule_config.action_is_sent_to_pending
            a.is_book_automatic = event_schedule_config.action_is_book_automatic
            a.button_position = 1

            eold = events_by_factor.get(f.id, None)
            self._event_save(processed, e, a, eold)

        self.event_schedules.filter(is_auto_generated=True).exclude(pk__in=processed).delete()

    def _event_to_dict(self, event, event_actions=None):
        # build dict from attrs for compare its
        if event is None:
            return None
        event_values = serializers.serialize("python", [event])[0]
        if event_actions is None and hasattr(event, 'actions'):
            event_actions = event_actions or event.actions.all()
        event_values['fields']['actions'] = serializers.serialize("python", event_actions)
        event_values.pop('pk')
        for action_values in event_values['fields']['actions']:
            action_values.pop('pk')
            action_values['fields'].pop('event_schedule')
        return event_values

    def _event_is_equal(self, event, event_actions, old_event, old_event_actions):
        # compare action by all attrs
        es = self._event_to_dict(event, event_actions)
        eolds = self._event_to_dict(old_event, old_event_actions)
        return es == eolds

    def _event_save(self, processed, event, event_action, old_event):
        # compare action by all attrs
        if not self._event_is_equal(event, [event_action], old_event, None):
            event.save()
            event_action.event_schedule = event
            event_action.save()
            processed.append(event.id)
        else:
            if old_event:
                processed.append(old_event.id)

    def find_accrual(self, d, accruals=None):
        if accruals is None:
            # TODO: verify that use queryset cache
            accruals = self.accrual_calculation_schedules.select_related(
                'periodicity', 'accrual_calculation_model'
            ).order_by('accrual_start_date').all()
        accrual = None
        for a in accruals:
            if a.accrual_start_date <= d:
                accrual = a
        return accrual

    # def find_factor(self, d, factors=None):
    #     if factors is None:
    #         # TODO: verify that use queryset cache
    #         factors = self.factor_schedules.order_by('effective_date').all()
    #     factor = None
    #     for f in factors:
    #         if f.effective_date <= d:
    #             factor = f
    #     return factor

    def calculate_prices_accrued_price(self, begin_date=None, end_date=None):
        accruals = [a for a in self.accrual_calculation_schedules.order_by('accrual_start_date')]
        if not accruals:
            return
        existed_prices = PriceHistory.objects.filter(instrument=self, date__range=(begin_date, end_date))
        if begin_date is None and end_date is None:
            # used from admin
            for price in existed_prices:
                if price.date >= self.maturity_date:
                    continue
                accrued_price = self.get_accrued_price(price.date, accruals)
                if accrued_price is None:
                    accrued_price = 0.0
                price.accrued_price = accrued_price
                price.save(update_fields=['accrued_price'])
        else:
            existed_prices = {(p.pricing_policy_id, p.date): p for p in existed_prices}
            for pp in PricingPolicy.objects.filter(master_user=self.master_user):
                for dt in rrule.rrule(rrule.DAILY, dtstart=begin_date, until=end_date):
                    d = dt.date()
                    if d >= self.maturity_date:
                        continue
                    price = existed_prices.get((pp.id, d), None)
                    accrued_price = self.get_accrued_price(d, accruals)
                    if price is None:
                        if accrued_price is not None:
                            price = PriceHistory()
                            price.instrument = self
                            price.pricing_policy = pp
                            price.date = d
                            price.accrued_price = accrued_price
                            price.save()
                    else:
                        if accrued_price is None:
                            accrued_price = 0.0
                        price.accrued_price = accrued_price
                        price.save(update_fields=['accrued_price'])

    def get_accrued_price(self, price_date, accruals=None):
        from poms.common.formula_accruals import coupon_accrual_factor
        accrual = self.find_accrual(price_date, accruals=accruals)
        if accrual is None:
            return None
        factor = coupon_accrual_factor(accrual_calculation_schedule=accrual,
                                       dt1=accrual.accrual_start_date,
                                       dt2=price_date,
                                       dt3=accrual.first_payment_date)
        return accrual.accrual_size * factor


class InstrumentUserObjectPermission(AbstractUserObjectPermission):
    content_object = models.ForeignKey(Instrument, related_name='user_object_permissions',
                                       verbose_name=ugettext_lazy('content object'))

    class Meta(AbstractUserObjectPermission.Meta):
        verbose_name = ugettext_lazy('instruments - user permission')
        verbose_name_plural = ugettext_lazy('instruments - user permissions')


class InstrumentGroupObjectPermission(AbstractGroupObjectPermission):
    content_object = models.ForeignKey(Instrument, related_name='group_object_permissions',
                                       verbose_name=ugettext_lazy('content object'))

    class Meta(AbstractGroupObjectPermission.Meta):
        verbose_name = ugettext_lazy('instruments - group permission')
        verbose_name_plural = ugettext_lazy('instruments - group permissions')


class InstrumentAttributeType(AbstractAttributeType):
    # classifier_root = models.OneToOneField(
    #     InstrumentClassifier,
    #     on_delete=models.PROTECT,
    #     null=True,
    #     blank=True,
    #     verbose_name=ugettext_lazy('classifier')
    # )

    class Meta(AbstractAttributeType.Meta):
        verbose_name = ugettext_lazy('instrument attribute type')
        verbose_name_plural = ugettext_lazy('instrument attribute types')
        permissions = [
            ('view_instrumentattributetype', 'Can view instrument attribute type'),
            ('manage_instrumentattributetype', 'Can manage instrument attribute type'),
        ]


class InstrumentAttributeTypeUserObjectPermission(AbstractUserObjectPermission):
    content_object = models.ForeignKey(InstrumentAttributeType, related_name='user_object_permissions',
                                       verbose_name=ugettext_lazy('content object'))

    class Meta(AbstractUserObjectPermission.Meta):
        verbose_name = ugettext_lazy('instrument attribute types - user permission')
        verbose_name_plural = ugettext_lazy('instrument attribute types - user permissions')


class InstrumentAttributeTypeGroupObjectPermission(AbstractGroupObjectPermission):
    content_object = models.ForeignKey(InstrumentAttributeType, related_name='group_object_permissions',
                                       verbose_name=ugettext_lazy('content object'))

    class Meta(AbstractGroupObjectPermission.Meta):
        verbose_name = ugettext_lazy('instrument attribute types - group permission')
        verbose_name_plural = ugettext_lazy('instrument attribute types - group permissions')


@python_2_unicode_compatible
class InstrumentClassifier(AbstractClassifier):
    attribute_type = models.ForeignKey(InstrumentAttributeType, related_name='classifiers',
                                       verbose_name=ugettext_lazy('attribute type'))
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True,
                            verbose_name=ugettext_lazy('parent'))

    class Meta(AbstractClassifier.Meta):
        verbose_name = ugettext_lazy('instrument classifier')
        verbose_name_plural = ugettext_lazy('instrument classifiers')


class InstrumentAttributeTypeOption(AbstractAttributeTypeOption):
    member = models.ForeignKey(Member, related_name='instrument_attribute_type_options',
                               verbose_name=ugettext_lazy('member'))
    attribute_type = models.ForeignKey(InstrumentAttributeType, related_name='options',
                                       verbose_name=ugettext_lazy('attribute type'))

    class Meta(AbstractAttributeTypeOption.Meta):
        verbose_name = ugettext_lazy('instrument attribute types - option')
        verbose_name_plural = ugettext_lazy('instrument attribute types - options')


class InstrumentAttribute(AbstractAttribute):
    attribute_type = models.ForeignKey(InstrumentAttributeType, related_name='attributes',
                                       verbose_name=ugettext_lazy('attribute type'))
    content_object = models.ForeignKey(Instrument, related_name='attributes',
                                       verbose_name=ugettext_lazy('content object'))
    classifier = models.ForeignKey(InstrumentClassifier, on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name=ugettext_lazy('classifier'))

    class Meta(AbstractAttribute.Meta):
        verbose_name = ugettext_lazy('instrument attribute')
        verbose_name_plural = ugettext_lazy('instrument attributes')


@python_2_unicode_compatible
class ManualPricingFormula(models.Model):
    instrument = models.ForeignKey(Instrument, related_name='manual_pricing_formulas',
                                   verbose_name=ugettext_lazy('instrument'))
    pricing_policy = models.ForeignKey(PricingPolicy, on_delete=models.PROTECT, related_name='manual_pricing_formulas',
                                       verbose_name=ugettext_lazy('pricing policy'))
    expr = models.CharField(max_length=255, blank=True, default='', verbose_name=ugettext_lazy('expression'))
    notes = models.TextField(blank=True, default='', verbose_name=ugettext_lazy('notes'))

    class Meta:
        verbose_name = ugettext_lazy('manual pricing formula')
        verbose_name_plural = ugettext_lazy('manual pricing formulas')
        unique_together = [
            ['instrument', 'pricing_policy']
        ]
        ordering = ['pricing_policy']

    def __str__(self):
        return self.expr


@python_2_unicode_compatible
class PriceHistory(models.Model):
    instrument = models.ForeignKey(Instrument, related_name='prices', verbose_name=ugettext_lazy('instrument'))
    pricing_policy = models.ForeignKey(PricingPolicy, on_delete=models.PROTECT, null=True, blank=True,
                                       verbose_name=ugettext_lazy('pricing policy'))
    date = models.DateField(db_index=True, default=date_now, verbose_name=ugettext_lazy('date'))
    principal_price = models.FloatField(default=0.0, verbose_name=ugettext_lazy('principal price'))
    accrued_price = models.FloatField(default=0.0, verbose_name=ugettext_lazy('accrued price'))

    class Meta:
        verbose_name = ugettext_lazy('price history')
        verbose_name_plural = ugettext_lazy('price histories')
        unique_together = (
            ('instrument', 'pricing_policy', 'date',)
        )
        ordering = ['date']

    def __str__(self):
        # return '%s/%s@%s,%s,%s' % (
        #     self.instrument, self.pricing_policy, self.date, self.principal_price, self.accrued_price)
        return '%s:%s:%s:%s:%s' % (
            self.instrument_id, self.pricing_policy_id, self.date, self.principal_price, self.accrued_price)

        # def find_accrual(self, accruals=None):
        #     return self.instrument.find_accrual(self.date, accruals=accruals)
        #
        # def calculate_accrued_price(self, accrual=None, accruals=None, save=False):
        #     if accrual is None:
        #         accrual = self.find_accrual(accruals=accruals)
        #     old_accrued_price = self.accrued_price
        #     if accrual is None:
        #         self.accrued_price = 0.
        #     else:
        #         from poms.common.formula_accruals import coupon_accrual_factor
        #         factor = coupon_accrual_factor(accrual_calculation_schedule=accrual,
        #                                        dt1=accrual.accrual_start_date,
        #                                        dt2=self.date,
        #                                        dt3=accrual.first_payment_date)
        #         self.accrued_price = accrual.accrual_size * factor
        #     if save and not isclose(old_accrued_price, self.accrued_price):
        #         self.save(update_fields=['accrued_price'])


@python_2_unicode_compatible
class AccrualCalculationSchedule(models.Model):
    instrument = models.ForeignKey(Instrument, related_name='accrual_calculation_schedules',
                                   verbose_name=ugettext_lazy('instrument'))
    accrual_start_date = models.DateField(default=date_now, verbose_name=ugettext_lazy('accrual start date'))
    first_payment_date = models.DateField(default=date_now, verbose_name=ugettext_lazy('first payment date'))
    # TODO: is %
    accrual_size = models.FloatField(default=0.0, verbose_name=ugettext_lazy('accrual size'))
    accrual_calculation_model = models.ForeignKey(AccrualCalculationModel, on_delete=models.PROTECT,
                                                  verbose_name=ugettext_lazy('accrual calculation model'))
    periodicity = models.ForeignKey(Periodicity, on_delete=models.PROTECT, null=True, blank=True,
                                    verbose_name=ugettext_lazy('periodicity'))
    periodicity_n = models.IntegerField(default=0, verbose_name=ugettext_lazy('periodicity n'))
    notes = models.TextField(blank=True, default='', verbose_name=ugettext_lazy('notes'))

    class Meta:
        verbose_name = ugettext_lazy('accrual calculation schedule')
        verbose_name_plural = ugettext_lazy('accrual calculation schedules')
        ordering = ['accrual_start_date']

    def __str__(self):
        return '%s @ %s' % (self.instrument_id, self.accrual_start_date)


@python_2_unicode_compatible
class InstrumentFactorSchedule(models.Model):
    instrument = models.ForeignKey(Instrument, related_name='factor_schedules',
                                   verbose_name=ugettext_lazy('instrument'))
    effective_date = models.DateField(default=date_now, verbose_name=ugettext_lazy('effective date'))
    factor_value = models.FloatField(default=0., verbose_name=ugettext_lazy('factor value'))

    class Meta:
        verbose_name = ugettext_lazy('instrument factor schedule')
        verbose_name_plural = ugettext_lazy('instrument factor schedules')
        ordering = ['effective_date']

    def __str__(self):
        return '%s @ %s' % (self.instrument_id, self.effective_date)


class EventSchedule(models.Model):
    instrument = models.ForeignKey(Instrument, related_name='event_schedules', verbose_name=ugettext_lazy('instrument'))

    # T O D O: name & description is expression
    # T O D O: default settings.POMS_EVENT_*
    name = models.CharField(max_length=255, verbose_name=ugettext_lazy('name'))
    description = models.TextField(blank=True, default='', verbose_name=ugettext_lazy('description'))

    event_class = models.ForeignKey('transactions.EventClass', on_delete=models.PROTECT,
                                    verbose_name=ugettext_lazy('event class'))

    # T O D O: add to MasterUser defaults
    notification_class = models.ForeignKey('transactions.NotificationClass', on_delete=models.PROTECT,
                                           verbose_name=ugettext_lazy('notification class'))

    # TODO: is first_payment_date for regular
    # TODO: is instrument.maturity for one-off
    effective_date = models.DateField(null=True, blank=True, verbose_name=ugettext_lazy('effective date'))
    notify_in_n_days = models.PositiveIntegerField(default=0)

    periodicity = models.ForeignKey(Periodicity, null=True, blank=True, on_delete=models.PROTECT)
    periodicity_n = models.IntegerField(default=0)
    # TODO: =see next accrual_calculation_schedule.accrual_start_date or instrument.maturity_date (if last)
    final_date = models.DateField(default=date.max)

    is_auto_generated = models.BooleanField(default=False)
    accrual_calculation_schedule = models.ForeignKey(AccrualCalculationSchedule, null=True, blank=True, editable=False,
                                                     related_name='event_schedules',
                                                     help_text=ugettext_lazy(
                                                         'Used for store link when is_auto_generated is True'))
    factor_schedule = models.ForeignKey(InstrumentFactorSchedule, null=True, blank=True, editable=False,
                                        related_name='event_schedules',
                                        help_text=ugettext_lazy('Used for store link when is_auto_generated is True'))

    class Meta:
        verbose_name = ugettext_lazy('event schedule')
        verbose_name_plural = ugettext_lazy('event schedules')
        ordering = ['effective_date']

    def __str__(self):
        return self.name


class EventScheduleAction(models.Model):
    # TODO: for auto generated always one
    event_schedule = models.ForeignKey(EventSchedule, related_name='actions',
                                       verbose_name=ugettext_lazy('event schedule'))
    transaction_type = models.ForeignKey('transactions.TransactionType', on_delete=models.PROTECT)
    # T O D O: on auto generate fill 'Book: ' + transaction_type
    text = models.CharField(max_length=100, blank=True, default='')
    # T O D O: add to MasterUser defaults
    is_sent_to_pending = models.BooleanField(default=True)
    # T O D O: add to MasterUser defaults
    # T O D O: rename to: is_book_automatic (used when now notification)
    is_book_automatic = models.BooleanField(default=True)
    button_position = models.IntegerField(default=0)

    class Meta:
        verbose_name = ugettext_lazy('event schedule action')
        verbose_name_plural = ugettext_lazy('event schedule actions')
        ordering = ['is_book_automatic', 'button_position']

    def __str__(self):
        return self.text


class GeneratedEvent(models.Model):
    NEW = 1
    IGNORED = 2
    BOOK_PENDING = 3
    BOOKED = 4
    STATUS_CHOICES = (
        (NEW, ugettext_lazy('New')),
        (IGNORED, ugettext_lazy('Ignored')),
        (BOOK_PENDING, ugettext_lazy('Book pending')),
        (BOOKED, ugettext_lazy('Booked')),
    )

    master_user = models.ForeignKey(MasterUser, related_name='+')

    effective_date = models.DateField(default=date_now, db_index=True)
    notification_date = models.DateField(default=date_now, db_index=True)

    status = models.PositiveSmallIntegerField(default=NEW, choices=STATUS_CHOICES, db_index=True)
    event_schedule = models.ForeignKey(EventSchedule, null=True, blank=True, on_delete=models.SET_NULL,
                                       related_name='+')

    instrument = models.ForeignKey('instruments.Instrument', null=True, blank=True, on_delete=models.SET_NULL)
    portfolio = models.ForeignKey('portfolios.Portfolio', null=True, blank=True, on_delete=models.SET_NULL)
    account = models.ForeignKey('accounts.Account', null=True, blank=True, on_delete=models.SET_NULL)
    strategy1 = models.ForeignKey('strategies.Strategy1', null=True, blank=True, on_delete=models.SET_NULL)
    strategy2 = models.ForeignKey('strategies.Strategy2', null=True, blank=True, on_delete=models.SET_NULL)
    strategy3 = models.ForeignKey('strategies.Strategy3', null=True, blank=True, on_delete=models.SET_NULL)
    position = models.FloatField(default=0.0)

    action_text = models.TextField(default='', blank=True)
    action = models.ForeignKey(EventScheduleAction, null=True, blank=True, on_delete=models.SET_NULL,
                               related_name='+')
    transaction_type = models.ForeignKey('transactions.TransactionType', null=True, blank=True,
                                         on_delete=models.SET_NULL, related_name='+')
    member = models.ForeignKey('users.Member', null=True, blank=True)
    status_modified = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        abstract = True
        verbose_name = ugettext_lazy('generated event')
        verbose_name_plural = ugettext_lazy('generated events')
        ordering = ['date']

    def __str__(self):
        return self.action_text


class EventScheduleConfig(models.Model):
    master_user = models.OneToOneField('users.MasterUser', related_name='instrument_event_schedule_config',
                                       verbose_name=ugettext_lazy('master user'))

    name = models.CharField(max_length=255, blank=True, default='', verbose_name=ugettext_lazy('name'))
    description = models.CharField(max_length=255, blank=True, default='', verbose_name=ugettext_lazy('description'))
    notification_class = models.ForeignKey('transactions.NotificationClass', null=True, blank=True,
                                           on_delete=models.PROTECT, verbose_name=ugettext_lazy('notification class'))
    notify_in_n_days = models.PositiveSmallIntegerField(default=0, verbose_name=ugettext_lazy('notify in N days'))
    action_text = models.CharField(max_length=255, blank=True, default='', verbose_name=ugettext_lazy('action text'))
    action_is_sent_to_pending = models.BooleanField(default=True)
    action_is_book_automatic = models.BooleanField(default=True)

    class Meta:
        verbose_name = ugettext_lazy('event schedule config')
        verbose_name_plural = ugettext_lazy('event schedule configs')

    def __str__(self):
        return ugettext('event schedule config')

    @staticmethod
    def create_default(master_user):
        from poms.transactions.models import NotificationClass
        return EventScheduleConfig.objects.create(
            master_user=master_user,
            name="''",
            description="''",
            notification_class_id=NotificationClass.DONT_REACT,
            action_text="''",
        )
