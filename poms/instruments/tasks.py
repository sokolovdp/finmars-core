import logging
from datetime import timedelta, date

from celery import shared_task
from django.conf import settings
from django.db.models import F, Count

from poms.common.utils import date_now
from poms.instruments.models import EventSchedule, Instrument
from poms.reports.backends.balance import BalanceReport2PositionBuilder
from poms.reports.models import BalanceReport
from poms.transactions.models import EventClass, NotificationClass
from poms.users.models import MasterUser

_l = logging.getLogger('poms.instruments')


def calculate_prices_accrued_price(master_user, begin_date, end_date, instruments=None):
    _l.debug('process_events')
    instruments_qs = Instrument.objects.filter(master_user=master_user)
    if instruments:
        instruments_qs = instruments_qs.filter(pk__in=instruments)
    processed = []
    for instrument in instruments_qs:
        instrument.calculate_prices_accrued_price(begin_date, end_date)
        processed.append(instrument)
    _l.debug('processed: %s', len(processed))
    return processed


@shared_task(name='instruments.calculate_prices_accrued_price', ignore_result=True)
def calculate_prices_accrued_price_async(master_user, begin_date, end_date):
    # TODO: type conversion
    # calculate_prices_accrued_price(master_user, begin_date, end_date)
    pass


def process_events(instruments=None):
    _l.debug('process_events')

    now = date_now()

    master_user_qs = MasterUser.objects.annotate(
        transactions__count=Count('transactions', distinct=True)
    ).filter(transactions__transaction_date__lte=now, transactions__count__gt=0)
    if instruments:
        master_user_qs = master_user_qs.filter(instruments__in=instruments)

    _l.debug('master_user: count=%s', master_user_qs.count())
    for master_user in master_user_qs:
        # TODO: need cost_method to build report
        report = BalanceReport(master_user=master_user, begin_date=date.min, end_date=now,
                               use_portfolio=True, use_account=True, use_strategy=True, show_transaction_details=False,
                               cost_method=None)
        _l.debug('build position report: %s', report)
        # builder = BalanceReport2PositionBuilder(instance=report)
        # builder.build()

        for i in report.items:
            # if i.instrument:
            #     instruments_opened.add(i.instrument.id)
            pass

    event_schedule_qs = EventSchedule.objects.select_related(
        'instrument', 'instrument__master_user', 'event_class', 'notification_class', 'periodicity'
    ).prefetch_related(
        'actions', 'actions__transaction_type'
    ).filter(
        effective_date__lte=(now + F("notify_in_n_days")),
        final_date__gte=now
    ).exclude(
        notification_class__in=[NotificationClass.DONT_REACT]
    ).order_by(
        'instrument__master_user__id', 'instrument__id'
    )
    if instruments:
        event_schedule_qs = event_schedule_qs.filter(instrument__in=instruments)

    _l.debug('event_schedule: count=%s', event_schedule_qs.count())
    for event_schedule in event_schedule_qs:
        instrument = event_schedule.instrument
        master_user = instrument.master_user

        _l.debug(
            'master_user=%s, instrument=%s, event_schedule=%s, event_class=%s, notification_class=%s, periodicity=%s',
            master_user.id, instrument.id, event_schedule.id, event_schedule.event_class,
            event_schedule.notification_class, event_schedule.periodicity)

        notification_date_correction = timedelta(days=event_schedule.notify_in_n_days)

        is_complies = False
        effective_date = None
        notification_date = None

        if event_schedule.event_class_id == EventClass.ONE_OFF:
            effective_date = event_schedule.effective_date
            notification_date = effective_date - notification_date_correction
            _l.debug('effective_date=%s, notification_date=%s', effective_date, notification_date)

            if notification_date == now or effective_date == now:
                is_complies = True

        elif event_schedule.event_class_id == EventClass.REGULAR:
            for i in range(0, settings.INSTRUMENT_EVENTS_REGULAR_MAX_INTERVALS):
                effective_date = event_schedule.effective_date + event_schedule.periodicity.to_timedelta(
                    i, same_date=event_schedule.effective_date)
                notification_date = effective_date - notification_date_correction
                _l.debug('i=%s, book_date=%s, notify_date=%s', i, effective_date, notification_date)

                if effective_date > event_schedule.final_date:
                    break
                if effective_date < now:
                    continue
                if notification_date > now and effective_date > now:
                    break

                if notification_date == now or effective_date == now:
                    is_complies = True
                    break

        if is_complies:
            notification_class = event_schedule.notification_class
            need_inform, need_react, apply_def = notification_class.check_date(now, effective_date, notification_date)

            if need_inform:
                _l.info('need_inform !!!!')

            if need_react:
                _l.info('need_react !!!!')

            if apply_def:
                _l.info('apply_def !!!!')

    _l.debug('finished')


@shared_task(name='instruments.process_events_auto', ignore_result=True)
def process_events_auto():
    process_events()
