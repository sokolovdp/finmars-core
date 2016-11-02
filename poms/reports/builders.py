# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division

import logging
from collections import Counter
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone
from django.utils.functional import cached_property

from poms.common.utils import isclose, date_now
from poms.currencies.models import CurrencyHistory
from poms.instruments.models import PriceHistory, CostMethod
from poms.transactions.models import Transaction, TransactionClass

_l = logging.getLogger('poms.reports')


class VirtualTransaction(object):
    def __init__(self, transaction, pk, override_values):
        self.transaction = transaction
        self.pk = pk
        self.override_values = override_values or {}

    def __getattr__(self, item):
        if item == 'pk' or item == 'id':
            return self.pk
        if item in self.override_values:
            return self.override_values[item]
        return getattr(self.transaction, item)


class ReportItem(object):
    def __init__(self, pk=None, instrument=None, currency=None,
                 portfolio=None, account=None, strategy1=None, strategy2=None, strategy3=None,
                 detail_transaction=None, transaction_class=None, custom_fields=None,
                 position=0.0):
        self.pk = pk
        self.instrument = instrument  # -> Instrument
        self.currency = currency  # -> Currency
        self.portfolio = portfolio  # -> Portfolio if use_portfolio
        self.account = account  # -> Account if use_account
        self.strategy1 = strategy1  # -> Strategy1 if use_strategy1
        self.strategy2 = strategy2  # -> Strategy2 if use_strategy2
        self.strategy3 = strategy3  # -> Strategy3 if use_strategy3
        self.detail_transaction = detail_transaction  # -> Transaction if show_transaction_details
        self.transaction_class = transaction_class  # -> TransactionClass for TRANSACTION_PL and FX_TRADE
        self.custom_fields = custom_fields or {}

        self.position = position

        # balance
        self.market_value_system_ccy = 0.0
        self.market_value_report_ccy = 0.0

        # P&L

        self.principal_with_sign_system_ccy = 0.0
        self.carry_with_sign_system_ccy = 0.0
        self.overheads_with_sign_system_ccy = 0.0
        self.total_with_sign_system_ccy = 0.0

        self.principal_with_sign_report_ccy = 0.0
        self.carry_with_sign_report_ccy = 0.0
        self.overheads_with_sign_report_ccy = 0.0
        self.total_with_sign_report_ccy = 0.0

    def __str__(self):
        return "%s #%s" % (self.__class__.__name__, self.pk,)

    def is_zero(self):
        return isclose(self.position, 0.0) \
               and isclose(self.market_value_system_ccy, 0.0) \
               and isclose(self.principal_with_sign_system_ccy, 0.0) \
               and isclose(self.carry_with_sign_system_ccy, 0.0) \
               and isclose(self.overheads_with_sign_system_ccy, 0.0) \
               and isclose(self.total_with_sign_system_ccy, 0.0)


class ReportSummary(object):
    def __init__(self):
        # balance
        self.market_value_system_ccy = 0.0
        self.market_value_report_ccy = 0.0

        # P&L
        self.principal_with_sign_system_ccy = 0.0
        self.carry_with_sign_system_ccy = 0.0
        self.overheads_with_sign_system_ccy = 0.0
        self.total_with_sign_system_ccy = 0.0

        self.principal_with_sign_report_ccy = 0.0
        self.carry_with_sign_report_ccy = 0.0
        self.overheads_with_sign_report_ccy = 0.0
        self.total_with_sign_report_ccy = 0.0

    def __str__(self):
        return "summary"

    def add_items(self, items):
        for item in items:
            self.market_value_system_ccy += item.market_value_system_ccy
            self.market_value_report_ccy += item.market_value_report_ccy

            # P&L
            self.principal_with_sign_system_ccy += item.principal_with_sign_system_ccy
            self.carry_with_sign_system_ccy += item.carry_with_sign_system_ccy
            self.overheads_with_sign_system_ccy += item.overheads_with_sign_system_ccy
            self.total_with_sign_system_ccy += item.total_with_sign_system_ccy

            self.principal_with_sign_report_ccy += item.principal_with_sign_report_ccy
            self.carry_with_sign_report_ccy += item.carry_with_sign_report_ccy
            self.overheads_with_sign_report_ccy += item.overheads_with_sign_report_ccy
            self.total_with_sign_report_ccy += item.total_with_sign_report_ccy


