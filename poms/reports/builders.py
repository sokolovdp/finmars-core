# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division

import logging
from collections import Counter

from django.db.models import Q
from django.utils import timezone
from django.utils.functional import cached_property

from poms.common.utils import isclose
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
    def __init__(self, pk=None, portfolio=None, account=None, strategy1=None, strategy2=None, strategy3=None,
                 instrument=None, currency=None, position=0.0, transaction=None, custom_fields=None):
        self.pk = pk
        self.portfolio = portfolio  # -> Portfolio if use_portfolio
        self.account = account  # -> Account if use_account
        self.strategy1 = strategy1  # -> Strategy1 if use_strategy1
        self.strategy2 = strategy2  # -> Strategy2 if use_strategy2
        self.strategy3 = strategy3  # -> Strategy3 if use_strategy3
        self.instrument = instrument  # -> Instrument
        self.currency = currency  # -> Currency
        self.transaction = transaction  # -> Transaction if show_transaction_details

        self.position = position

        self.custom_fields = custom_fields or {}

    def __str__(self):
        return "%s #%s" % (self.__class__.__name__, self.pk,)


class ReportSummary(object):
    def __init__(self):
        pass

    def __str__(self):
        return "summary"


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
        self.report_date = report_date
        self.report_currency = report_currency
        self.pricing_policy = pricing_policy
        self.cost_method = cost_method

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
        self.summary = summary or ReportSummary()
        self.transactions = transactions or []

    def __str__(self):
        return "%s for %s @ %s" % (self.__class__.__name__, self.master_user, self.report_date)


