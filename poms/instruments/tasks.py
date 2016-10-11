import logging
from datetime import timedelta

from celery import shared_task
from django.db.models import F

from poms.common.utils import date_now
from poms.instruments.models import EventSchedule, Instrument
from poms.transactions.models import EventClass, NotificationClass

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
        action_qs = event_schedule_qs.filter(instrument__in=instruments)

    _l.debug('count=%s', event_schedule_qs.count())
    for event_schedule in event_schedule_qs:
        instrument = event_schedule.instrument
        master_user = instrument.master_user

        _l.debug(
            'master_user=%s, instrument=%s, event_schedule=%s, event_class=%s, notification_class=%s, periodicity=%s',
            master_user.id, instrument.id, event_schedule.id, event_schedule.event_class,
            event_schedule.notification_class, event_schedule.periodicity)

        notify_correction = timedelta(days=event_schedule.notify_in_n_days)

        is_complies = False
        book_date = None
        notify_date = None

        if event_schedule.event_class_id == EventClass.ONE_OFF:
            book_date = event_schedule.effective_date
            notify_date = book_date - notify_correction
            _l.info('book_date=%s, notify_date=%s', book_date, notify_date)

            if notify_date == now or book_date == now:
                is_complies = True

        elif event_schedule.event_class_id == EventClass.REGULAR:
            for i in range(0, 1000):
                book_date = event_schedule.effective_date + event_schedule.periodicity.to_timedelta(
                    i, same_date=event_schedule.effective_date)
                notify_date = book_date - notify_correction
                _l.info('i=%s, book_date=%s, notify_date=%s', i, book_date, notify_date)

                if book_date > event_schedule.final_date:
                    break
                if book_date < now:
                    continue
                if notify_date > now and book_date > now:
                    break

                if notify_date == now or book_date == now:
                    is_complies = True
                    break

        if is_complies:
            if notify_date == now:
                _l.debug('notify !!!')
            if book_date == now:
                _l.debug('book !!!')
            pass

    _l.debug('finished')


@shared_task(name='instruments.process_events', ignore_result=True)
def process_events_async():
    process_events()
