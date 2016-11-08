# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division

import logging
from collections import Counter, defaultdict
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import ugettext

from poms.common import formula
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
    TYPE_UNKNOWN = 0
    TYPE_INSTRUMENT = 1
    TYPE_CURRENCY = 2
    TYPE_TRANSACTION_PL = 3
    TYPE_FX_TRADE = 4
    TYPE_CHOICES = (
        (TYPE_UNKNOWN, 'Unknown'),
        (TYPE_INSTRUMENT, 'Instrument'),
        (TYPE_CURRENCY, 'Currency'),
        (TYPE_TRANSACTION_PL, 'Transaction PL'),
        (TYPE_FX_TRADE, 'FX-Trade'),
    )

    def __init__(self, pk=None, instrument=None, currency=None,
                 portfolio=None, account=None, strategy1=None, strategy2=None, strategy3=None,
                 detail_transaction=None, transaction_class=None, custom_fields=None,
                 position_size_with_sign=0.0):
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
        self.custom_fields = custom_fields or []

        # balance

        self.position_size_with_sign = position_size_with_sign

        self.market_value_sys_ccy = 0.0
        self.market_value_res_ccy = 0.0

        self.cost_with_sign_sys_ccy = 0.0
        self.cost_with_sign_res_ccy = 0.0

        # P&L

        self.principal_with_sign_sys_ccy = 0.0
        self.carry_with_sign_sys_ccy = 0.0
        self.overheads_with_sign_sys_ccy = 0.0
        self.total_with_sign_sys_ccy = 0.0

        self.real_pl_principal_with_sign_sys_ccy = 0.0
        self.real_pl_carry_with_sign_sys_ccy = 0.0
        self.real_pl_overheads_with_sign_sys_ccy = 0.0
        self.real_pl_total_with_sign_sys_ccy = 0.0

        self.unreal_pl_principal_with_sign_sys_ccy = 0.0
        self.unreal_pl_carry_with_sign_sys_ccy = 0.0
        self.unreal_pl_overheads_with_sign_sys_ccy = 0.0
        self.unreal_pl_total_with_sign_sys_ccy = 0.0

        self.principal_with_sign_res_ccy = 0.0
        self.carry_with_sign_res_ccy = 0.0
        self.overheads_with_sign_res_ccy = 0.0
        self.total_with_sign_res_ccy = 0.0

        self.real_pl_principal_with_sign_res_ccy = 0.0
        self.real_pl_carry_with_sign_res_ccy = 0.0
        self.real_pl_overheads_with_sign_res_ccy = 0.0
        self.real_pl_total_with_sign_res_ccy = 0.0

        self.unreal_pl_principal_with_sign_res_ccy = 0.0
        self.unreal_pl_carry_with_sign_res_ccy = 0.0
        self.unreal_pl_overheads_with_sign_res_ccy = 0.0
        self.unreal_pl_total_with_sign_res_ccy = 0.0

    def __str__(self):
        return "%s #%s" % (self.__class__.__name__, self.pk,)

    @property
    def is_zero(self):
        return isclose(self.position_size_with_sign, 0.0) \
               and isclose(self.market_value_sys_ccy, 0.0) \
               and isclose(self.principal_with_sign_sys_ccy, 0.0) \
               and isclose(self.carry_with_sign_sys_ccy, 0.0) \
               and isclose(self.overheads_with_sign_sys_ccy, 0.0) \
               and isclose(self.total_with_sign_sys_ccy, 0.0)

    @property
    def type(self):
        if self.instrument:
            return ReportItem.TYPE_INSTRUMENT
        elif self.currency:
            return ReportItem.TYPE_CURRENCY
        elif self.transaction_class:
            if self.transaction_class.id == TransactionClass.TRANSACTION_PL:
                return ReportItem.TYPE_TRANSACTION_PL
            elif self.transaction_class.id == TransactionClass.FX_TRADE:
                return ReportItem.TYPE_FX_TRADE
        return ReportItem.TYPE_UNKNOWN

    @property
    def type_name(self):
        t = self.type
        for i, n in ReportItem.TYPE_CHOICES:
            if i == t:
                return n
        return 'ERR'

    @property
    def type_code(self):
        t = self.type
        if t == ReportItem.TYPE_UNKNOWN:
            return 'UNKN'
        elif t == ReportItem.TYPE_INSTRUMENT:
            return 'INSTR'
        elif t == ReportItem.TYPE_CURRENCY:
            return 'CCY'
        elif t == ReportItem.TYPE_TRANSACTION_PL:
            return 'TRN PL'
        elif t == ReportItem.TYPE_FX_TRADE:
            return 'FX TRADE'
        else:
            return 'ERR'

    @property
    def user_code(self):
        if self.instrument:
            return self.instrument.user_code
        elif self.currency:
            return self.currency.user_code
        elif self.transaction_class:
            if self.transaction_class.id in [TransactionClass.TRANSACTION_PL, TransactionClass.FX_TRADE]:
                return self.transaction_class.system_code
        return ''

    @property
    def name(self):
        if self.instrument:
            return self.instrument.name
        elif self.currency:
            return self.currency.name
        elif self.transaction_class:
            if self.transaction_class.id in [TransactionClass.TRANSACTION_PL, TransactionClass.FX_TRADE]:
                return self.transaction_class.name
        return ''


