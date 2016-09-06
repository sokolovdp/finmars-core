from __future__ import unicode_literals

import math
from datetime import date

from dateutil import relativedelta, rrule
from django.core import serializers
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
        (NONE, 'NONE', _("none")),
        (ACT_ACT, 'ACT_ACT', _("ACT/ACT")),
        (ACT_ACT_ISDA, 'ACT_ACT_ISDA', _("ACT/ACT - ISDA")),
        (ACT_360, 'ACT_360', _("ACT/360")),
        (ACT_365, 'ACT_365', _("ACT/365")),
        (ACT_365_25, 'ACT_365_25', _("Act/365.25")),
        (ACT_365_366, 'ACT_365_366', _("Act/365(366)")),
        (ACT_1_365, 'ACT_1_365', _("Act+1/365")),
        (ACT_1_360, 'ACT_1_360', _("Act+1/360")),
        # (C_30_ACT, 'C_30_ACT', _("30/ACT")),
        (C_30_360, 'C_30_360', _("30/360")),
        (C_30_360_NO_EOM, 'C_30_360_NO_EOM', _("30/360 (NO EOM)")),
        (C_30E_P_360_ITL, 'C_30E_P_360_ITL', _("30E+/360.ITL")),
        (NL_365, 'NL_365', _("NL/365")),
        (NL_365_NO_EOM, 'NL_365_NO_EOM', _("NL/365 (NO-EOM)")),
        (ISMA_30_360, 'ISMA_30_360', _("ISMA-30/360")),
        (ISMA_30_360_NO_EOM, 'ISMA_30_360_NO_EOM', _("ISMA-30/360 (NO EOM)")),
        (US_MINI_30_360_EOM, 'US_MINI_30_360_EOM', _("US MUNI-30/360 (EOM)")),
        (US_MINI_30_360_NO_EOM, 'US_MINI_30_360_NO_EOM', _("US MUNI-30/360 (NO EOM)")),
        (BUS_DAYS_252, 'BUS_DAYS_252', _("BUS DAYS/252")),
        (GERMAN_30_360_EOM, 'GERMAN_30_360_EOM', _("GERMAN-30/360 (EOM)")),
        (GERMAN_30_360_NO_EOM, 'GERMAN_30_360_NO_EOM', _("GERMAN-30/360 (NO EOM)")),
        (REVERSED_ACT_365, 'REVERSED_ACT_365', _("Reversed ACT/365")),
        (C_30E_P_360, 'C_30E_P_360', _('30E+/360'))
    )

    class Meta(AbstractClassModel.Meta):
        verbose_name = _('accrual calculation model')
        verbose_name_plural = _('accrual calculation models')


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
        (N_DAY, 'N_DAY', _("N Days")),
        (N_WEEK_EOBW, 'N_WEEK_EOBW', _("N Weeks (eobw)")),
        (N_MONTH_EOM, 'N_MONTH_EOM', _("N Months (eom)")),
        (N_MONTH_SAME_DAY, 'N_MONTH_SAME_DAY', _("N Months (same date)")),
        (N_YEAR_EOY, 'N_YEAR_EOY', _("N Years (eoy)")),
        (N_YEAR_SAME_DAY, 'N_YEAR_SAME_DAY', _("N Years (same date)")),

        (WEEKLY, 'WEEKLY', _('Weekly')),
        (MONTHLY, 'MONTHLY', _('Monthly')),
        (BIMONTHLY, 'BIMONTHLY', _('Bimonthly')),
        (QUARTERLY, 'QUARTERLY', _('Quarterly')),
        (SEMI_ANNUALLY, 'SEMI_ANNUALLY', _('Semi-annually')),
        (ANNUALLY, 'ANNUALLY', _('Annually')),
    )

    class Meta(AbstractClassModel.Meta):
        verbose_name = _('periodicity')
        verbose_name_plural = _('periodicities')

    @staticmethod
    def to_timedelta(periodicity, delta=None, same_date=None):
        if isinstance(periodicity, Periodicity):
            periodicity = periodicity.id

        if delta is None:
            delta = 1

        if periodicity == Periodicity.N_DAY:
            return relativedelta.relativedelta(days=delta)
        elif periodicity == Periodicity.N_WEEK_EOBW:
            # return relativedelta.relativedelta(days=7 * delta, weekday=relativedelta.FR)
            return relativedelta.relativedelta(weeks=delta, weekday=relativedelta.FR)
        elif periodicity == Periodicity.N_MONTH_EOM:
            return relativedelta.relativedelta(months=delta, day=31)
        elif periodicity == Periodicity.N_MONTH_SAME_DAY:
            return relativedelta.relativedelta(months=delta, day=same_date.day)
        elif periodicity == Periodicity.N_YEAR_EOY:
            return relativedelta.relativedelta(years=delta, month=12, day=31)
        elif periodicity == Periodicity.N_YEAR_SAME_DAY:
            return relativedelta.relativedelta(years=delta, month=same_date.month, day=same_date.day)
        elif periodicity == Periodicity.WEEKLY:
            return relativedelta.relativedelta(weeks=1 * delta)
        elif periodicity == Periodicity.MONTHLY:
            return relativedelta.relativedelta(months=1 * delta)
        elif periodicity == Periodicity.BIMONTHLY:
            return relativedelta.relativedelta(months=2 * delta)
        elif periodicity == Periodicity.QUARTERLY:
            return relativedelta.relativedelta(months=3 * delta)
        elif periodicity == Periodicity.SEMI_ANNUALLY:
            return relativedelta.relativedelta(months=6 * delta)
        elif periodicity == Periodicity.ANNUALLY:
            return relativedelta.relativedelta(years=1 * delta)
        return None

    @staticmethod
    def to_rrule(periodicity, dtstart=None, count=None, until=None):
        if isinstance(periodicity, Periodicity):
            periodicity = periodicity.id

        if periodicity == Periodicity.N_DAY:
            return rrule.rrule(dtstart=dtstart, count=count, until=until, freq=rrule.DAILY)
        elif periodicity == Periodicity.N_WEEK_EOBW:
            return rrule.rrule(dtstart=dtstart, count=count, until=until, freq=rrule.WEEKLY,
                               byweekday=[rrule.FR])
        elif periodicity == Periodicity.N_MONTH_EOM:
            raise ValueError()
        elif periodicity == Periodicity.N_MONTH_SAME_DAY:
            raise ValueError()
        elif periodicity == Periodicity.N_YEAR_EOY:
            raise ValueError()
        elif periodicity == Periodicity.N_YEAR_SAME_DAY:
            return rrule.rrule(dtstart=dtstart, count=count, until=until, freq=rrule.WEEKLY)
        elif periodicity == Periodicity.WEEKLY:
            return rrule.rrule(dtstart=dtstart, count=count, until=until, freq=rrule.WEEKLY)
        elif periodicity == Periodicity.MONTHLY:
            return rrule.rrule(dtstart=dtstart, count=count, until=until, freq=rrule.MONTHLY)
        elif periodicity == Periodicity.BIMONTHLY:
            return rrule.rrule(dtstart=dtstart, count=count, interval=2, until=until, freq=rrule.MONTHLY)
        elif periodicity == Periodicity.QUARTERLY:
            return rrule.rrule(dtstart=dtstart, count=count, interval=3, until=until, freq=rrule.MONTHLY)
        elif periodicity == Periodicity.SEMI_ANNUALLY:
            return rrule.rrule(dtstart=dtstart, count=count, interval=6, until=until, freq=rrule.MONTHLY)
        elif periodicity == Periodicity.ANNUALLY:
            return rrule.rrule(dtstart=dtstart, count=count, until=until, freq=rrule.YEARLY)
        return None

    @staticmethod
    def to_freq(periodicity):
        if isinstance(periodicity, Periodicity):
            periodicity = periodicity.id

        if periodicity == Periodicity.N_DAY:
            return 0
        elif periodicity == Periodicity.N_WEEK_EOBW:
            return 0
        elif periodicity == Periodicity.N_MONTH_EOM:
            return 0
        elif periodicity == Periodicity.N_MONTH_SAME_DAY:
            return 0
        elif periodicity == Periodicity.N_YEAR_EOY:
            return 0
        elif periodicity == Periodicity.N_YEAR_SAME_DAY:
            return 0
        elif periodicity == Periodicity.WEEKLY:
            return 52
        elif periodicity == Periodicity.MONTHLY:
            return 12
        elif periodicity == Periodicity.BIMONTHLY:
            return 6
        elif periodicity == Periodicity.QUARTERLY:
            return 4
        elif periodicity == Periodicity.SEMI_ANNUALLY:
            return 2
        elif periodicity == Periodicity.ANNUALLY:
            return 1
        return 0


