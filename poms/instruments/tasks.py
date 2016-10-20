import logging
from collections import defaultdict
from datetime import timedelta, date

from celery import shared_task
from django.conf import settings
from django.db.models import F

from poms import notifications
from poms.common.utils import date_now
from poms.instruments.models import EventSchedule, Instrument, CostMethod
from poms.reports.backends.balance import BalanceReport2PositionBuilder
from poms.reports.models import BalanceReport
from poms.transactions.models import EventClass
from poms.users.models import MasterUser, Member

_l = logging.getLogger('poms.instruments')


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
def calculate_prices_accrued_price_async(master_user=None, begin_date=None, end_date=None, instruments=None):
    if begin_date:
        begin_date = date.fromordinal(begin_date)
    if end_date:
        end_date = date.fromordinal(end_date)
    calculate_prices_accrued_price(master_user=master_user, begin_date=begin_date, end_date=end_date,
                                   instruments=instruments)


@shared_task(name='instruments.process_events', ignore_result=True)
def process_events(master_user=None, send_notification=True, notification_recipients=None):
    _l.debug('process_events: master_user=%s', master_user)

    now = date_now()

    # TODO: need cost_method to build report
    cost_method = CostMethod.objects.get(pk=CostMethod.AVCO)
    master_user = MasterUser.objects.get(pk=master_user)
    members = Member.objects.filter(master_user=master_user, is_deleted=False)

    opened_instrument_items = []
    instruments_pk = set()

    report = BalanceReport(master_user=master_user, begin_date=date.min, end_date=now, cost_method=cost_method,
                           use_portfolio=True, use_account=True, use_strategy=True, show_transaction_details=False)
    builder = BalanceReport2PositionBuilder(instance=report)
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
        position = item.balance_position

        event_schedules = event_schedule_cache.get(instrument.id) or []

        _l.debug('opened instrument: portfolio=%s, account=%s, strategy1=%s, strategy2=%s, strategy3=%s, '
                 'instrument=%s, event_schedules=%s',
                 portfolio.id, account.id, strategy1.id, strategy2.id, strategy3.id,
                 instrument.id, [e.id for e in event_schedules])

        if not event_schedules:
            continue

        for event_schedule in event_schedules:
            _l.debug('event_schedule=%s, event_class=%s, notification_class=%s, periodicity=%s',
                     event_schedule.id, event_schedule.event_class,
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
                need_inform, need_react, book_automatic = notification_class.check_date(
                    now, effective_date, notification_date)
                _l.debug('founded: event_class=%s, effective_date=%s, notification_date=%s, '
                         'need_inform=%s, need_react=%s, book_automatic=%s',
                         event_schedule.event_class, effective_date, notification_date,
                         need_inform, need_react, book_automatic)

                # ge_dup_qs = GeneratedEvent.objects.filter(
                #     master_user=master_user,
                #     effective_date=effective_date,
                #     notification_date=notification_date,
                #     instrument=instrument,
                #     portfolio=portfolio,
                #     account=account,
                #     strategy1=strategy1,
                #     strategy2=strategy2,
                #     strategy3=strategy3,
                #     position=position
                # )
                # if ge_dup_qs.exists():
                #     _l.debug('generated event already exist')
                #     continue

                # ge = GeneratedEvent()
                # ge.master_user = master_user
                # ge.status = GeneratedEvent.NEW
                # ge.status_modified = timezone.now()
                # ge.effective_date = effective_date
                # ge.notification_date = notification_date
                # ge.instrument = instrument
                # ge.portfolio = portfolio
                # ge.account = account
                # ge.strategy1 = strategy1
                # ge.strategy2 = strategy2
                # ge.strategy3 = strategy3
                # ge.position = position
                # ge.save()

                if need_inform:
                    _l.info('need_inform !!!!')
                    # action_object -> ge
                    if send_notification:
                        recipients = members
                        if notification_recipients is not None:
                            recipients = [m for m in members if m.id in notification_recipients]
                        notifications.send(recipients=recipients,
                                           actor=master_user,
                                           verb='event occurred',
                                           action_object=event_schedule,
                                           target=instrument)
                if need_react:
                    _l.info('need_react !!!!')

                if book_automatic:
                    _l.info('book_automatic !!!!')

    # _l.debug('event_schedule: count=%s', event_schedule_qs.count())
    # for event_schedule in event_schedule_qs:
    #     instrument = event_schedule.instrument
    #     master_user = instrument.master_user
    #
    #     _l.debug(
    #         'master_user=%s, instrument=%s, event_schedule=%s, event_class=%s, notification_class=%s, periodicity=%s',
    #         master_user.id, instrument.id, event_schedule.id, event_schedule.event_class,
    #         event_schedule.notification_class, event_schedule.periodicity)
    #
    #     notification_date_correction = timedelta(days=event_schedule.notify_in_n_days)
    #
    #     is_complies = False
    #     effective_date = None
    #     notification_date = None
    #
    #     if event_schedule.event_class_id == EventClass.ONE_OFF:
    #         effective_date = event_schedule.effective_date
    #         notification_date = effective_date - notification_date_correction
    #         _l.debug('effective_date=%s, notification_date=%s', effective_date, notification_date)
    #
    #         if notification_date == now or effective_date == now:
    #             is_complies = True
    #
    #     elif event_schedule.event_class_id == EventClass.REGULAR:
    #         for i in range(0, settings.INSTRUMENT_EVENTS_REGULAR_MAX_INTERVALS):
    #             effective_date = event_schedule.effective_date + event_schedule.periodicity.to_timedelta(
    #                 i, same_date=event_schedule.effective_date)
    #             notification_date = effective_date - notification_date_correction
    #             _l.debug('i=%s, book_date=%s, notify_date=%s', i, effective_date, notification_date)
    #
    #             if effective_date > event_schedule.final_date:
    #                 break
    #             if effective_date < now:
    #                 continue
    #             if notification_date > now and effective_date > now:
    #                 break
    #
    #             if notification_date == now or effective_date == now:
    #                 is_complies = True
    #                 break
    #
    #     if is_complies:
    #         notification_class = event_schedule.notification_class
    #         need_inform, need_react, apply_def = notification_class.check_date(now, effective_date, notification_date)
    #
    #         if need_inform:
    #             _l.info('need_inform !!!!')
    #
    #         if need_react:
    #             _l.info('need_react !!!!')
    #
    #         if apply_def:
    #             _l.info('apply_def !!!!')

    _l.debug('finished')


# @receiver(post_save, dispatch_uid='chat_message_created', sender=GeneratedEvent)
# def chat_message_created(sender, instance=None, created=None, **kwargs):
#     if created:
#
#         instance.instrument = instrument
#         instance.portfolio = portfolio
#         instance.account = account
#         instance.strategy1 = strategy1
#         instance.strategy2 = strategy2
#         instance.strategy3 = strategy3
#
#         master_user = instance.thread.master_user
#         thread = instance.thread
#         qs = Member.objects.filter(master_user=master_user).exclude(id=instance.sender_id)
#         recipients = [m.user for m in qs if has_view_perms(m, thread)]
#         notifications.send(recipients,
#                            actor=instance.sender,
#                            verb='sent',
#                            action_object=instance,
#                            target=instance.thread)


@shared_task(name='instruments.process_events_auto', ignore_result=True)
def process_events_auto():
    for master_user in MasterUser.objects.all():
        process_events.delay(master_user=master_user.pk)
