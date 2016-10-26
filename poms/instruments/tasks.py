import logging
from collections import defaultdict
from datetime import timedelta, date

from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone

from poms import notifications
from poms.common.utils import date_now
from poms.instruments.models import EventSchedule, Instrument, CostMethod, GeneratedEvent
from poms.reports.backends.balance import BalanceReport2Builder
from poms.reports.models import BalanceReport
from poms.transactions.models import EventClass
from poms.users.models import MasterUser

_l = logging.getLogger('poms.instruments')


@transaction.atomic()
def calculate_prices_accrued_price(master_user=None, begin_date=None, end_date=None, instruments=None):
    _l.debug('process_events: master_user=%s, begin_date=%s, end_date=%s, instruments=%s',
             master_user, begin_date, end_date, instruments)
    instruments_qs = Instrument.objects.all()
    if master_user:
        instruments_qs = instruments_qs.filter(master_user=master_user)
    if instruments:
        instruments_qs = instruments_qs.filter(pk__in=instruments)
    _l.debug('instruments: count=%s', instruments_qs.count())
    for instrument in instruments_qs:
        _l.debug('calculate_prices_accrued_price: instrument=%s', instrument.id)
        instrument.calculate_prices_accrued_price(begin_date, end_date)


@shared_task(name='instruments.calculate_prices_accrued_price', ignore_result=False)
@transaction.atomic()
def calculate_prices_accrued_price_async(master_user=None, begin_date=None, end_date=None, instruments=None):
    if begin_date:
        begin_date = date.fromordinal(begin_date)
    if end_date:
        end_date = date.fromordinal(end_date)
    calculate_prices_accrued_price(master_user=master_user, begin_date=begin_date, end_date=end_date,
                                   instruments=instruments)


@shared_task(name='instruments.generate_events', ignore_result=True)
def generate_events(master_users=None):
    _l.debug('generate_events: master_users=%s', master_users)

    now = date_now()

    # TODO: need cost_method to build report
    cost_method = CostMethod.objects.get(pk=CostMethod.AVCO)

    master_user_qs = MasterUser.objects.all()
    if master_users:
        master_user_qs = master_user_qs.filter(pk__in=master_users)

    for master_user in master_user_qs:
        _l.debug('generate_events: master_user=%s', master_user.id)

        opened_instrument_items = []
        instruments_pk = set()
        report = BalanceReport(master_user=master_user, end_date=now, cost_method=cost_method, use_portfolio=True,
                               use_account=True, use_strategy1=True, use_strategy2=True, use_strategy3=True,
                               show_transaction_details=False)
        builder = BalanceReport2Builder(instance=report)
        builder.build()

        for item in report.items:
            if item.instrument:
                opened_instrument_items.append(item)
                instruments_pk.add(item.instrument.id)

        _l.debug('opened_instrument_items: count=%s', len(opened_instrument_items))
        if not opened_instrument_items:
            return

        event_schedule_qs = EventSchedule.objects.select_related(
            'instrument', 'instrument__master_user', 'event_class', 'notification_class', 'periodicity'
        ).prefetch_related(
            'actions', 'actions__transaction_type'
        ).filter(
            effective_date__lte=(now + F("notify_in_n_days")),
            final_date__gte=now
            # ).exclude(
            #     notification_class__in=[NotificationClass.DONT_REACT]
        ).order_by(
            'instrument__master_user__id', 'instrument__id'
        )
        event_schedule_qs = event_schedule_qs.filter(instrument__in=instruments_pk)

        event_schedule_cache = defaultdict(list)
        for event_schedule in event_schedule_qs:
            event_schedule_cache[event_schedule.instrument_id].append(event_schedule)

        for item in opened_instrument_items:
            portfolio = item.portfolio
            account = item.account
            strategy1 = item.strategy1
            strategy2 = item.strategy2
            strategy3 = item.strategy3
            instrument = item.instrument
            position = item.position

            event_schedules = event_schedule_cache.get(instrument.id) or []

            _l.debug('opened instrument: portfolio=%s, account=%s, strategy1=%s, strategy2=%s, strategy3=%s, '
                     'instrument=%s, position=%s, event_schedules=%s',
                     portfolio.id, account.id, strategy1.id, strategy2.id, strategy3.id,
                     instrument.id, position,[e.id for e in event_schedules])

            if not event_schedules:
                continue

            for event_schedule in event_schedules:
                _l.debug('event_schedule=%s, event_class=%s, notification_class=%s, periodicity=%s, n=%s',
                         event_schedule.id, event_schedule.event_class, event_schedule.notification_class,
                         event_schedule.periodicity, event_schedule.periodicity_n)

                notification_date_correction = timedelta(days=event_schedule.notify_in_n_days)

                is_complies = False
                effective_date = None
                notification_date = None

                if event_schedule.event_class_id == EventClass.ONE_OFF:
                    effective_date = event_schedule.effective_date
                    notification_date = effective_date - notification_date_correction
                    # _l.debug('effective_date=%s, notification_date=%s', effective_date, notification_date)

                    if notification_date == now or effective_date == now:
                        is_complies = True

                elif event_schedule.event_class_id == EventClass.REGULAR:
                    for i in range(0, settings.INSTRUMENT_EVENTS_REGULAR_MAX_INTERVALS):
                        effective_date = event_schedule.effective_date + event_schedule.periodicity.to_timedelta(
                            i, same_date=event_schedule.effective_date)
                        notification_date = effective_date - notification_date_correction
                        # _l.debug('i=%s, book_date=%s, notify_date=%s', i, effective_date, notification_date)

                        if effective_date > event_schedule.final_date:
                            break
                        if effective_date < now:
                            continue
                        if notification_date > now and effective_date > now:
                            break

                        if notification_date == now or effective_date == now:
                            is_complies = True
                            break

                _l.debug('is_complies=%s', is_complies)
                if is_complies:
                    ge_dup_qs = GeneratedEvent.objects.filter(
                        master_user=master_user,
                        event_schedule=event_schedule,
                        effective_date=effective_date,
                        notification_date=notification_date,
                        instrument=instrument,
                        portfolio=portfolio,
                        account=account,
                        strategy1=strategy1,
                        strategy2=strategy2,
                        strategy3=strategy3,
                        position=position
                    )
                    if ge_dup_qs.exists():
                        _l.debug('generated event already exist')
                        continue

                    generated_event = GeneratedEvent()
                    generated_event.master_user = master_user
                    generated_event.event_schedule = event_schedule
                    generated_event.status = GeneratedEvent.NEW
                    generated_event.status_modified = timezone.now()
                    generated_event.effective_date = effective_date
                    generated_event.notification_date = notification_date
                    generated_event.instrument = instrument
                    generated_event.portfolio = portfolio
                    generated_event.account = account
                    generated_event.strategy1 = strategy1
                    generated_event.strategy2 = strategy2
                    generated_event.strategy3 = strategy3
                    generated_event.position = position
                    generated_event.save()

    process_events.apply_async(kwargs={'master_users': master_users})

    _l.debug('finished')