class Report(object):
    def __init__(self, id=None, master_user=None, task_id=None, task_status=None,
                 report_date=None, report_currency=None, pricing_policy=None, cost_method=None,
                 detail_by_portfolio=False, detail_by_account=False, detail_by_strategy1=False,
                 detail_by_strategy2=False, detail_by_strategy3=False,
                 show_transaction_details=False,
                 portfolios=None, accounts=None, strategies1=None, strategies2=None, strategies3=None,
                 custom_fields=None, items=None, summary=None, transactions=None):
        self.id = id
        self.task_id = task_id
        self.task_status = task_status

        self.master_user = master_user
        self.pricing_policy = pricing_policy
        self.report_date = report_date or (date_now() - timedelta(days=1))
        self.report_currency = report_currency or master_user.system_currency
        self.cost_method = cost_method or CostMethod.objects.get(pk=CostMethod.AVCO)

        self.detail_by_portfolio = detail_by_portfolio
        self.detail_by_account = detail_by_account
        self.detail_by_strategy1 = detail_by_strategy1
        self.detail_by_strategy2 = detail_by_strategy2
        self.detail_by_strategy3 = detail_by_strategy3
        self.show_transaction_details = show_transaction_details

        self.portfolios = portfolios or []
        self.accounts = accounts or []
        self.strategies1 = strategies1 or []
        self.strategies2 = strategies2 or []
        self.strategies3 = strategies3 or []

        self.custom_fields = custom_fields or []

        self.items = items or []
        self.summary = ReportSummary()
        if items:
            self.summary.add_items(items)
        self.summary = summary or ReportSummary()
        self.transactions = transactions or []

    def __str__(self):
        return "%s for %s @ %s" % (self.__class__.__name__, self.master_user, self.report_date)