class CostMethod(AbstractClassModel):
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
    expr = models.CharField(max_length=255, default='', blank=True, verbose_name=_('expression'))

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
                                      related_name='+', verbose_name=_('one-off event'))
    regular_event = models.ForeignKey('transactions.TransactionType', null=True, blank=True, on_delete=models.PROTECT,
                                      related_name='+', verbose_name=_('regular event'))

    factor_same = models.ForeignKey('transactions.TransactionType', null=True, blank=True, on_delete=models.PROTECT,
                                    related_name='+', verbose_name=_('factor same'))
    factor_up = models.ForeignKey('transactions.TransactionType', null=True, blank=True, on_delete=models.PROTECT,
                                  related_name='+', verbose_name=_('factor up'))
    factor_down = models.ForeignKey('transactions.TransactionType', null=True, blank=True, on_delete=models.PROTECT,
                                    related_name='+', verbose_name=_('factor down'))

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

    def rebuild_event_schedules(self):
        from poms.transactions.models import EventClass
        # TODO: add validate equality before process

        # self.event_schedules.filter(is_auto_generated=True).delete()

        master_user = self.master_user
        instrument_type = self.instrument_type
        instrument_class = instrument_type.instrument_class
        config = master_user.instrument_event_schedule_config

        events = list(self.event_schedules.prefetch_related('actions').filter(is_auto_generated=True))
        events_by_accrual = {e.accrual_calculation_schedule_id: e for e in events
                             if e.accrual_calculation_schedule_id is not None}
        events_by_factor = {e.factor_schedule_id: e for e in events
                            if e.factor_schedule_id is not None}

        processed = []

        def _to_dict(e, e_actions=None):
            if e is None:
                return None
            es = serializers.serialize("python", [e])[0]
            if e_actions is None and hasattr(e, 'actions'):
                e_actions = e_actions or e.actions.all()
            es['fields']['actions'] = serializers.serialize("python", e_actions)
            es.pop('pk')
            for a in es['fields']['actions']:
                a.pop('pk')
                a['fields'].pop('event_schedule')
            return es

        def _is_equal(e, e_actions, eold, eold_actions):
            es = _to_dict(e, e_actions)
            eolds = _to_dict(eold, eold_actions)
            return es == eolds

        def _e_save(e, eold):
            if not _is_equal(e, [a], eold, None):
                e.save()
                a.event_schedule = e
                a.save()
                processed.append(e.id)
            else:
                if eold:
                    processed.append(eold.id)

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
                    e.name = config.name
                    e.description = config.description
                    e.event_class_id = EventClass.REGULAR
                    e.notification_class = config.notification_class
                    e.effective_date = accrual.first_payment_date
                    e.notify_in_n_days = config.notify_in_n_days
                    e.periodicity = accrual.periodicity
                    e.periodicity_n = accrual.periodicity_n
                    e.final_date = accrual_next.accrual_start_date if accrual_next else self.maturity_date

                    a = EventScheduleAction()
                    a.text = config.action_text
                    a.transaction_type = instrument_type.regular_event
                    a.is_sent_to_pending = config.action_is_sent_to_pending
                    a.is_book_automatic = config.action_is_book_automatic
                    a.button_position = 1

                    eold = events_by_accrual.get(accrual.id, None)
                    # if not _is_equal(e, [a], eold, None):
                    #     e.save()
                    #     a.event_schedule = e
                    #     a.save()
                    #     updated_events.append(e.id)
                    # else:
                    #     if eold:
                    #         updated_events.append(eold.id)
                    _e_save(e, eold)
                else:
                    raise ValueError('Field regular event in instrument type "%s" must be set' % instrument_type)

        if instrument_class.has_one_off_event:
            if instrument_type.one_off_event:
                e = EventSchedule()
                e.instrument = self
                e.is_auto_generated = True
                e.name = config.name
                e.description = config.description
                e.event_class_id = EventClass.ONE_OFF
                e.notification_class = config.notification_class
                e.effective_date = self.maturity_date
                e.notify_in_n_days = config.notify_in_n_days
                e.final_date = self.maturity_date

                a = EventScheduleAction()
                a.text = config.action_text
                a.transaction_type = instrument_type.one_off_event
                a.is_sent_to_pending = config.action_is_sent_to_pending
                a.is_book_automatic = config.action_is_book_automatic
                a.button_position = 1

                eold = None
                for e0 in events:
                    if e0.is_auto_generated and e0.event_class_id == EventClass.ONE_OFF and \
                                    e0.accrual_calculation_schedule_id is None and e0.factor_schedule_id is None:
                        eold = e0
                        break
                # if not _is_equal(e, [a], eold, None):
                #     e.save()
                #     a.event_schedule = e
                #     a.save()
                #     updated_events.append(e.id)
                # else:
                #     if eold:
                #         updated_events.append(eold.id)
                _e_save(e, eold)
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

            if math.isclose(f.factor_value, fprev.factor_value):
                transaction_type = instrument_type.factor_same
                cmp = 1
            elif f.factor_value > fprev.factor_value:
                transaction_type = instrument_type.factor_up
                cmp = 2
            else:
                transaction_type = instrument_type.factor_down
                cmp = 3

            if transaction_type:
                e = EventSchedule()
                e.instrument = self
                e.is_auto_generated = True
                e.factor_schedule = f
                e.name = config.name
                e.description = config.description
                e.event_class_id = EventClass.ONE_OFF
                e.notification_class = config.notification_class
                e.effective_date = f.effective_date
                e.notify_in_n_days = config.notify_in_n_days
                e.final_date = f.effective_date

                a = EventScheduleAction()
                a.text = config.action_text
                a.transaction_type = transaction_type
                a.is_sent_to_pending = config.action_is_sent_to_pending
                a.is_book_automatic = config.action_is_book_automatic
                a.button_position = 1

                eold = events_by_factor.get(f.id, None)
                # if not _is_equal(e, [a], eold, None):
                #     e.save()
                #     a.event_schedule = e
                #     a.save()
                #     updated_events.append(e.id)
                # else:
                #     if eold:
                #         updated_events.append(eold.id)
                _e_save(e, eold)
            else:
                if cmp == 1:
                    raise ValueError(
                        'Field factor same  in instrument type "%s" must be set' % instrument_type)
                elif cmp == 2:
                    raise ValueError(
                        'Fields factor up in instrument type "%s" must be set' % instrument_type)
                elif cmp == 3:
                    raise ValueError(
                        'Fields factor down in instrument type "%s" must be set' % instrument_type)

        self.event_schedules.filter(is_auto_generated=True).exclude(pk__in=processed).delete()

    def find_accrual(self, some_date, accruals=None):
        if accruals is None:
            # TODO: verify that use queryset cache
            accruals = self.accrual_calculation_schedules.order_by('accrual_start_date').all()
        accrual = None
        for a in accruals:
            if a.accrual_start_date <= some_date:
                accrual = a
        return accrual

    def find_factor(self, some_date, factors=None):
        if factors is None:
            # TODO: verify that use queryset cache
            factors = self.factor_schedules.order_by('effective_date').all()
        factor = None
        for f in factors:
            if f.effective_date <= some_date:
                factor = f
        return factor

    def calculate_prices_accrued_price(self, save=False):
        accruals = [a for a in self.accrual_calculation_schedules.order_by('accrual_start_date')]
        for p in self.prices.order_by('date'):
            p.calculate_accrued_price(accruals=accruals, save=save)


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
    attribute_type = models.ForeignKey(InstrumentAttributeType, null=True, blank=True, related_name='classifiers',
                                       verbose_name=_('attribute type'))
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True,
                            verbose_name=_('parent'))

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
    content_object = models.ForeignKey(Instrument, related_name='attributes', verbose_name=_('content object'))
    classifier = models.ForeignKey(InstrumentClassifier, on_delete=models.PROTECT, null=True, blank=True,
                                   verbose_name=_('classifier'))

    class Meta(AbstractAttribute.Meta):
        verbose_name = _('instrument attribute')
        verbose_name_plural = _('instrument attributes')