@shared_task(name='instruments.process_events', ignore_result=True)
def process_events(master_users=None):
    from poms.instruments.handlers import GeneratedEventProcess

    _l.debug('process_events: master_users=%s', master_users)

    now = date_now()

    master_user_qs = MasterUser.objects.all()
    if master_users:
        master_user_qs = master_user_qs.filter(pk__in=master_users)

    for master_user in master_user_qs:
        _l.debug('process_events: master_user=%s', master_user.id)
        with transaction.atomic():
            generated_event_qs = GeneratedEvent.objects.filter(
                master_user=master_user,
                status=GeneratedEvent.NEW,
            ).filter(
                Q(effective_date=now) | Q(notification_date=now),
            )

            for generated_event in generated_event_qs:
                is_notify_on_notification_date = generated_event.is_notify_on_notification_date(now)
                is_notify_on_effective_date = generated_event.is_notify_on_effective_date(now)
                is_apply_default_on_notification_date = generated_event.is_apply_default_on_notification_date(now)
                is_apply_default_on_effective_date = generated_event.is_apply_default_on_effective_date(now)
                is_need_reaction_on_notification_date = generated_event.is_need_reaction_on_notification_date(now)
                is_need_reaction_on_effective_date = generated_event.is_need_reaction_on_effective_date(now)

                _l.debug(
                    'process:'
                    ' notification_class=%s,'
                    ' notification_date=%s,'
                    ' notification_date_notified=%s'
                    ' effective_date=%s,'
                    ' effective_date_notified=%s,'
                    ' is_notify_on_notification_date=%s,'
                    ' is_notify_on_effective_date=%s,'
                    ' is_apply_default_on_notification_date=%s,'
                    ' is_apply_default_on_effective_date=%s,'
                    ' is_need_reaction_on_notification_date=%s,'
                    ' is_need_reaction_on_effective_date=%s',
                    generated_event.event_schedule.notification_class,
                    generated_event.notification_date,
                    generated_event.notification_date_notified,
                    generated_event.effective_date,
                    generated_event.effective_date_notified,
                    is_notify_on_notification_date,
                    is_notify_on_effective_date,
                    is_apply_default_on_notification_date,
                    is_apply_default_on_effective_date,
                    is_need_reaction_on_notification_date,
                    is_need_reaction_on_effective_date)

                if is_notify_on_notification_date or is_notify_on_effective_date:
                    if is_notify_on_notification_date:
                        generated_event.notification_date_notified = True
                    if is_notify_on_effective_date:
                        generated_event.effective_date_notified = True

                    recipients = generated_event.master_user.members.all()
                    notifications.send(recipients=recipients,
                                       actor=generated_event.master_user,
                                       verb='event occurred',
                                       action_object=generated_event.event_schedule,
                                       target=generated_event.instrument)

                if is_apply_default_on_notification_date or is_apply_default_on_effective_date:
                    action = next((a for a in generated_event.event_schedule.actions.all() if a.is_book_automatic),
                                  None)
                    if action:
                        ttp = GeneratedEventProcess(generated_event=generated_event, action=action, calculate=True,
                                                    store=True)
                        # ttp.process()
                        # generated_event.processed(None, action, ttp.complex_transaction)
                        generated_event.processed(None, action, None)
                    else:
                        generated_event.status = GeneratedEvent.BOOKED
                        generated_event.status_date = timezone.now()

                if is_notify_on_notification_date or is_notify_on_effective_date or \
                        is_apply_default_on_notification_date or is_apply_default_on_effective_date:
                    generated_event.save()