class ReportBuilder(object):
    def __init__(self, instance=None, queryset=None, transactions=None):
        self.instance = instance
        self._queryset = queryset
        self._filter_date_attr = 'transaction_date'

        self._transactions = transactions

        self._now = timezone.now().date()
        self._report_date = self.instance.report_date or self._now

        self._detail_by_portfolio = self.instance.detail_by_portfolio
        self._detail_by_account = self.instance.detail_by_account
        self._detail_by_strategy1 = self.instance.detail_by_strategy1
        self._detail_by_strategy2 = self.instance.detail_by_strategy2
        self._detail_by_strategy3 = self.instance.detail_by_strategy3
        self._any_details = self._detail_by_portfolio or self._detail_by_account or self._detail_by_strategy1 or self._detail_by_strategy2 or self._detail_by_strategy3

        self._items = {}

    @property
    def system_currency(self):
        return self.instance.master_user.system_currency

    def _get_transaction_qs(self):
        if self._queryset is None:
            queryset = Transaction.objects
        else:
            queryset = self._queryset

        queryset = queryset.filter(master_user=self.instance.master_user, is_canceled=False)

        queryset = queryset.select_related(
            # TODO: add fields!!!
        )

        queryset = queryset.filter(**{'%s__lte' % self._filter_date_attr: self._report_date})

        if self.instance.portfolios:
            queryset = queryset.filter(portfolio__in=self.instance.portfolios)

        if self.instance.accounts:
            queryset = queryset.filter(account_position__in=self.instance.accounts)
            queryset = queryset.filter(account_cash__in=self.instance.accounts)
            queryset = queryset.filter(account_interim__in=self.instance.accounts)

        if self.instance.strategies1:
            queryset = queryset.filter(strategy1_position__in=self.instance.strategies1)
            queryset = queryset.filter(strategy1_cash__in=self.instance.strategies1)

        if self.instance.strategies2:
            queryset = queryset.filter(strategy2_position__in=self.instance.strategies2)
            queryset = queryset.filter(strategy2_cash__in=self.instance.strategies2)

        if self.instance.strategies3:
            queryset = queryset.filter(strategy3_position__in=self.instance.strategies3)
            queryset = queryset.filter(strategy3_cash__in=self.instance.strategies3)

        queryset = queryset.order_by(self._filter_date_attr, 'transaction_code', 'id')

        return queryset

    def _get_instrument_price_history_qs(self):
        transaction_qs = self._get_transaction_qs()
        return PriceHistory.objects.filter(
            pricing_policy=self.instance.pricing_policy
        ).filter(
            Q(date=self._report_date) |
            Q(date__in=transaction_qs.values_list('accounting_date', flat=True))
        ).filter(
            instrument__in=transaction_qs.values_list('instrument', flat=True)
        )

    def _get_currency_history_qs(self):
        transaction_qs = self._get_transaction_qs()
        return CurrencyHistory.objects.filter(
            pricing_policy=self.instance.pricing_policy
        ).filter(
            Q(date=self._report_date) |
            Q(date__in=transaction_qs.values_list('cash_date', flat=True)) |
            Q(date__in=transaction_qs.values_list('accounting_date', flat=True))
        ).filter(
            Q(currency__in=transaction_qs.values_list('transaction_currency', flat=True)) |
            Q(currency__in=transaction_qs.values_list('settlement_currency', flat=True)) |
            Q(currency__in=transaction_qs.values_list('instrument__pricing_currency', flat=True)) |
            Q(currency__in=transaction_qs.values_list('instrument__accrued_currency', flat=True))
        )

    @cached_property
    def _price_history_cache(self):
        cache = {}
        for h in self._get_instrument_price_history_qs():
            cache[(h.instrument_id, h.date)] = h
        return cache

    def _get_instrument_price_history(self, instrument, date=None):
        date = date or self._report_date
        key = (instrument.id, date)
        try:
            return self._price_history_cache[key]
        except KeyError:
            h = PriceHistory(pricing_policy=self.instance.pricing_policy, instrument=instrument, date=date)
            self._price_history_cache[key] = h
            return h

    @cached_property
    def _currency_history_cache(self):
        cache = {}
        for h in self._get_currency_history_qs():
            cache[(h.currency_id, h.date)] = h
        return cache

    def _get_currency_history(self, currency, date=None):
        date = date or self._report_date
        key = (currency.id, date)
        try:
            return self._currency_history_cache[key]
        except KeyError:
            h = CurrencyHistory(pricing_policy=self.instance.pricing_policy, currency=currency, date=date)
            # if currency.is_system:
            if self.instance.master_user.system_currency_id == currency.id:
                h.fx_rate = 1.0
            self._currency_history_cache[key] = h
            return h

    @cached_property
    def _transaction_class_sell(self):
        return TransactionClass.objects.get(pk=TransactionClass.SELL)

    @cached_property
    def _transaction_class_buy(self):
        return TransactionClass.objects.get(pk=TransactionClass.BUY)

    @cached_property
    def _transaction_class_fx_trade(self):
        return TransactionClass.objects.get(pk=TransactionClass.FX_TRADE)

    @cached_property
    def transactions(self):
        from poms.reports.models import VirtualTransaction

        if self._transactions:
            return self._transactions

        transactions = [t for t in self._get_transaction_qs()]

        self._annotate_multiplier(transactions)

        transactions1 = []
        for t in transactions:
            # self._annotate_transaction_history(t)
            self._annotate_transaction_case(t)

            t_class = t.transaction_class_id
            if t_class == TransactionClass.TRANSFER:
                if t.position_size_with_sign >= 0:
                    t1 = VirtualTransaction(
                        transaction=t,
                        pk='%s:sell' % t.pk,
                        override_values={
                            'transaction_class_id': self._transaction_class_sell.id,
                            'transaction_class': self._transaction_class_sell,
                            'account_position': t.account_cash,
                            'account_cash': t.account_cash,

                            'position_size_with_sign': -t.position_size_with_sign,
                            'cash_consideration': t.cash_consideration,
                            'principal_with_sign': t.principal_with_sign,
                            'carry_with_sign': t.carry_with_sign,
                            'overheads_with_sign': t.overheads_with_sign,
                        })
                    t2 = VirtualTransaction(
                        transaction=t,
                        pk='%s:buy' % t.pk,
                        override_values={
                            'transaction_class_id': self._transaction_class_buy.id,
                            'transaction_class': self._transaction_class_buy,
                            'account_position': t.account_position,
                            'account_cash': t.account_position,

                            'position_size_with_sign': t.position_size_with_sign,
                            'cash_consideration': -t.cash_consideration,
                            'principal_with_sign': -t.principal_with_sign,
                            'carry_with_sign': -t.carry_with_sign,
                            'overheads_with_sign': -t.overheads_with_sign,
                        })
                else:
                    t1 = VirtualTransaction(
                        transaction=t,
                        pk='%s:buy' % t.pk,
                        override_values={
                            'transaction_class_id': self._transaction_class_buy.id,
                            'transaction_class': self._transaction_class_buy,
                            'account_position': t.account_cash,
                            'account_cash': t.account_cash,

                            'position_size_with_sign': -t.position_size_with_sign,
                            'cash_consideration': t.cash_consideration,
                            'principal_with_sign': t.principal_with_sign,
                            'carry_with_sign': t.carry_with_sign,
                            'overheads_with_sign': t.overheads_with_sign,
                        })
                    t2 = VirtualTransaction(
                        transaction=t,
                        pk='%s:sell' % t.pk,
                        override_values={
                            'transaction_class_id': self._transaction_class_sell.id,
                            'transaction_class': self._transaction_class_sell,
                            'account_position': t.account_position,
                            'account_cash': t.account_position,

                            'position_size_with_sign': t.position_size_with_sign,
                            'cash_consideration': -t.cash_consideration,
                            'principal_with_sign': -t.principal_with_sign,
                            'carry_with_sign': -t.carry_with_sign,
                            'overheads_with_sign': -t.overheads_with_sign,
                        })
                transactions1.append(t1)
                transactions1.append(t2)
            elif t_class == TransactionClass.FX_TRANSFER:
                t1 = VirtualTransaction(
                    transaction=t,
                    pk='%s:sell' % t.pk,
                    override_values={
                        'transaction_class_id': self._transaction_class_fx_trade.id,
                        'transaction_class': self._transaction_class_fx_trade,
                        'account_position': t.account_cash,
                        'account_cash': t.account_cash,

                        'position_size_with_sign': -t.position_size_with_sign,
                        'cash_consideration': t.cash_consideration,
                        'principal_with_sign': t.principal_with_sign,
                        'carry_with_sign': t.carry_with_sign,
                        'overheads_with_sign': t.overheads_with_sign,
                    })

                t2 = VirtualTransaction(
                    transaction=t,
                    pk='%s:buy' % t.pk,
                    override_values={
                        'transaction_class_id': self._transaction_class_fx_trade.id,
                        'transaction_class': self._transaction_class_fx_trade,
                        'account_position': t.account_position,
                        'account_cash': t.account_position,

                        'position_size_with_sign': t.position_size_with_sign,
                        'cash_consideration': -t.cash_consideration,
                        'principal_with_sign': -t.principal_with_sign,
                        'carry_with_sign': -t.carry_with_sign,
                        'overheads_with_sign': -t.overheads_with_sign,
                    })
                transactions1.append(t1)
                transactions1.append(t2)
            else:
                transactions1.append(t)
        return transactions1

    # def _annotate_transaction_history(self, transaction):
    #     if transaction.instrument:
    #         transaction.instrument_price_history = self._get_instrument_price_history(
    #             transaction.instrument)
    #         # transaction.instrument_price_history_on_accounting_date = self._get_instrument_price_history(
    #         #     transaction.instrument, transaction.accounting_date)
    #
    #         if transaction.instrument.pricing_currency:
    #             transaction.instrument_pricing_currency_history = self._get_currency_history(
    #                 transaction.instrument.pricing_currency)
    #             # transaction.instrument_pricing_currency_history_on_accounting_date = self._get_currency_history(
    #             #     transaction.instrument.pricing_currency, transaction.accounting_date)
    #         if transaction.instrument.accrued_currency:
    #             transaction.instrument_accrued_currency_history = self._get_currency_history(
    #                 transaction.instrument.accrued_currency)
    #             # transaction.instrument_accrued_currency_history_on_accounting_date = self._get_currency_history(
    #             #     transaction.instrument.accrued_currency, transaction.accounting_date)
    #
    #     if transaction.transaction_currency:
    #         transaction.transaction_currency_history = self._get_currency_history(
    #             transaction.transaction_currency)
    #         # transaction.transaction_currency_history_on_accounting_date = self._get_currency_history(
    #         #     transaction.transaction_currency, transaction.accounting_date)
    #
    #     if transaction.settlement_currency:
    #         transaction.settlement_currency_history = self._get_currency_history(
    #             transaction.settlement_currency)
    #         # transaction.settlement_currency_history_on_cash_date = self._get_currency_history(
    #         #     transaction.settlement_currency, transaction.cash_date)

    def _annotate_multiplier(self, transactions):
        if self._any_details:
            if self.instance.cost_method.id == CostMethod.AVCO:
                self._annotate_avco_multiplier(transactions)
            elif self.instance.cost_method.id == CostMethod.FIFO:
                self._annotate_fifo_multiplier(transactions)
        else:
            for t in transactions:
                t.multiplier = 1.0

    def _annotate_avco_multiplier(self, transactions):
        in_stock = {}
        not_closed = {}
        rolling_positions = Counter()

        for t in transactions:
            t_class = t.transaction_class_id

            if t_class not in [TransactionClass.BUY, TransactionClass.SELL]:
                continue

            # do not use strategy!!!
            t_key = self._make_key(portfolio=t.portfolio, account=t.account_position, instrument=t.instrument)

            t.avco_multiplier = 0.0
            position_size_with_sign = t.position_size_with_sign
            rolling_position = rolling_positions[t_key]

            # if position_size_with_sign > 0.:  # покупка
            if t_class == TransactionClass.BUY:
                i_not_closed = not_closed.get(t_key, [])
                if i_not_closed:  # есть прошлые продажи, которые надо закрыть
                    if position_size_with_sign + rolling_position >= 0.0:  # все есть
                        t.avco_multiplier = abs(rolling_position / position_size_with_sign)
                        for t0 in i_not_closed:
                            t0.avco_multiplier = 1.0
                        in_stock[t_key] = in_stock.get(t_key, []) + [t]
                    else:  # только частично
                        t.avco_multiplier = 1.0
                        for t0 in i_not_closed:
                            t0.avco_multiplier += abs(
                                (1.0 - t0.avco_multiplier) * position_size_with_sign / rolling_position)
                    not_closed[t_key] = [t0 for t0 in i_not_closed if t0.avco_multiplier < 1.0]
                else:  # новая "чистая" покупка
                    t.avco_multiplier = 0.0
                    in_stock[t_key] = in_stock.get(t_key, []) + [t]

            # else:  # продажа
            elif t_class == TransactionClass.SELL:
                i_in_stock = in_stock.get(t_key, [])
                if i_in_stock:  # есть что продавать
                    if position_size_with_sign + rolling_position >= 0.0:  # все есть
                        t.avco_multiplier = 1.0
                        for t0 in i_in_stock:
                            t0.avco_multiplier += abs(
                                (1.0 - t0.avco_multiplier) * position_size_with_sign / rolling_position)
                    else:  # только частично
                        t.avco_multiplier = abs(rolling_position / position_size_with_sign)
                        for t0 in i_in_stock:
                            t0.avco_multiplier = 1.0
                        not_closed[t_key] = not_closed.get(t_key, []) + [t]
                    in_stock[t_key] = [t0 for t0 in i_in_stock if t0.avco_multiplier < 1.0]
                else:  # нечего продавать
                    t.avco_multiplier = 0.0
                    not_closed[t_key] = not_closed.get(t_key, []) + [t]

            rolling_position += position_size_with_sign
            rolling_positions[t_key] = rolling_position
            t.rolling_position = rolling_position

        for t in self.transactions:
            t.multiplier = t.avco_multiplier

    def _annotate_fifo_multiplier(self, transactions):
        in_stock = {}
        not_closed = {}
        rolling_positions = Counter()

        for t in transactions:
            t_class = t.transaction_class_id
            if t_class not in [TransactionClass.BUY, TransactionClass.SELL]:
                continue

            # do not use strategy!!!
            t_key = self._make_key(portfolio=t.portfolio, account=t.account_position, instrument=t.instrument)

            t.fifo_multiplier = 0.0
            position_size_with_sign = t.position_size_with_sign
            rolling_position = rolling_positions[t_key]

            # if position_size_with_sign > 0.:  # покупка
            if t_class == TransactionClass.BUY:
                i_not_closed = not_closed.get(t_key, [])
                balance = position_size_with_sign
                if i_not_closed:
                    for t0 in i_not_closed:
                        sale = t0.not_closed
                        if balance + sale > 0.0:  # есть все
                            balance -= abs(sale)
                            t0.fifo_multiplier = 1.0
                            t0.not_closed = t0.not_closed - abs(t0.position_size_with_sign)
                        else:
                            t0.not_closed = t0.not_closed + balance
                            t0.fifo_multiplier = 1.0 - abs(t0.not_closed / t0.position_size_with_sign)
                            balance = 0.0
                        if balance <= 0.0:
                            break
                    not_closed[t_key] = [t0 for t0 in i_not_closed if t0.fifo_multiplier < 1.0]
                t.balance = balance
                t.fifo_multiplier = abs((position_size_with_sign - balance) / position_size_with_sign)
                if t.fifo_multiplier < 1.0:
                    in_stock[t_key] = in_stock.get(t_key, []) + [t]

            # else:  # продажа
            elif t_class == TransactionClass.SELL:
                i_in_stock = in_stock.get(t_key, [])
                sale = position_size_with_sign
                if i_in_stock:
                    for t0 in i_in_stock:
                        balance = t0.balance
                        if sale + balance > 0.0:  # есть все
                            t0.balance = balance - abs(sale)
                            t0.fifo_multiplier = abs(
                                (t0.position_size_with_sign - t0.balance) / t0.position_size_with_sign)
                            sale = 0.0
                        else:
                            t0.balance = 0.0
                            t0.fifo_multiplier = 1.0
                            sale += abs(balance)
                        if sale >= 0.0:
                            break
                    in_stock[t_key] = [t0 for t0 in i_in_stock if t0.fifo_multiplier < 1.0]
                t.not_closed = sale
                t.fifo_multiplier = abs((position_size_with_sign - sale) / position_size_with_sign)
                if t.fifo_multiplier < 1.0:
                    not_closed[t_key] = not_closed.get(t_key, []) + [t]

            rolling_position += position_size_with_sign
            rolling_positions[t_key] = rolling_position
            t.rolling_position = rolling_position

        for t in self.transactions:
            t.multiplier = t.fifo_multiplier

    def _annotate_transaction_case(self, t):
        if t.accounting_date <= self._report_date < t.cash_date:  # default
            t.case = 1
        elif t.cash_date <= self._report_date < t.accounting_date:
            t.case = 2
        else:
            t.case = 0

    def build(self):
        for t in self.transactions:
            t_class = t.transaction_class_id
            if t_class == TransactionClass.BUY:
                self._process_transaction_buy(t)

            elif t_class == TransactionClass.SELL:
                self._process_transaction_sell(t)

            elif t_class == TransactionClass.FX_TRADE:
                self._process_transaction_fx_trade(t)

            elif t_class == TransactionClass.INSTRUMENT_PL:
                self._process_transaction_instrument_pl(t)

            elif t_class == TransactionClass.TRANSACTION_PL:
                self._process_transaction_transaction_pl(t)

            elif t_class == TransactionClass.TRANSFER:
                self._process_transaction_transfer(t)

            elif t_class == TransactionClass.FX_TRANSFER:
                self._process_transaction_fx_transfer(t)

            elif t_class == TransactionClass.CASH_INFLOW:
                self._process_transaction_cash_inflow(t)

            elif t_class == TransactionClass.CASH_OUTFLOW:
                self._process_transaction_cash_outflow(t)

        for item in self._items.values():
            self._process_final(item)

        self.instance.items = sorted([i for i in self._items.values()], key=lambda x: x.pk)
        self.instance.summary.add_items(self.instance.items)

        return self.instance

    def _process_transaction_buy(self, t):
        if self._any_details:
            self._process_instrument(t, value=t.position_size_with_sign * (1.0 - t.multiplier))
        else:
            self._process_instrument(t, value=t.position_size_with_sign)
        self._process_cash(t, currency=t.settlement_currency, value=t.cash_consideration)

    def _process_transaction_sell(self, t):
        self._process_transaction_sell(t)

    def _process_transaction_fx_trade(self, t):
        self._process_cash(t, currency=t.transaction_currency, value=t.position_size_with_sign,
                           account=t.account_position, account_interim=t.account_interim)

        self._process_cash(t, currency=t.settlement_currency, value=t.cash_consideration,
                           account=t.account_cash, account_interim=t.account_interim)

        # P&L
        item = self._get_item(t)
        item.principal_with_sign_system_ccy += self._to_system_ccy(t.position_size_with_sign, t.transaction_currency) + \
                                               self._to_system_ccy(t.principal_with_sign, t.settlement_currency)
        item.carry_with_sign_system_ccy += self._to_system_ccy(t.carry_with_sign, t.settlement_currency)
        item.overheads_with_sign_system_ccy += self._to_system_ccy(t.overheads_with_sign, t.settlement_currency)

    def _process_transaction_instrument_pl(self, t):
        self._process_cash(t, currency=t.settlement_currency, value=t.cash_consideration,
                           account=t.account_cash, account_interim=t.account_interim)

    def _process_transaction_transaction_pl(self, t):
        self._process_instrument(t, value=0.0)

        self._process_cash(t, currency=t.settlement_currency, value=t.cash_consideration,
                           account=t.account_cash, account_interim=t.account_interim)

    def _process_transaction_transfer(self, t):
        raise RuntimeError('Virtual transaction must be created')

    def _process_transaction_fx_transfer(self, t):
        raise RuntimeError('Virtual transaction must be created')

    def _process_transaction_cash_inflow(self, t):
        self._process_cash(t, currency=t.transaction_currency, value=t.position_size_with_sign,
                           account=t.account_position, account_interim=t.account_interim)

    def _process_transaction_cash_outflow(self, t):
        self._process_transaction_cash_outflow(t)

    def _to_system_ccy(self, value, ccy):
        h = self._get_currency_history(ccy)
        return value * h.fx_rate

    def _to_report_ccy(self, value):
        h = self._get_currency_history(self.instance.report_currency)
        if isclose(h.fx_rate, 0.0):
            return 0.0
        else:
            return value / h.fx_rate

    def _show_transaction_details(self, case, acc):
        if case in [1, 2] and self.instance.show_transaction_details:
            return acc and acc.type and acc.type.show_transaction_details
        return False

    def _make_key(self, instrument=None, currency=None,
                  portfolio=None, account=None, strategy1=None, strategy2=None, strategy3=None,
                  case=None, detail_transaction=None,
                  transaction_class=None):
        instrument = getattr(instrument, 'pk', -1)
        currency = getattr(currency, 'pk', -1)
        portfolio = getattr(portfolio, 'pk', -1) if self._detail_by_portfolio else -1
        account = getattr(account, 'pk', -1) if self._detail_by_account else -1
        strategy1 = getattr(strategy1, 'pk', -1) if self._detail_by_strategy1 else -1
        strategy2 = getattr(strategy2, 'pk', -1) if self._detail_by_strategy2 else -1
        strategy3 = getattr(strategy3, 'pk', -1) if self._detail_by_strategy3 else -1
        detail_transaction = getattr(detail_transaction, 'pk', -1) if self._show_transaction_details(case,
                                                                                                     account) else -1
        transaction_class = getattr(transaction_class, 'pk', -1)

        return 'i:%s|c:%s|p:%s|s1:%s|s2:%s|s3:%s|a:%s|dt:%s|tcls:%s' % (
            instrument, currency, portfolio, strategy1, strategy2, strategy3, account, detail_transaction,
            transaction_class,
        )

    def _get_item(self, t, instrument=None, currency=None, account=None, transaction_class=None):
        i_instrument = instrument
        i_currency = currency

        i_portfolio = None
        if self._detail_by_portfolio:
            i_portfolio = t.portfolio

        i_account = None
        if self._detail_by_account:
            i_account = account
            if i_account is None:
                if instrument:
                    i_account = t.account_position
                elif currency:
                    i_account = t.account_cash

        i_strategy1 = None
        if self._detail_by_strategy1:
            if instrument:
                i_strategy1 = t.strategy1_position
            elif currency:
                i_strategy1 = t.strategy1_cash

        i_strategy2 = None
        if self._detail_by_strategy2:
            if instrument:
                i_strategy2 = t.strategy2_position
            elif currency:
                i_strategy2 = t.strategy2_cash

        i_strategy3 = None
        if self._detail_by_strategy3:
            if instrument:
                i_strategy3 = t.strategy3_position
            elif currency:
                i_strategy3 = t.strategy3_cash

        i_detail_transaction = t if i_account and self._show_transaction_details(t.case, i_account) else None
        if isinstance(i_detail_transaction, VirtualTransaction):
            i_detail_transaction = i_detail_transaction.transaction

        i_transaction_class = None
        if t.transaction_class.id in [TransactionClass.TRANSACTION_PL, TransactionClass.FX_TRADE]:
            i_instrument = None
            i_transaction_class = t.transaction_class

        pk = self._make_key(
            instrument=i_instrument,
            currency=i_currency,
            portfolio=i_portfolio,
            account=i_account,
            strategy1=i_strategy1,
            strategy2=i_strategy2,
            strategy3=i_strategy3,
            case=t.case,
            detail_transaction=i_detail_transaction,
            transaction_class=i_transaction_class
        )

        try:
            return self._items[pk]
        except KeyError:
            item = ReportItem(
                pk=pk,
                instrument=instrument,
                currency=currency,
                portfolio=i_portfolio,
                account=i_account,
                strategy1=i_strategy1,
                strategy2=i_strategy2,
                strategy3=i_strategy3,
                detail_transaction=i_detail_transaction
            )
            self._items[pk] = item
            return item

    def _process_instrument(self, t, value):
        if t.case == 0:
            item = self._get_item(t, instrument=t.instrument)
            item.position += value
            self._process_instrument_p_l(t, item)

        elif t.case == 1:
            item = self._get_item(t, instrument=t.instrument)
            item.position += value
            self._process_instrument_p_l(t, item)

        elif t.case == 2:
            pass

    def _process_instrument_p_l(self, t, item):
        if item is None:
            item = self._get_item(t, instrument=t.instrument)

        ccy = t.settlement_currency
        item.principal_with_sign_system_ccy += self._to_system_ccy(t.principal_with_sign, ccy)
        item.carry_with_sign_system_ccy += self._to_system_ccy(t.carry_with_sign, ccy)
        item.overheads_with_sign_system_ccy += self._to_system_ccy(t.overheads_with_sign, ccy)

    def _process_cash(self, t, currency, value, account=None, account_interim=None):
        if account is None:
            account = t.account_cash
        if account_interim is None:
            account_interim = t.account_interim

        if t.case == 0:
            item = self._get_item(t, currency=currency, account=account)
            item.position += value

        elif t.case == 1:
            item = self._get_item(t, currency=currency, account=account_interim)
            item.position += value

        elif t.case == 2:
            item = self._get_item(t, currency=currency, account=account)
            item.position += value

            item = self._get_item(t, currency=currency, account=account_interim)
            item.position -= value

    def _process_final(self, item):
        if item.instrument:
            price = self._get_instrument_price_history(item.instrument)

            principal_value = item.instrument.price_multiplier * item.position * price.principal_price
            accrued_value = item.instrument.accrued_multiplier * item.position * price.accrued_price

            principal_value_system_ccy = self._to_system_ccy(principal_value, item.instrument.pricing_currency)
            accrued_value_system_ccy = self._to_system_ccy(accrued_value, item.instrument.accrued_currency)

            # balance
            item.market_value_system_ccy = principal_value_system_ccy + accrued_value_system_ccy
            # item.market_value_report_ccy = self._to_report_ccy(item.market_value_system_ccy)

            # P&L
            # item.total_with_sign_system_ccy = item.principal_with_sign_system_ccy + \
            #                                   item.carry_with_sign_system_ccy + \
            #                                   item.overheads_with_sign_system_ccy
            #
            # item.principal_with_sign_report_ccy = self._to_report_ccy(item.principal_with_sign_system_ccy)
            # item.carry_with_sign_system_ccy = self._to_report_ccy(item.carry_with_sign_system_ccy)
            # item.overheads_with_sign_system_ccy = self._to_report_ccy(item.overheads_with_sign_system_ccy)
            # item.total_with_sign_system_ccy = self._to_report_ccy(item.total_with_sign_system_ccy)
            pass

        elif item.currency:
            # balance
            item.market_value_system_ccy = self._to_system_ccy(item.position, item.currency)
            # item.market_value_report_ccy = self._to_report_ccy(item.market_value_system_ccy)

            # P&L
            # item.total_with_sign_system_ccy = item.principal_with_sign_system_ccy + \
            #                                   item.carry_with_sign_system_ccy + \
            #                                   item.overheads_with_sign_system_ccy
            #
            # item.principal_with_sign_report_ccy = self._to_report_ccy(item.principal_with_sign_system_ccy)
            # item.carry_with_sign_system_ccy = self._to_report_ccy(item.carry_with_sign_system_ccy)
            # item.overheads_with_sign_system_ccy = self._to_report_ccy(item.overheads_with_sign_system_ccy)
            # item.total_with_sign_system_ccy = self._to_report_ccy(item.total_with_sign_system_ccy)
            pass

        # balance
        item.market_value_report_ccy = self._to_report_ccy(item.market_value_system_ccy)

        # P&L
        item.total_with_sign_system_ccy = item.principal_with_sign_system_ccy + \
                                          item.carry_with_sign_system_ccy + \
                                          item.overheads_with_sign_system_ccy

        item.principal_with_sign_report_ccy = self._to_report_ccy(item.principal_with_sign_system_ccy)
        item.carry_with_sign_system_ccy = self._to_report_ccy(item.carry_with_sign_system_ccy)
        item.overheads_with_sign_system_ccy = self._to_report_ccy(item.overheads_with_sign_system_ccy)
        item.total_with_sign_system_ccy = self._to_report_ccy(item.total_with_sign_system_ccy)