@python_2_unicode_compatible
class ManualPricingFormula(models.Model):
    instrument = models.ForeignKey(Instrument, related_name='manual_pricing_formulas', verbose_name=_('instrument'))
    pricing_policy = models.ForeignKey(PricingPolicy, on_delete=models.PROTECT, related_name='manual_pricing_formulas',
                                       verbose_name=_('pricing policy'))
    expr = models.CharField(max_length=255, blank=True, default='', verbose_name=_('expression'))
    notes = models.TextField(blank=True, default='', verbose_name=_('notes'))

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
        # return '%s/%s@%s,%s,%s' % (
        #     self.instrument, self.pricing_policy, self.date, self.principal_price, self.accrued_price)
        return '%s:%s:%s:%s:%s' % (
            self.instrument_id, self.pricing_policy_id, self.date, self.principal_price, self.accrued_price)

    def find_accrual(self, accruals=None):
        return self.instrument.find_accrual(self.date, accruals=accruals)

    def calculate_accrued_price(self, accrual=None, accruals=None, save=False):
        if accrual is None:
            accrual = self.find_accrual(accruals=accruals)
        old_accrued_price = self.accrued_price
        if accrual is None:
            self.accrued_price = 0.
        else:
            from poms.common.formula_accruals import coupon_accrual_factor
            factor = coupon_accrual_factor(accrual_calculation_schedule=accrual,
                                           dt1=accrual.accrual_start_date,
                                           dt2=self.date,
                                           dt3=accrual.first_payment_date)
            self.accrued_price = accrual.accrual_size * factor
        if save and not math.isclose(old_accrued_price, self.accrued_price):
            self.save(update_fields=['accrued_price'])