class ReportBuilder(object):
    def __init__(self, instance=None, queryset=None, transactions=None):
        self.instance = instance
        self._queryset = queryset
        self._filter_date_attr = 'transaction_date'
        self._price_history_cache = {}
        self._currency_history_cache = {}

        self._transactions = transactions

        self._now = timezone.now().date()
        self._report_date = self.instance.report_date or self._now

        self._detail_by_portfolio = self.instance.detail_by_portfolio
        self._detail_by_account = self.instance.detail_by_account
        self._detail_by_strategy1 = self.instance.detail_by_strategy1
        self._detail_by_strategy2 = self.instance.detail_by_strategy2
        self._detail_by_strategy3 = self.instance.detail_by_strategy3

        self._items = {}
        self._invested_items = {}

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
            'master_user',
            # 'complex_transaction',
            # 'complex_transaction__transaction_type',
            'transaction_class',
            'portfolio',
            'instrument',
            'instrument__instrument_type',
            'instrument__instrument_type__instrument_class',
            'instrument__pricing_currency',
            'instrument__accrued_currency',
            'transaction_currency',
            'settlement_currency',
            'account_cash',
            'account_cash__type',
            'account_position',
            'account_position__type',
            'account_interim',
            'account_interim__type',
            'strategy1_position',
            'strategy1_position__subgroup', 'strategy1_position__subgroup__group',
            'strategy1_cash',
            'strategy1_cash__subgroup',
            'strategy1_cash__subgroup__group',
            'strategy2_position',
            'strategy2_position__subgroup',
            'strategy2_position__subgroup__group',
            'strategy2_cash',
            'strategy2_cash__subgroup',
            'strategy2_cash__subgroup__group',
            'strategy3_position',
            'strategy3_position__subgroup',
            'strategy3_position__subgroup__group',
            'strategy3_cash',
            'strategy3_cash__subgroup',
            'strategy3_cash__subgroup__group',
            'responsible',
            'responsible__group',
            'counterparty',
            'counterparty__group',
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

        queryset = queryset.order_by(self._filter_date_attr, 'id')

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

    def _get_instrument_price_history(self, instrument, date=None):
        if not self._price_history_cache:
            self._price_history_cache = {}
            for h in self._get_instrument_price_history_qs():
                self._price_history_cache[(h.instrument_id, h.date)] = h
        date = date or self._report_date
        key = (instrument.id, date)
        try:
            return self._price_history_cache[key]
        except KeyError:
            h = PriceHistory(pricing_policy=self.instance.pricing_policy, instrument=instrument, date=date)
            self._price_history_cache[key] = h
            return h

    def _get_currency_history(self, currency, date=None):
        if not self._currency_history_cache:
            self._currency_history_cache = {}
            for h in self._get_currency_history_qs():
                self._currency_history_cache[(h.currency_id, h.date)] = h
        date = date or self._report_date
        key = (currency.id, date)
        try:
            return self._currency_history_cache[key]
        except KeyError:
            h = CurrencyHistory(pricing_policy=self.instance.pricing_policy, currency=currency, date=date)
            if currency.is_system:
                h.fx_rate = 1.0
            self._currency_history_cache[key] = h
            return h

    @cached_property
    def transactions(self):
        from poms.reports.models import VirtualTransaction

        if self._transactions:
            return self._transactions

        sell = TransactionClass.objects.get(pk=TransactionClass.SELL)
        buy = TransactionClass.objects.get(pk=TransactionClass.BUY)
        fx_trade = TransactionClass.objects.get(pk=TransactionClass.FX_TRADE)

        transactions = [t for t in self._get_transaction_qs()]

        self._annotate_multiplier(transactions)

        transactions1 = []
        for t in transactions:
            self._annotate_transaction_history(t)
            self._annotate_transaction_case(t)

            t_class = t.transaction_class_id
            if t_class == TransactionClass.TRANSFER:
                if t.position_size_with_sign >= 0:
                    t1 = VirtualTransaction(t, '%s:sell' % t.pk,
                                            override_values={
                                                'transaction_class_id': sell.id,
                                                'transaction_class': sell,
                                                'account_position': t.account_cash,
                                                'account_cash': t.account_cash,

                                                'position_size_with_sign': -t.position_size_with_sign,
                                                'cash_consideration': t.cash_consideration,
                                                'principal_with_sign': t.principal_with_sign,
                                                'carry_with_sign': t.carry_with_sign,
                                                'overheads_with_sign': t.overheads_with_sign,
                                            })
                    t2 = VirtualTransaction(t, '%s:buy' % t.pk,
                                            override_values={
                                                'transaction_class_id': buy.id,
                                                'transaction_class': buy,
                                                'account_position': t.account_position,
                                                'account_cash': t.account_position,

                                                'position_size_with_sign': t.position_size_with_sign,
                                                'cash_consideration': -t.cash_consideration,
                                                'principal_with_sign': -t.principal_with_sign,
                                                'carry_with_sign': -t.carry_with_sign,
                                                'overheads_with_sign': -t.overheads_with_sign,
                                            })
                else:
                    t1 = VirtualTransaction(t, '%s:buy' % t.pk,
                                            override_values={
                                                'transaction_class_id': buy.id,
                                                'transaction_class': buy,
                                                'account_position': t.account_cash,
                                                'account_cash': t.account_cash,

                                                'position_size_with_sign': -t.position_size_with_sign,
                                                'cash_consideration': t.cash_consideration,
                                                'principal_with_sign': t.principal_with_sign,
                                                'carry_with_sign': t.carry_with_sign,
                                                'overheads_with_sign': t.overheads_with_sign,
                                            })
                    t2 = VirtualTransaction(t, '%s:sell' % t.pk,
                                            override_values={
                                                'transaction_class_id': sell.id,
                                                'transaction_class': sell,
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
                t1 = VirtualTransaction(t, '%s:sell' % t.pk,
                                        override_values={
                                            'transaction_class_id': fx_trade.id,
                                            'transaction_class': fx_trade,
                                            'account_position': t.account_cash,
                                            'account_cash': t.account_cash,

                                            'position_size_with_sign': -t.position_size_with_sign,
                                            'cash_consideration': t.cash_consideration,
                                            'principal_with_sign': t.principal_with_sign,
                                            'carry_with_sign': t.carry_with_sign,
                                            'overheads_with_sign': t.overheads_with_sign,
                                        })

                t2 = VirtualTransaction(t, '%s:buy' % t.pk,
                                        override_values={
                                            'transaction_class_id': fx_trade.id,
                                            'transaction_class': fx_trade,
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

    def _annotate_transaction_history(self, transaction):
        if transaction.instrument:
            transaction.instrument_price_history = self._get_instrument_price_history(
                transaction.instrument)
            # transaction.instrument_price_history_on_accounting_date = self._get_instrument_price_history(
            #     transaction.instrument, transaction.accounting_date)

            if transaction.instrument.pricing_currency:
                transaction.instrument_pricing_currency_history = self._get_currency_history(
                    transaction.instrument.pricing_currency)
                # transaction.instrument_pricing_currency_history_on_accounting_date = self._get_currency_history(
                #     transaction.instrument.pricing_currency, transaction.accounting_date)
            if transaction.instrument.accrued_currency:
                transaction.instrument_accrued_currency_history = self._get_currency_history(
                    transaction.instrument.accrued_currency)
                # transaction.instrument_accrued_currency_history_on_accounting_date = self._get_currency_history(
                #     transaction.instrument.accrued_currency, transaction.accounting_date)

        if transaction.transaction_currency:
            transaction.transaction_currency_history = self._get_currency_history(
                transaction.transaction_currency)
            # transaction.transaction_currency_history_on_accounting_date = self._get_currency_history(
            #     transaction.transaction_currency, transaction.accounting_date)

        if transaction.settlement_currency:
            transaction.settlement_currency_history = self._get_currency_history(
                transaction.settlement_currency)
            # transaction.settlement_currency_history_on_cash_date = self._get_currency_history(
            #     transaction.settlement_currency, transaction.cash_date)

    def _annotate_multiplier(self, transactions):
        if self._detail_by_portfolio or self._detail_by_account or self._detail_by_strategy1 or self._detail_by_strategy2 or self._detail_by_strategy3:
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
            t_key = self.make_key(portfolio=t.portfolio, account=t.account_position, instrument=t.instrument)

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
            t_key = self.make_key(portfolio=t.portfolio, account=t.account_position, instrument=t.instrument)

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

    def _to_system_ccy(self, value, ccy):
        h = self._get_currency_history(ccy)
        return value * h.fx_rate

    def _system_ccy_to_report_ccy(self, value):
        h = self._get_currency_history(self.instance.report_currency)
        if isclose(h.fx_rate, 0.0):
            return 0.0
        else:
            return value / h.fx_rate

    def _calc_balance_instrument(self, i):
        # i.price_history = self.find_price_history(i.instrument)
        # self.set_price(i, 'instrument')
        price_history = self._get_instrument_price_history(i.instrument)

        instrument_principal_currency_history = self._get_currency_history(i.instrument.pricing_currency)
        instrument_accrued_currency_history = self._get_currency_history(i.instrument.accrued_currency)

        instrument_price_multiplier = i.instrument.price_multiplier if i.instrument.price_multiplier is not None else 1.0
        instrument_accrued_multiplier = i.instrument.accrued_multiplier if i.instrument.accrued_multiplier is not None else 1.0

        # instrument_principal_price = getattr(i.price_history, 'principal_price', 0.) or 0.
        # instrument_accrued_price = getattr(i.price_history, 'accrued_price', 0.) or 0.
        # instrument_principal_price = price_history.principal_price
        # instrument_accrued_price = price_history.accrued_price

        principal_value_instrument_principal_ccy = instrument_price_multiplier * i.position * price_history.principal_price
        accrued_value_instrument_accrued_ccy = instrument_accrued_multiplier * i.position * price_history.accrued_price

        # instrument_principal_fx_rate = getattr(i.instrument_principal_currency_history, 'fx_rate', 0.) or 0.
        # instrument_accrued_fx_rate = getattr(i.instrument_accrued_currency_history, 'fx_rate', 0.) or 0.
        instrument_principal_fx_rate = instrument_principal_currency_history.fx_rate
        instrument_accrued_fx_rate = instrument_accrued_currency_history.fx_rate

        i.principal_value_system_ccy = principal_value_instrument_principal_ccy * instrument_principal_fx_rate
        i.accrued_value_system_ccy = accrued_value_instrument_accrued_ccy * instrument_accrued_fx_rate
        i.market_value_system_ccy = i.principal_value_system_ccy + i.accrued_value_system_ccy

        i.principal_value_report_ccy = self._system_ccy_to_report_ccy(i.principal_value_system_ccy)
        i.accrued_value_report_ccy = self._system_ccy_to_report_ccy(i.accrued_value_system_ccy)
        i.market_value_report_ccy = self._system_ccy_to_report_ccy(i.market_value_system_ccy)

    def _calc_balance_currency(self, i):
        currency_history = self._get_currency_history(i.currency)
        # currency_fx_rate = currency_history.fx_rate

        i.principal_value_system_ccy = i.position * currency_history.fx_rate
        i.market_value_system_ccy = i.principal_value_system_ccy

        i.principal_value_report_ccy = self._system_ccy_to_report_ccy(i.principal_value_system_ccy)
        i.market_value_report_ccy = self._system_ccy_to_report_ccy(i.market_value_system_ccy)

    def _show_transaction_details(self, case, acc):
        if case in [1, 2] and self.instance.show_transaction_details:
            return acc and acc.type and acc.type.show_transaction_details
        return False

    # -----

    def make_key(self, portfolio=None, account=None, instrument=None, currency=None, ext=None,
                 strategy1=None, strategy2=None, strategy3=None):
        portfolio = getattr(portfolio, 'pk', None) if self._detail_by_portfolio else ''
        account = getattr(account, 'pk', None) if self._detail_by_account else ''
        strategy1 = getattr(strategy1, 'pk', None) if self._detail_by_strategy1 else ''
        strategy2 = getattr(strategy2, 'pk', None) if self._detail_by_strategy2 else ''
        strategy3 = getattr(strategy3, 'pk', None) if self._detail_by_strategy3 else ''
        instrument = getattr(instrument, 'pk', None) if instrument else ''
        currency = getattr(currency, 'pk', None) if currency else ''

        ext = ext if ext is not None else ''

        return 'p:%s|s1:%s|s2:%s|s3:%s|a:%s|i:%s|c:%s|e:%s' % (
            portfolio, strategy1, strategy2, strategy3, account, instrument, currency, ext,)

    def make_item(self, key, portfolio=None, account=None, strategy1=None, strategy2=None, strategy3=None,
                  **kwargs):
        item = ReportItem(pk=key,
                          portfolio=portfolio if self._detail_by_portfolio else None,
                          account=account if self._detail_by_account else None,
                          strategy1=strategy1 if self._detail_by_strategy1 else None,
                          strategy2=strategy2 if self._detail_by_strategy2 else None,
                          strategy3=strategy3 if self._detail_by_strategy3 else None,
                          **kwargs)
        return item

    def _get_item0(self, items, trn, instr=None, ccy=None, acc=None, ext=None):
        strategy1 = None
        if self._detail_by_strategy1:
            if instr:
                strategy1 = trn.strategy1_position
            elif ccy:
                strategy1 = trn.strategy1_cash

        strategy2 = None
        if self._detail_by_strategy2:
            if instr:
                strategy2 = trn.strategy2_position
            elif ccy:
                strategy2 = trn.strategy2_cash

        strategy3 = None
        if self._detail_by_strategy3:
            if instr:
                strategy3 = trn.strategy3_position
            elif ccy:
                strategy3 = trn.strategy3_cash

        t_key = self.make_key(portfolio=trn.portfolio, account=acc, instrument=instr, currency=ccy, ext=ext,
                              strategy1=strategy1, strategy2=strategy2, strategy3=strategy3)
        try:
            return items[t_key]
        except KeyError:
            item = self.make_item(key=t_key, portfolio=trn.portfolio, account=acc, instrument=instr,
                                  currency=ccy, strategy1=strategy1, strategy2=strategy2, strategy3=strategy3)
            items[t_key] = item
            return item

    def _get_item(self, trn, instr=None, ccy=None, acc=None, case=None):
        ext = trn.id if self._show_transaction_details(case, acc) else None
        item = self._get_item0(self._items, trn, instr=instr, ccy=ccy, acc=acc, ext=ext)
        if ext:
            item.transaction = trn
        return item

    # -----

    def build(self):
        for t in self.transactions:
            t_class = t.transaction_class_id
            if t_class == TransactionClass.BUY:
                self.process_trnasaction_buy(t)

            elif t_class == TransactionClass.SELL:
                self.process_trnasaction_sell(t)

            elif t_class == TransactionClass.FX_TRADE:
                self.process_trnasaction_fx_trade(t)

            elif t_class == TransactionClass.INSTRUMENT_PL:
                self.process_trnasaction_instrument_pl(t)

            elif t_class == TransactionClass.TRANSACTION_PL:
                self.process_trnasaction_transaction_pl(t)

            elif t_class == TransactionClass.TRANSFER:
                self.process_trnasaction_transfer(t)

            elif t_class == TransactionClass.FX_TRANSFER:
                self.process_trnasaction_fx_transfer(t)

            elif t_class == TransactionClass.CASH_INFLOW:
                self.process_trnasaction_cash_inflow(t)

            elif t_class == TransactionClass.CASH_OUTFLOW:
                self.process_trnasaction_cash_outflow(t)

        raise NotImplementedError('subclasses of BaseReportBuilder must provide an build() method')

    def _process_instrument(self, t):
        if t.case == 0:
            pass

        elif t.case == 1:
            pass

        elif t.case == 2:
            pass

    def _process_cash(self, t):
        if t.case == 0:
            pass

        elif t.case == 1:
            pass

        elif t.case == 2:
            pass

    def process_trnasaction_buy(self, t):
        if self._detail_by_strategy1 or self._detail_by_strategy2 or self._detail_by_strategy3:
            self._process_instrument(t, val=t.position_size_with_sign * (1.0 - t.multiplier), acc=t.account_position)
        else:
            self._process_instrument(t, val=t.position_size_with_sign, acc=t.account_position, case=case)

        self._process_cash(t, ccy=t.settlement_currency, ccy_val=t.cash_consideration,
                           acc=t.account_cash, acc_interim=t.account_interim, case=case)

    def process_trnasaction_sell(self, t):
        pass

    def process_trnasaction_fx_trade(self, t):
        pass

    def process_trnasaction_instrument_pl(self, t):
        pass

    def process_trnasaction_transaction_pl(self, t):
        pass

    def process_trnasaction_transfer(self, t):
        pass

    def process_trnasaction_fx_transfer(self, t):
        pass

    def process_trnasaction_cash_inflow(self, t):
        pass

    def process_trnasaction_cash_outflow(self, t):
        pass