class ReportSummary(object):
    def __init__(self):
        # balance
        self.market_value_sys_ccy = 0.0
        self.market_value_res_ccy = 0.0

        self.cost_with_sign_sys_ccy = 0.0
        self.cost_with_sign_res_ccy = 0.0

        # P&L
        self.principal_with_sign_sys_ccy = 0.0
        self.carry_with_sign_sys_ccy = 0.0
        self.overheads_with_sign_sys_ccy = 0.0
        self.total_with_sign_sys_ccy = 0.0

        self.real_pl_principal_with_sign_sys_ccy = 0.0
        self.real_pl_carry_with_sign_sys_ccy = 0.0
        self.real_pl_overheads_with_sign_sys_ccy = 0.0
        self.real_pl_total_with_sign_sys_ccy = 0.0

        # self.unreal_pl_principal_with_sign_sys_ccy = 0.0
        # self.unreal_pl_carry_with_sign_sys_ccy = 0.0
        # self.unreal_pl_overheads_with_sign_sys_ccy = 0.0
        self.unreal_pl_total_with_sign_sys_ccy = 0.0

        self.principal_with_sign_res_ccy = 0.0
        self.carry_with_sign_res_ccy = 0.0
        self.overheads_with_sign_res_ccy = 0.0
        self.total_with_sign_res_ccy = 0.0

        self.real_pl_principal_with_sign_res_ccy = 0.0
        self.real_pl_carry_with_sign_res_ccy = 0.0
        self.real_pl_overheads_with_sign_res_ccy = 0.0
        self.real_pl_total_with_sign_res_ccy = 0.0

        # self.unreal_pl_principal_with_sign_res_ccy = 0.0
        # self.unreal_pl_carry_with_sign_res_ccy = 0.0
        # self.unreal_pl_overheads_with_sign_res_ccy = 0.0
        self.unreal_pl_total_with_sign_res_ccy = 0.0

    def __str__(self):
        return "summary"


class Report(object):
    def __init__(self, id=None, master_user=None, task_id=None, task_status=None,
                 report_date=None, report_currency=None, pricing_policy=None, cost_method=None,
                 detail_by_portfolio=False, detail_by_account=False, detail_by_strategy1=False,
                 detail_by_strategy2=False, detail_by_strategy3=False,
                 show_transaction_details=False,
                 portfolios=None, accounts=None, strategies1=None, strategies2=None, strategies3=None,
                 transaction_classes=None, date_field=None,
                 custom_fields=None, items=None, summary=None):
        self.id = id
        self.task_id = task_id
        self.task_status = task_status

        self.master_user = master_user
        self.pricing_policy = pricing_policy
        self.report_date = report_date or (date_now() - timedelta(days=1))
        self.report_currency = report_currency or master_user.system_currency
        self.cost_method = cost_method or CostMethod.objects.get(pk=CostMethod.AVCO)
        self.pl_real_unreal_end_multiplier = 0.5

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
        self.transaction_classes = transaction_classes or []
        self.date_field = date_field or 'transaction_date'

        self.custom_fields = custom_fields or []

        self.items = items or []
        self.invested_items = items or []
        self.summary = ReportSummary()
        if items:
            self.summary.add_items(items)
        self.summary = summary or ReportSummary()
        self.transactions = []

    def __str__(self):
        return "%s for %s @ %s" % (self.__class__.__name__, self.master_user, self.report_date)