@python_2_unicode_compatible
class AccrualCalculationSchedule(models.Model):
    instrument = models.ForeignKey(Instrument, related_name='accrual_calculation_schedules',
                                   verbose_name=_('instrument'))
    accrual_start_date = models.DateField(default=date_now, verbose_name=_('accrual start date'))
    first_payment_date = models.DateField(default=date_now, verbose_name=_('first payment date'))
    # TODO: is %
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

    # T O D O: name & description is expression
    # T O D O: default settings.POMS_EVENT_*
    name = models.CharField(max_length=255, verbose_name=_('name'))
    description = models.TextField(blank=True, default='', verbose_name=_('description'))

    event_class = models.ForeignKey('transactions.EventClass', on_delete=models.PROTECT, verbose_name=_('event class'))

    # T O D O: add to MasterUser defaults
    notification_class = models.ForeignKey('transactions.NotificationClass', on_delete=models.PROTECT,
                                           verbose_name=_('notification class'))

    # TODO: is first_payment_date for regular
    # TODO: is instrument.maturity for one-off
    effective_date = models.DateField(null=True, blank=True, verbose_name=_('effective date'))
    notify_in_n_days = models.PositiveIntegerField(default=0)

    periodicity = models.ForeignKey(Periodicity, null=True, blank=True, on_delete=models.PROTECT)
    periodicity_n = models.IntegerField(default=0)
    # TODO: =see next accrual_calculation_schedule.accrual_start_date or instrument.maturity_date (if last)
    final_date = models.DateField(default=date.max)

    is_auto_generated = models.BooleanField(default=False)
    accrual_calculation_schedule = models.ForeignKey(AccrualCalculationSchedule, null=True, blank=True, editable=False,
                                                     related_name='event_schedules',
                                                     help_text=_('Used for store link when is_auto_generated is True'))
    factor_schedule = models.ForeignKey(InstrumentFactorSchedule, null=True, blank=True, editable=False,
                                        related_name='event_schedules',
                                        help_text=_('Used for store link when is_auto_generated is True'))

    class Meta:
        verbose_name = _('event schedule')
        verbose_name_plural = _('event schedules')

    def __str__(self):
        return self.name


