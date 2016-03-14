# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division

import datetime
from collections import Counter

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from django.utils.functional import cached_property

from poms.currencies.models import CurrencyHistory, Currency
from poms.instruments.models import PriceHistory
from poms.transactions.models import Transaction, TransactionClass


def fval(value, default=0.):
    return value if value is not None else default


def fgetattr(obj, attr, default=0.):
    return fval(getattr(obj, attr, default), default)


class BaseReportBuilder(object):
    def __init__(self, instance=None, queryset=None):
        self.instance = instance
        self._queryset = queryset
        self._filter_date_attr = None
        self._now = timezone.now().date()
        self._currency_history_cache = {}
        self._price_history_cache = {}

    @property
    def begin_date(self):
        return self.instance.begin_date or datetime.date.min

    @property
    def end_date(self):
        return self.instance.end_date or self._now

    def _get_transaction_qs(self):
        assert self._filter_date_attr is not None, "_filter_date_attr is None!"
        assert self.instance is not None, "instance is None!"
        assert self.instance.master_user is not None, "master_user is None!"
        if self._queryset is None:
            queryset = Transaction.objects
        else:
            queryset = self._queryset
        queryset = queryset.prefetch_related('transaction_class',
                                             'transaction_currency',
                                             'instrument',
                                             'instrument__pricing_currency',
                                             'instrument__accrued_currency',
                                             'settlement_currency')
        queryset = queryset.filter(master_user=self.instance.master_user, is_canceled=False)

        if self.instance.begin_date:
            # queryset = queryset.filter(transaction_date__gte=self.begin_date)
            queryset = queryset.filter(**{'%s__gte' % self._filter_date_attr: self.begin_date})
        # queryset = queryset.filter(transaction_date__lte=self.end_date)
        queryset = queryset.filter(**{'%s__lte' % self._filter_date_attr: self.end_date})
        if self.instance.instruments:
            queryset = queryset.filter(
                Q(instrument__in=self.instance.instruments) | Q(transaction_currency__isnull=False))
        queryset = queryset.order_by(self._filter_date_attr, 'id')
        return queryset

    @cached_property
    def transactions(self):
        queryset = self._get_transaction_qs()
        return list(queryset.all())

    def build(self):
        raise NotImplementedError('subclasses of BaseReportBuilder must provide an build() method')

    @cached_property
    def system_currency(self):
        return Currency.objects.get(master_user__isnull=True, user_code=settings.CURRENCY_CODE)

    def find_currency_history(self, currency, date=None):
        if currency is None:
            return None
        if not date:
            date = self.end_date
        if currency.is_system:
            return CurrencyHistory(currency=currency, date=date, fx_rate=1.)
        key = '%s:%s' % (currency.id, date)
        h = self._currency_history_cache.get(key, None)
        if h is None:
            h = CurrencyHistory.objects.filter(currency=currency, date__lte=date).order_by('date').last()
            if h is None:
                h = CurrencyHistory(currency=currency, date=date, fx_rate=0.)
            self._currency_history_cache[key] = h
        return h

    def find_price_history(self, instrument, date=None):
        if not date:
            date = self.end_date
        key = '%s:%s' % (instrument.id, date)
        h = self._price_history_cache.get(key, None)
        if h is None:
            h = PriceHistory.objects.filter(instrument=instrument, date__lte=date).order_by('date').last()
            if h is None:
                h = PriceHistory(instrument=instrument, date=date, principal_price=0., accrued_price=0., factor=0.)
            self._price_history_cache[key] = h
        return h

    def annotate_fx_rate(self, obj, currency_attr, date=None):
        currency = getattr(obj, currency_attr)
        currency_history = self.find_currency_history(currency, date=date)
        currency_fx_rate = getattr(currency_history, 'fx_rate', 0.) or 0.
        setattr(obj, '%s_history' % currency_attr, currency_history)
        setattr(obj, '%s_fx_rate' % currency_attr, currency_fx_rate)

    def annotate_price(self, transaction, date=None):
        instrument = transaction.instrument
        price_history = self.find_price_history(instrument, date=date)
        transaction.price_history = price_history

    def annotate_fx_rates(self, date=None):
        for t in self.transactions:
            if t.transaction_currency:
                self.annotate_fx_rate(t, 'transaction_currency', date=date)
                # t.transaction_currency_history = self.find_currency_history(t.transaction_currency)
                # t.transaction_currency_fx_rate = getattr(t.transaction_currency_history, 'fx_rate', 0.) or 0.

            if t.settlement_currency:
                self.annotate_fx_rate(t, 'settlement_currency', date=date)
                # t.settlement_currency_history = self.find_currency_history(t.settlement_currency)
                # t.settlement_currency_fx_rate = getattr(t.settlement_currency_history, 'fx_rate', 0.) or 0.

    def annotate_prices(self, date=None):
        for t in self.transactions:
            if t.instrument:
                self.annotate_price(t, date=date)

    def annotate_multiplier(self, multiplier_class):
        multiplier_attr = None
        if multiplier_class == 'avco':
            multiplier_attr = 'avco_multiplier'
            self.annotate_avco_multiplier()
        elif multiplier_class == 'fifo':
            multiplier_attr = 'fifo_multiplier'
            self.annotate_fifo_multiplier()
        return multiplier_attr

    def annotate_avco_multiplier(self):
        in_stock = {}
        not_closed = {}
        rolling_positions = Counter()

        for t in self.transactions:
            t_class = t.transaction_class.code
            if t_class not in [TransactionClass.BUY, TransactionClass.SELL]:
                continue

            i = t.instrument
            i_key = '%s' % i.pk

            t.avco_multiplier = 0.
            position_size_with_sign = t.position_size_with_sign
            rolling_position = rolling_positions[i_key]

            # if position_size_with_sign > 0.:  # покупка
            if t_class == TransactionClass.BUY:
                i_not_closed = not_closed.get(i_key, [])
                if i_not_closed:  # есть прошлые продажи, которые надо закрыть
                    if position_size_with_sign + rolling_position >= 0.:  # все есть
                        t.avco_multiplier = abs(rolling_position / position_size_with_sign)
                        for t0 in i_not_closed:
                            t0.avco_multiplier = 1.
                        in_stock[i_key] = in_stock.get(i_key, []) + [t]
                    else:  # только частично
                        t.avco_multiplier = 1.
                        for t0 in i_not_closed:
                            t0.avco_multiplier += abs(
                                (1. - t0.avco_multiplier) * position_size_with_sign / rolling_position)
                    not_closed[i_key] = [t for t in i_not_closed if t.avco_multiplier < 1.]
                else:  # новая "чистая" покупка
                    t.avco_multiplier = 0.
                    in_stock[i_key] = in_stock.get(i_key, []) + [t]
            # else:  # продажа
            elif t_class == TransactionClass.SELL:
                i_in_stock = in_stock.get(i_key, [])
                if i_in_stock:  # есть что продавать
                    if position_size_with_sign + rolling_position >= 0.:  # все есть
                        t.avco_multiplier = 1.
                        for t0 in i_in_stock:
                            t0.avco_multiplier += abs(
                                (1. - t0.avco_multiplier) * position_size_with_sign / rolling_position)
                    else:  # только частично
                        t.avco_multiplier = abs(rolling_position / position_size_with_sign)
                        for t0 in i_in_stock:
                            t0.avco_multiplier = 1.
                        not_closed[i_key] = not_closed.get(i_key, []) + [t]
                    in_stock[i_key] = [t for t in i_in_stock if t.avco_multiplier < 1.]
                else:  # нечего продавать
                    t.avco_multiplier = 0.
                    not_closed[i_key] = not_closed.get(i_key, []) + [t]
            rolling_position += position_size_with_sign
            rolling_positions[i_key] = rolling_position
            t.rolling_position = rolling_position

    def annotate_fifo_multiplier(self):
        in_stock = {}
        not_closed = {}
        rolling_positions = Counter()

        for t in self.transactions:
            t_class = t.transaction_class.code
            if t_class not in [TransactionClass.BUY, TransactionClass.SELL]:
                continue

            i = t.instrument
            i_key = '%s' % i.pk

            t.fifo_multiplier = 0.
            position_size_with_sign = t.position_size_with_sign
            rolling_position = rolling_positions[i_key]

            # if position_size_with_sign > 0.:  # покупка
            if t_class == TransactionClass.BUY:
                i_not_closed = not_closed.get(i_key, [])
                balance = position_size_with_sign
                if i_not_closed:
                    for t0 in i_not_closed:
                        sale = t0.not_closed
                        if balance + sale > 0.:  # есть все
                            balance -= abs(sale)
                            t0.fifo_multiplier = 1.
                            t0.not_closed = t0.not_closed - abs(t0.position_size_with_sign)
                        else:
                            t0.not_closed = t0.not_closed + balance
                            t0.fifo_multiplier = 1. - abs(t0.not_closed / t0.position_size_with_sign)
                            balance = 0.
                        if balance <= 0.:
                            break
                    not_closed[i_key] = [t for t in i_not_closed if t.fifo_multiplier < 1.]
                t.balance = balance
                t.fifo_multiplier = abs((position_size_with_sign - balance) / position_size_with_sign)
                if t.fifo_multiplier < 1.:
                    in_stock[i_key] = in_stock.get(i_key, []) + [t]
            # else:  # продажа
            elif t_class == TransactionClass.SELL:
                i_in_stock = in_stock.get(i_key, [])
                sale = position_size_with_sign
                if i_in_stock:
                    for t0 in i_in_stock:
                        balance = t0.balance
                        if sale + balance > 0.:  # есть все
                            t0.balance = balance - abs(sale)
                            t0.fifo_multiplier = abs(
                                (t0.position_size_with_sign - t0.balance) / t0.position_size_with_sign)
                            sale = 0.
                        else:
                            t0.balance = 0.
                            t0.fifo_multiplier = 1.
                            sale += abs(balance)
                        if sale >= 0.:
                            break
                    in_stock[i_key] = [t for t in i_in_stock if t.fifo_multiplier < 1.]
                t.not_closed = sale
                t.fifo_multiplier = abs((position_size_with_sign - sale) / position_size_with_sign)
                if t.fifo_multiplier < 1.:
                    not_closed[i_key] = not_closed.get(i_key, []) + [t]

            rolling_position += position_size_with_sign
            rolling_positions[i_key] = rolling_position
            t.rolling_position = rolling_position