class ReportBuilder(object):
    def __init__(self, instance=None, queryset=None, transactions=None):
        self.instance = instance
        self._queryset = queryset
        self._filter_date_attr = self.instance.date_field

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
        self._invested_items = {}

    @property
    def _system_currency(self):
        return self.instance.master_user.system_currency

    @cached_property
    def _transaction_class_sell(self):
        return TransactionClass.objects.get(pk=TransactionClass.SELL)

    @cached_property
    def _transaction_class_buy(self):
        return TransactionClass.objects.get(pk=TransactionClass.BUY)

    @cached_property
    def _transaction_class_fx_trade(self):
        return TransactionClass.objects.get(pk=TransactionClass.FX_TRADE)

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

        if self.instance.transaction_classes:
            queryset = queryset.filter(transaction_class__in=self.instance.transaction_classes)

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
        report_currency = self.instance.report_currency or self._system_currency
        return CurrencyHistory.objects.filter(
            pricing_policy=self.instance.pricing_policy
        ).filter(
            Q(date=self._report_date) |
            Q(date__in=transaction_qs.values_list('cash_date', flat=True)) |
            Q(date__in=transaction_qs.values_list('accounting_date', flat=True))
        ).filter(
            Q(currency=report_currency) |
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
    def transactions(self):
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

    # def _annotate_multiplier(self, transactions):
    #     if self._any_details:
    #         self._annotate_multiplier1(transactions)
    #         pass
    #     else:
    #         for t in transactions:
    #             t.multiplier = 0.0

    def _annotate_multiplier(self, transactions):
        rolling_positions = Counter()
        items = defaultdict(list)

        for i, t in enumerate(transactions):
            if t.transaction_class_id not in [TransactionClass.BUY, TransactionClass.SELL]:
                continue

            # print('-----')
            # print(i, t.id)

            # do not use strategy!!!
            t_key = self._make_key(
                instrument=t.instrument,
                portfolio=t.portfolio if self._detail_by_portfolio else None,
                account=t.account_position if self._detail_by_account else  None
            )

            real_pl_changes = []

            t.multiplier = 0.0
            t.cost_with_sign = 0.0
            t.balance_position_size_with_sign = 0.0

            t.real_pl_principal_with_sign = 0.0
            t.real_pl_carry_with_sign = 0.0
            t.real_pl_overheads_with_sign = 0.0
            t.real_pl_total_with_sign = 0.0

            t.unreal_pl_principal_with_sign = 0.0
            t.unreal_pl_carry_with_sign = 0.0
            t.unreal_pl_overheads_with_sign = 0.0
            t.unreal_pl_total_with_sign = 0.0

            rolling_position = rolling_positions[t_key]

            if isclose(rolling_position, 0.0):
                k = -1
            else:
                k = - t.position_size_with_sign / rolling_position

            if self.instance.cost_method.id == CostMethod.AVCO:

                if k > 1.0:
                    if t_key in items:
                        for t0 in items[t_key]:
                            self._set_multiplier(real_pl_changes, t0, 1.0)
                        del items[t_key]
                    items[t_key].append(t)
                    self._set_multiplier(real_pl_changes, t, 1.0 / k)
                    rolling_position = t.position_size_with_sign * (1.0 - t.multiplier)

                elif isclose(k, 1.0):
                    if t_key in items:
                        for t0 in items[t_key]:
                            self._set_multiplier(real_pl_changes, t0, 1.0)
                        del items[t_key]
                    self._set_multiplier(real_pl_changes, t, 1.0)
                    rolling_position = 0.0

                elif k > 0.0:
                    if t_key in items:
                        for t0 in items[t_key]:
                            self._set_multiplier(real_pl_changes, t0, t0.multiplier + k * (1.0 - t0.multiplier))
                    self._set_multiplier(real_pl_changes, t, 1.0)
                    rolling_position += t.position_size_with_sign

                else:
                    items[t_key].append(t)
                    rolling_position += t.position_size_with_sign

            elif self.instance.cost_method.id == CostMethod.FIFO:

                if k > 1.0:
                    if t_key in items:
                        for t0 in items[t_key]:
                            self._set_multiplier(real_pl_changes, t0, 1.0)
                        items[t_key].clear()
                    items[t_key].append(t)
                    self._set_multiplier(real_pl_changes, t, 1.0 / k)
                    rolling_position = t.position_size_with_sign * (1.0 - t.multiplier)

                elif isclose(k, 1.0):
                    if t_key in items:
                        for t0 in items[t_key]:
                            self._set_multiplier(real_pl_changes, t0, 1.0)
                        del items[t_key]
                    self._set_multiplier(real_pl_changes, t, 1.0)
                    rolling_position = 0.0

                elif k > 0.0:
                    position = t.position_size_with_sign
                    if t_key in items:
                        t_items = items[t_key]
                        for t0 in t_items:
                            remaining = t0.position_size_with_sign * (1.0 - t0.multiplier)
                            k0 = - position / remaining
                            if k0 > 1.0:
                                self._set_multiplier(real_pl_changes, t0, 1.0)
                                position += remaining
                            elif isclose(k0, 1.0):
                                self._set_multiplier(real_pl_changes, t0, 1.0)
                                position += remaining
                            elif k0 > 0.0:
                                position += remaining * k0
                                self._set_multiplier(real_pl_changes, t0, t0.multiplier + k0 * (1.0 - t0.multiplier))
                            # else:
                            #     break
                            if isclose(position, 0.0):
                                break
                        t_items = [t0 for t0 in t_items if not isclose(t0.multiplier, 1.0)]
                        if t_items:
                            items[t_key] = t_items
                        else:
                            del items[t_key]

                    self._set_multiplier(real_pl_changes, t,
                                         abs((t.position_size_with_sign - position) / t.position_size_with_sign))
                    rolling_position += t.position_size_with_sign * t.multiplier

                else:
                    items[t_key].append(t)
                    rolling_position += t.position_size_with_sign

            rolling_positions[t_key] = rolling_position
            # print('i =', i, ', rolling_positions =', rolling_position)

            self._pl_real(real_pl_changes)

        for t in transactions:
            if t.transaction_class_id not in [TransactionClass.BUY, TransactionClass.SELL]:
                continue
            t.balance_position_size_with_sign = t.position_size_with_sign * (1.0 - t.multiplier)
            t.cost_with_sign = t.principal_with_sign * (1.0 - t.multiplier)

        self._pl_unreal(transactions)

    def _set_multiplier(self, real_pl_changes, t, multiplier):
        old_multiplier = t.multiplier
        if not isclose(old_multiplier, multiplier):
            # print('\t', t.id, str(t.transaction_class)[0], t.instrument, old_multiplier, multiplier)
            pass
        t.multiplier = multiplier
        inc_multiplier = t.multiplier - old_multiplier

        real_pl_changes.append((t, inc_multiplier))

    def _pl_real(self, real_pl_changes):
        if real_pl_changes:
            init_mult = 1 - self.instance.pl_real_unreal_end_multiplier
            end_mult = self.instance.pl_real_unreal_end_multiplier

            t, inc_multiplier = real_pl_changes[-1]

            # sum_principal = 0.0
            # sum_carry = 0.0
            # sum_overheads = 0.0
            sum_total = 0.0
            for t0, inc_multiplier0 in real_pl_changes:
                # sum_principal += t0.principal_with_sign * inc_multiplier0
                # sum_carry += t0.carry_with_sign * inc_multiplier0
                # sum_overheads += t0.overheads_with_sign * inc_multiplier0
                sum_total += (t0.principal_with_sign + t0.carry_with_sign + t0.overheads_with_sign) * inc_multiplier0

            for t0, inc_multiplier0 in real_pl_changes:
                mult = end_mult if t0.id == t.id else init_mult

                matched = abs((t0.position_size_with_sign * inc_multiplier0) / (
                    t.position_size_with_sign * inc_multiplier))
                # adj = matched * mult

                # t0.real_pl_principal_with_sign += sum_principal * matched * mult
                # t0.real_pl_carry_with_sign += sum_carry * matched * mult
                # t0.real_pl_overheads_with_sign += sum_overheads * matched * mult
                t0.real_pl_total_with_sign += sum_total * matched * mult

    def _pl_unreal(self, transactions):
        # for t in transactions:
        #     if t.transaction_class_id not in [TransactionClass.BUY, TransactionClass.SELL]:
        #         continue
        #     t.unreal_pl_principal_with_sign = t.principal_with_sign * (1.0 - t.multiplier)
        #     t.unreal_pl_carry_with_sign = t.carry_with_sign * (1.0 - t.multiplier)
        #     t.unreal_pl_overheads_with_sign = t.overheads_with_sign * (1.0 - t.multiplier)
        #     t.unreal_pl_total_with_sign = t.unreal_pl_principal_with_sign + t.unreal_pl_carry_with_sign + t.unreal_pl_overheads_with_sign
        pass

    # def _annotate_avco_multiplier(self, transactions):
    #     in_stock = OrderedDict()
    #     not_closed = OrderedDict()
    #     rolling_positions = Counter()
    #
    #     def _set_multiplier(t, multiplier):
    #         old_multiplier = t.multiplier
    #         if not isclose(old_multiplier, multiplier):
    #             print('\t', t.id, str(t.transaction_class)[0], t.instrument, old_multiplier, multiplier)
    #         t.multiplier = multiplier
    #
    #     print('1' * 10)
    #     for t in transactions:
    #         if t.transaction_class_id not in [TransactionClass.BUY, TransactionClass.SELL]:
    #             continue
    #         print(t.id, str(t.transaction_class)[0], t.instrument)
    #
    #     print('2' * 10)
    #     for t in transactions:
    #         if t.transaction_class_id not in [TransactionClass.BUY, TransactionClass.SELL]:
    #             continue
    #
    #         print('-' * 10)
    #         print(t.id, str(t.transaction_class)[0], t.instrument)
    #
    #         # do not use strategy!!!
    #         t_key = self._make_key(
    #             instrument=t.instrument,
    #             portfolio=t.portfolio if self._detail_by_portfolio else None,
    #             account=t.account_position if self._detail_by_account else  None
    #         )
    #
    #         t.multiplier = 0.0
    #         position_size_with_sign = t.position_size_with_sign
    #         rolling_position = rolling_positions[t_key]
    #
    #         # if position_size_with_sign > 0.:  # покупка
    #         if t.transaction_class_id == TransactionClass.BUY:
    #             i_not_closed = not_closed.get(t_key, [])
    #             if i_not_closed:  # есть прошлые продажи, которые надо закрыть
    #                 if position_size_with_sign + rolling_position >= 0.0:  # все есть
    #                     # t.multiplier = abs(rolling_position / position_size_with_sign)
    #                     _set_multiplier(t, abs(rolling_position / position_size_with_sign))
    #                     for t0 in i_not_closed:
    #                         # t0.multiplier = 1.0
    #                         _set_multiplier(t0, 1.0)
    #                     in_stock[t_key] = in_stock.get(t_key, []) + [t]
    #                 else:  # только частично
    #                     # t.multiplier = 1.0
    #                     _set_multiplier(t, 1.0)
    #                     for t0 in i_not_closed:
    #                         # t0.multiplier += abs((1.0 - t0.multiplier) * position_size_with_sign / rolling_position)
    #                         _set_multiplier(t0, abs((1.0 - t0.multiplier) * position_size_with_sign / rolling_position))
    #                 not_closed[t_key] = [t0 for t0 in i_not_closed if t0.multiplier < 1.0]
    #             else:  # новая "чистая" покупка
    #                 # t.multiplier = 0.0
    #                 _set_multiplier(t, 0.0)
    #                 in_stock[t_key] = in_stock.get(t_key, []) + [t]
    #
    #         # else:  # продажа
    #         elif t.transaction_class_id == TransactionClass.SELL:
    #             i_in_stock = in_stock.get(t_key, [])
    #             if i_in_stock:  # есть что продавать
    #                 if position_size_with_sign + rolling_position >= 0.0:  # все есть
    #                     # t.multiplier = 1.0
    #                     _set_multiplier(t, 1.0)
    #                     for t0 in i_in_stock:
    #                         # t0.multiplier += abs((1.0 - t0.multiplier) * position_size_with_sign / rolling_position)
    #                         _set_multiplier(t0, abs((1.0 - t0.multiplier) * position_size_with_sign / rolling_position))
    #                 else:  # только частично
    #                     # t.multiplier = abs(rolling_position / position_size_with_sign)
    #                     _set_multiplier(t, abs(rolling_position / position_size_with_sign))
    #                     for t0 in i_in_stock:
    #                         # t0.multiplier = 1.0
    #                         _set_multiplier(t0, 1.0)
    #                     not_closed[t_key] = not_closed.get(t_key, []) + [t]
    #                 in_stock[t_key] = [t0 for t0 in i_in_stock if t0.multiplier < 1.0]
    #             else:  # нечего продавать
    #                 # t.multiplier = 0.0
    #                 _set_multiplier(t, 0.0)
    #                 not_closed[t_key] = not_closed.get(t_key, []) + [t]
    #
    #         rolling_position += position_size_with_sign
    #         rolling_positions[t_key] = rolling_position
    #         t.rolling_position = rolling_position

    # def _annotate_fifo_multiplier(self, transactions):
    #     in_stock = {}
    #     not_closed = {}
    #     rolling_positions = Counter()
    #
    #     for t in transactions:
    #         if t.transaction_class_id not in [TransactionClass.BUY, TransactionClass.SELL]:
    #             continue
    #
    #         # do not use strategy!!!
    #         # t_key = self._make_key(portfolio=t.portfolio, account=t.account_position, instrument=t.instrument)
    #         t_key = self._make_key(
    #             instrument=t.instrument,
    #             portfolio=t.portfolio if self._detail_by_portfolio else None,
    #             account=t.account_position if self._detail_by_account else  None
    #         )
    #
    #         t.multiplier = 0.0
    #         position_size_with_sign = t.position_size_with_sign
    #         rolling_position = rolling_positions[t_key]
    #
    #         # if position_size_with_sign > 0.:  # покупка
    #         if t.transaction_class_id == TransactionClass.BUY:
    #             i_not_closed = not_closed.get(t_key, [])
    #             balance = position_size_with_sign
    #             if i_not_closed:
    #                 for t0 in i_not_closed:
    #                     sale = t0.not_closed
    #                     if balance + sale > 0.0:  # есть все
    #                         balance -= abs(sale)
    #                         t0.multiplier = 1.0
    #                         t0.not_closed = t0.not_closed - abs(t0.position_size_with_sign)
    #                     else:
    #                         t0.not_closed = t0.not_closed + balance
    #                         t0.multiplier = 1.0 - abs(t0.not_closed / t0.position_size_with_sign)
    #                         balance = 0.0
    #                     if balance <= 0.0:
    #                         break
    #                 not_closed[t_key] = [t0 for t0 in i_not_closed if t0.multiplier < 1.0]
    #             t.balance = balance
    #             t.multiplier = abs((position_size_with_sign - balance) / position_size_with_sign)
    #             if t.multiplier < 1.0:
    #                 in_stock[t_key] = in_stock.get(t_key, []) + [t]
    #
    #         # else:  # продажа
    #         elif t.transaction_class_id == TransactionClass.SELL:
    #             i_in_stock = in_stock.get(t_key, [])
    #             sale = position_size_with_sign
    #             if i_in_stock:
    #                 for t0 in i_in_stock:
    #                     balance = t0.balance
    #                     if sale + balance > 0.0:  # есть все
    #                         t0.balance = balance - abs(sale)
    #                         t0.multiplier = abs((t0.position_size_with_sign - t0.balance) / t0.position_size_with_sign)
    #                         sale = 0.0
    #                     else:
    #                         t0.balance = 0.0
    #                         t0.multiplier = 1.0
    #                         sale += abs(balance)
    #                     if sale >= 0.0:
    #                         break
    #                 in_stock[t_key] = [t0 for t0 in i_in_stock if t0.multiplier < 1.0]
    #             t.not_closed = sale
    #             t.multiplier = abs((position_size_with_sign - sale) / position_size_with_sign)
    #             if t.multiplier < 1.0:
    #                 not_closed[t_key] = not_closed.get(t_key, []) + [t]
    #
    #         rolling_position += position_size_with_sign
    #         rolling_positions[t_key] = rolling_position
    #         t.rolling_position = rolling_position
    #
    #     for t in transactions:
    #         if t.transaction_class_id in [TransactionClass.BUY, TransactionClass.SELL]:
    #             t.multiplier = t.multiplier

    def _annotate_transaction_case(self, t):
        if t.accounting_date <= self._report_date < t.cash_date:  # default
            t.case = 1
        elif t.cash_date <= self._report_date < t.accounting_date:
            t.case = 2
        else:
            t.case = 0

    def build(self):
        for trn in self.transactions:
            if trn.transaction_class_id == TransactionClass.BUY:
                self._process_transaction_buy(trn)

            elif trn.transaction_class_id == TransactionClass.SELL:
                self._process_transaction_sell(trn)

            elif trn.transaction_class_id == TransactionClass.FX_TRADE:
                self._process_transaction_fx_trade(trn)

            elif trn.transaction_class_id == TransactionClass.INSTRUMENT_PL:
                self._process_transaction_instrument_pl(trn)

            elif trn.transaction_class_id == TransactionClass.TRANSACTION_PL:
                self._process_transaction_transaction_pl(trn)

            elif trn.transaction_class_id == TransactionClass.TRANSFER:
                self._process_transaction_transfer(trn)

            elif trn.transaction_class_id == TransactionClass.FX_TRANSFER:
                self._process_transaction_fx_transfer(trn)

            elif trn.transaction_class_id == TransactionClass.CASH_INFLOW:
                self._process_transaction_cash_inflow(trn)

            elif trn.transaction_class_id == TransactionClass.CASH_OUTFLOW:
                self._process_transaction_cash_outflow(trn)

            else:
                raise RuntimeError('Invalid transaction class: %s' % trn.transaction_class_id)

        self._process_final(self._invested_items.values())
        self.instance.invested_items = sorted([i for i in self._invested_items.values()], key=lambda x: x.pk)

        self._process_final(self._items.values())
        self.instance.items = sorted([i for i in self._items.values()], key=lambda x: x.pk)
        self._process_summary(self.instance.summary, self.instance.items)

        self._process_custom_fields(self.instance.items)

        return self.instance

    def _process_transaction_buy(self, trn):
        # if self._any_details:
        #     position_size_with_sign = trn.position_size_with_sign * (1.0 - trn.multiplier)
        # else:
        #     position_size_with_sign = trn.position_size_with_sign

        self._add_instr(self._items, trn, value=trn.balance_position_size_with_sign)
        self._add_cash(self._items, trn, value=trn.cash_consideration, currency=trn.settlement_currency)

    def _process_transaction_sell(self, trn):
        self._process_transaction_buy(trn)

    def _process_transaction_fx_trade(self, trn):
        # TODO: Что используем для strategy?
        self._add_cash(self._items, trn, value=trn.position_size_with_sign, currency=trn.transaction_currency,
                       account=trn.account_position, strategy1=trn.strategy1_position,
                       strategy2=trn.strategy2_position, strategy3=trn.strategy3_position, )

        self._add_cash(self._items, trn, value=trn.cash_consideration, currency=trn.settlement_currency)

        # P&L
        item = self._get_item(self._items, trn, portfolio=trn.portfolio, account=trn.account_position,
                              strategy1=trn.strategy1_position, strategy2=trn.strategy2_position,
                              strategy3=trn.strategy3_position, transaction_class=trn.transaction_class)
        item.principal_with_sign_sys_ccy += \
            self._to_sys_ccy(trn.position_size_with_sign, trn.transaction_currency) + \
            self._to_sys_ccy(trn.principal_with_sign, trn.settlement_currency)
        # item.carry_with_sign_sys_ccy += self._to_sys_ccy(trn.carry_with_sign, trn.settlement_currency)
        item.overheads_with_sign_sys_ccy += self._to_sys_ccy(trn.overheads_with_sign, trn.settlement_currency)

    def _process_transaction_instrument_pl(self, trn):
        self._add_instr(self._items, trn, value=trn.position_size_with_sign)
        self._add_cash(self._items, trn, value=trn.cash_consideration, currency=trn.settlement_currency)

    def _process_transaction_transaction_pl(self, trn):
        item = self._get_item(self._items, trn, portfolio=trn.portfolio, account=trn.account_position,
                              strategy1=trn.strategy1_position, strategy2=trn.strategy2_position,
                              strategy3=trn.strategy3_position, transaction_class=trn.transaction_class)

        self._add_cash(self._items, trn, value=trn.cash_consideration, currency=trn.settlement_currency)

        item.principal_with_sign_sys_ccy += self._to_sys_ccy(trn.principal_with_sign, trn.settlement_currency)
        item.carry_with_sign_sys_ccy += self._to_sys_ccy(trn.carry_with_sign, trn.settlement_currency)
        item.overheads_with_sign_sys_ccy += self._to_sys_ccy(trn.overheads_with_sign, trn.settlement_currency)

    def _process_transaction_transfer(self, trn):
        raise RuntimeError('Virtual transaction must be created')

    def _process_transaction_fx_transfer(self, trn):
        raise RuntimeError('Virtual transaction must be created')

    def _process_transaction_cash_inflow(self, trn):
        self._add_cash(self._items, trn, value=trn.position_size_with_sign, currency=trn.transaction_currency,
                       account=trn.account_position, strategy1=trn.strategy1_position, strategy2=trn.strategy2_position,
                       strategy3=trn.strategy3_position)

        # invested cash
        self._add_cash(self._invested_items, trn, value=trn.position_size_with_sign, currency=trn.transaction_currency,
                       account=trn.account_position, strategy1=trn.strategy1_position, strategy2=trn.strategy2_position,
                       strategy3=trn.strategy3_position)

    def _process_transaction_cash_outflow(self, t):
        self._process_transaction_cash_inflow(t)

    def _add_instr(self, items, trn, value,
                   portfolio=None, account=None, strategy1=None, strategy2=None, strategy3=None):
        if portfolio is None:
            portfolio = trn.portfolio
        if account is None:
            account = trn.account_position
        if strategy1 is None:
            strategy1 = trn.strategy1_position
        if strategy2 is None:
            strategy2 = trn.strategy2_position
        if strategy3 is None:
            strategy3 = trn.strategy3_position

        if trn.case == 0:
            item = self._get_item(items, trn, instrument=trn.instrument, portfolio=portfolio, account=account,
                                  strategy1=strategy1, strategy2=strategy2, strategy3=strategy3)
        elif trn.case == 1:
            item = self._get_item(items, trn, instrument=trn.instrument, portfolio=portfolio, account=account,
                                  strategy1=strategy1, strategy2=strategy2, strategy3=strategy3)

        elif trn.case == 2:
            return

        else:
            raise RuntimeError('Invalid transaction case: %s' % trn.case)

        if item:
            ccy = trn.settlement_currency
            # balance
            item.position_size_with_sign += value
            item.cost_with_sign_sys_ccy += self._to_sys_ccy(trn.cost_with_sign, ccy)

            #  P&L
            item.principal_with_sign_sys_ccy += self._to_sys_ccy(trn.principal_with_sign, ccy)
            item.carry_with_sign_sys_ccy += self._to_sys_ccy(trn.carry_with_sign, ccy)
            item.overheads_with_sign_sys_ccy += self._to_sys_ccy(trn.overheads_with_sign, ccy)

            # item.real_pl_principal_with_sign_sys_ccy += self._to_sys_ccy(trn.real_pl_principal_with_sign, ccy)
            # item.real_pl_carry_with_sign_sys_ccy += self._to_sys_ccy(trn.real_pl_carry_with_sign, ccy)
            # item.real_pl_overheads_with_sign_sys_ccy += self._to_sys_ccy(trn.real_pl_overheads_with_sign, ccy)
            item.real_pl_total_with_sign_sys_ccy += self._to_sys_ccy(trn.real_pl_total_with_sign, ccy)

            # item.unreal_pl_principal_with_sign_sys_ccy += self._to_sys_ccy(trn.unreal_pl_principal_with_sign,ccy)
            # item.unreal_pl_carry_with_sign_sys_ccy += self._to_sys_ccy(trn.unreal_pl_carry_with_sign,ccy)
            # item.unreal_pl_overheads_with_sign_sys_ccy += self._to_sys_ccy(trn.unreal_pl_overheads_with_sign,ccy)
            # item.unreal_pl_total_with_sign_sys_ccy += self._to_sys_ccy(trn.unreal_pl_total_with_sign,ccy)
            pass

    def _add_cash(self, items, trn, value, currency,
                  portfolio=None, account=None, account_interim=None, strategy1=None, strategy2=None, strategy3=None):

        if portfolio is None:
            portfolio = trn.portfolio
        if account is None:
            account = trn.account_cash
        if account_interim is None:
            account_interim = trn.account_interim
        if strategy1 is None:
            strategy1 = trn.strategy1_cash
        if strategy2 is None:
            strategy2 = trn.strategy2_cash
        if strategy3 is None:
            strategy3 = trn.strategy3_cash

        if trn.case == 0:
            item = self._get_item(items, trn, currency=currency, portfolio=portfolio, account=account,
                                  strategy1=strategy1, strategy2=strategy2, strategy3=strategy3)
            item.position_size_with_sign += value

        elif trn.case == 1:
            item = self._get_item(items, trn, currency=currency, portfolio=portfolio, account=account_interim,
                                  strategy1=strategy1, strategy2=strategy2, strategy3=strategy3)
            item.position_size_with_sign += value

        elif trn.case == 2:
            item = self._get_item(items, trn, currency=currency, portfolio=portfolio, account=account,
                                  strategy1=strategy1, strategy2=strategy2, strategy3=strategy3)
            item.position_size_with_sign += value

            item = self._get_item(items, trn, currency=currency, portfolio=trn.portfolio, account=account_interim,
                                  strategy1=strategy1, strategy2=strategy2, strategy3=strategy3)
            item.position_size_with_sign += value

        else:
            raise RuntimeError('Invalid transaction case: %s' % trn.case)

    def _process_final(self, items):
        for item in items:
            if item.instrument:
                price = self._get_instrument_price_history(item.instrument)

                principal = item.position_size_with_sign * item.instrument.price_multiplier * price.principal_price
                accrued = item.position_size_with_sign * item.instrument.accrued_multiplier * price.accrued_price

                principal_sys_ccy = self._to_sys_ccy(principal, item.instrument.pricing_currency)
                accrued_sys_ccy = self._to_sys_ccy(accrued, item.instrument.accrued_currency)

                # balance
                item.market_value_sys_ccy = principal_sys_ccy + accrued_sys_ccy

                # P&L
                item.principal_with_sign_sys_ccy += principal_sys_ccy
                item.carry_with_sign_sys_ccy += accrued_sys_ccy

            elif item.currency:
                # balance
                item.market_value_sys_ccy = self._to_sys_ccy(item.position_size_with_sign, item.currency)

                # P&L
                pass

            # balance
            item.market_value_res_ccy = self._to_res_ccy(item.market_value_sys_ccy)
            item.cost_with_sign_res_ccy = self._to_res_ccy(item.cost_with_sign_sys_ccy)

            # P&L
            item.total_with_sign_sys_ccy = item.principal_with_sign_sys_ccy + \
                                           item.carry_with_sign_sys_ccy + \
                                           item.overheads_with_sign_sys_ccy

            item.principal_with_sign_res_ccy = self._to_res_ccy(item.principal_with_sign_sys_ccy)
            item.carry_with_sign_res_ccy = self._to_res_ccy(item.carry_with_sign_sys_ccy)
            item.overheads_with_sign_res_ccy = self._to_res_ccy(item.overheads_with_sign_sys_ccy)
            item.total_with_sign_res_ccy = self._to_res_ccy(item.total_with_sign_sys_ccy)

            if item.instrument:
                # item.real_pl_principal_with_sign_res_ccy = self._to_res_ccy(item.real_pl_principal_with_sign_sys_ccy)
                # item.real_pl_carry_with_sign_res_ccy = self._to_res_ccy(item.real_pl_carry_with_sign_sys_ccy)
                # item.real_pl_overheads_with_sign_res_ccy = self._to_res_ccy(item.real_pl_overheads_with_sign_sys_ccy)
                item.real_pl_total_with_sign_res_ccy = self._to_res_ccy(item.real_pl_total_with_sign_sys_ccy)

                # item.unreal_pl_principal_with_sign_res_ccy = self._to_res_ccy(
                #     item.unreal_pl_principal_with_sign_sys_ccy)
                # item.unreal_pl_carry_with_sign_res_ccy = self._to_res_ccy(
                #     item.unreal_pl_carry_with_sign_sys_ccy)
                # item.unreal_pl_overheads_with_sign_res_ccy = self._to_res_ccy(
                #     item.unreal_pl_overheads_with_sign_sys_ccy)
                item.unreal_pl_total_with_sign_sys_ccy = item.market_value_res_ccy + item.cost_with_sign_sys_ccy

    def _process_summary(self, summary, items):
        for item in items:
            summary.market_value_sys_ccy += item.market_value_sys_ccy
            summary.market_value_res_ccy += item.market_value_res_ccy

            summary.cost_with_sign_sys_ccy += item.cost_with_sign_sys_ccy
            summary.cost_with_sign_res_ccy += item.cost_with_sign_res_ccy

            # P&L
            summary.principal_with_sign_sys_ccy += item.principal_with_sign_sys_ccy
            summary.carry_with_sign_sys_ccy += item.carry_with_sign_sys_ccy
            summary.overheads_with_sign_sys_ccy += item.overheads_with_sign_sys_ccy
            summary.total_with_sign_sys_ccy += item.total_with_sign_sys_ccy

            # summary.real_pl_principal_with_sign_sys_ccy += item.real_pl_principal_with_sign_sys_ccy
            # summary.real_pl_carry_with_sign_sys_ccy += item.real_pl_carry_with_sign_sys_ccy
            # summary.real_pl_overheads_with_sign_sys_ccy += item.real_pl_overheads_with_sign_sys_ccy
            summary.real_pl_total_with_sign_sys_ccy += item.real_pl_total_with_sign_sys_ccy

            # summary.unreal_pl_principal_with_sign_sys_ccy += item.unreal_pl_principal_with_sign_sys_ccy
            # summary.unreal_pl_carry_with_sign_sys_ccy += item.unreal_pl_carry_with_sign_sys_ccy
            # summary.unreal_pl_overheads_with_sign_sys_ccy += item.unreal_pl_overheads_with_sign_sys_ccy
            summary.unreal_pl_total_with_sign_sys_ccy += item.unreal_pl_total_with_sign_sys_ccy

            summary.principal_with_sign_res_ccy += item.principal_with_sign_res_ccy
            summary.carry_with_sign_res_ccy += item.carry_with_sign_res_ccy
            summary.overheads_with_sign_res_ccy += item.overheads_with_sign_res_ccy
            summary.total_with_sign_res_ccy += item.total_with_sign_res_ccy

            # summary.real_pl_principal_with_sign_res_ccy += item.real_pl_principal_with_sign_res_ccy
            # summary.real_pl_carry_with_sign_res_ccy += item.real_pl_carry_with_sign_res_ccy
            # summary.real_pl_overheads_with_sign_res_ccy += item.real_pl_overheads_with_sign_res_ccy
            summary.real_pl_total_with_sign_res_ccy += item.real_pl_total_with_sign_res_ccy

            # summary.unreal_pl_principal_with_sign_res_ccy += item.unreal_pl_principal_with_sign_res_ccy
            # summary.unreal_pl_carry_with_sign_res_ccy += item.unreal_pl_carry_with_sign_res_ccy
            # summary.unreal_pl_overheads_with_sign_res_ccy += item.unreal_pl_overheads_with_sign_res_ccy
            summary.unreal_pl_total_with_sign_res_ccy += item.unreal_pl_total_with_sign_res_ccy

    def _process_custom_fields(self, items):
        if self.instance.custom_fields:
            for item in items:
                item.custom_fields = []
                for cf in self.instance.custom_fields:
                    if cf.expr:
                        try:
                            value = formula.safe_eval(cf.expr, names={'item': item})
                        except formula.InvalidExpression:
                            value = ugettext('Invalid expression')
                    else:
                        value = None
                    item.custom_fields.append({
                        'custom_field': cf,
                        'value': value
                    })

    def _to_sys_ccy(self, value, ccy):
        if isclose(value, 0.0):
            return 0.0
        h = self._get_currency_history(ccy)
        return value * h.fx_rate

    def _to_res_ccy(self, value):
        if isclose(value, 0.0):
            return 0.0
        h = self._get_currency_history(self.instance.report_currency)
        if isclose(h.fx_rate, 0.0):
            return 0.0
        else:
            return value / h.fx_rate

    def _show_transaction_details(self, case, acc):
        if case in [1, 2] and self.instance.show_transaction_details:
            return acc and acc.type and acc.type.show_transaction_details
        return False

    def _make_key(self, instrument=None, currency=None, portfolio=None, account=None, strategy1=None, strategy2=None,
                  strategy3=None, detail_transaction=None, transaction_class=None):
        return ','.join((
            'i=%s' % getattr(instrument, 'pk', -1),
            'c=%s' % getattr(currency, 'pk', -1),
            'p=%s' % getattr(portfolio, 'pk', -1),
            'a=%s' % getattr(account, 'pk', -1),
            's1=%s' % getattr(strategy1, 'pk', -1),
            's2=%s' % getattr(strategy2, 'pk', -1),
            's3=%s' % getattr(strategy3, 'pk', -1),
            'dt=%s' % getattr(detail_transaction, 'pk', -1),
            'tc=%s' % getattr(transaction_class, 'pk', -1),
        ))

    def _get_item(self, items, trn, instrument=None, currency=None, portfolio=None, account=None, strategy1=None,
                  strategy2=None, strategy3=None, transaction_class=None):
        t_instrument = instrument
        t_currency = currency

        if self._detail_by_portfolio:
            t_portfolio = portfolio
        else:
            t_portfolio = None

        if self._detail_by_account:
            t_account = account
        else:
            t_account = None

        if self._detail_by_strategy1:
            t_strategy1 = strategy1
        else:
            t_strategy1 = None

        if self._detail_by_strategy2:
            t_strategy2 = strategy2
        else:
            t_strategy2 = None

        if self._detail_by_strategy3:
            t_strategy3 = strategy3
        else:
            t_strategy3 = None

        if account and self._show_transaction_details(trn.case, account):
            if isinstance(trn, VirtualTransaction):
                t_detail_transaction = trn.transaction
            else:
                t_detail_transaction = trn
        else:
            t_detail_transaction = None

        if transaction_class:
            t_transaction_class = transaction_class
            t_instrument = None
            t_currency = None
            t_detail_transaction = None
        else:
            t_transaction_class = None

        pk = self._make_key(
            instrument=t_instrument,
            currency=t_currency,
            portfolio=t_portfolio,
            account=t_account,
            strategy1=t_strategy1,
            strategy2=t_strategy2,
            strategy3=t_strategy3,
            detail_transaction=t_detail_transaction,
            transaction_class=t_transaction_class
        )

        try:
            return items[pk]
        except KeyError:
            item = ReportItem(
                pk=pk,
                instrument=t_instrument,
                currency=t_currency,
                portfolio=t_portfolio,
                account=t_account,
                strategy1=t_strategy1,
                strategy2=t_strategy2,
                strategy3=t_strategy3,
                detail_transaction=t_detail_transaction,
                transaction_class=t_transaction_class
            )
            items[pk] = item
            return item