class EventScheduleAction(models.Model):
    # TODO: for auto generated always one
    event_schedule = models.ForeignKey(EventSchedule, related_name='actions', verbose_name=_('event schedule'))
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
        verbose_name = _('event schedule action')
        verbose_name_plural = _('event schedule actions')

    def __str__(self):
        return self.text


class EventScheduleConfig(models.Model):
    master_user = models.OneToOneField('users.MasterUser', related_name='instrument_event_schedule_config',
                                       verbose_name=_('master user'))

    name = models.CharField(max_length=255, blank=True, default='', verbose_name=_('name'))
    description = models.CharField(max_length=255, blank=True, default='', verbose_name=_('description'))
    notification_class = models.ForeignKey('transactions.NotificationClass', null=True, blank=True,
                                           on_delete=models.PROTECT, verbose_name=_('notification class'))
    notify_in_n_days = models.PositiveSmallIntegerField(default=0, verbose_name=_('notify in N days'))
    action_text = models.CharField(max_length=255, blank=True, default='', verbose_name=_('action text'))
    action_is_sent_to_pending = models.BooleanField(default=True)
    action_is_book_automatic = models.BooleanField(default=True)

    class Meta:
        verbose_name = _('event schedule config')
        verbose_name_plural = _('event schedule configs')

    def __str__(self):
        return 'event schedule config'
