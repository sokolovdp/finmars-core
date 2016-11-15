# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division

import logging
from collections import Counter, defaultdict, OrderedDict
from datetime import timedelta

import pandas
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import ugettext

from poms.common import formula
from poms.common.utils import isclose, date_now
from poms.instruments.models import CostMethod
from poms.reports.pricing import InstrumentPricingProvider, CurrencyFxRateProvider
from poms.transactions.models import Transaction, TransactionClass

_l = logging.getLogger('poms.reports')


class VirtualTransaction(object):
    def __init__(self, transaction, pk, overrides, sign=1.0):
        self.transaction = transaction
        self.pk = pk
        self.overrides = overrides or {}

    def __getattr__(self, item):
        if item == 'pk' or item == 'id':
            return self.pk
        if item in self.overrides:
            return self.overrides[item]
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

    # balance

    position_size = 0.0

    market_value_sys = 0.0
    market_value = 0.0

    cost_sys = 0.0
    cost = 0.0

    # P&L

    instr_principal_sys = 0.0
    instr_accrued_sys = 0.0
    principal_sys = 0.0
    carry_sys = 0.0
    overheads_sys = 0.0
    total_sys = 0.0

    instr_principal = 0.0
    instr_accrued = 0.0
    principal = 0.0
    carry = 0.0
    overheads = 0.0
    total = 0.0

    # principal_real_sys = 0.0
    # carry_real_sys = 0.0
    # overheads_real_sys = 0.0
    total_real_sys = 0.0

    # principal_real = 0.0
    # carry_real = 0.0
    # overheads_real = 0.0
    total_real = 0.0

    # principal_unreal_sys = 0.0
    # carry_unreal_sys = 0.0
    # overheads_unreal_sys = 0.0
    total_unreal_sys = 0.0

    # principal_unreal = 0.0
    # carry_unreal = 0.0
    # overheads_unreal = 0.0
    total_unreal = 0.0

    def __init__(self, pk=None, instrument=None, currency=None,
                 portfolio=None, account=None, strategy1=None, strategy2=None, strategy3=None,
                 detail_transaction=None, transaction_class=None, custom_fields=None):
        self.pk = pk

        self.type = ReportItem.TYPE_UNKNOWN
        if instrument:
            self.type = ReportItem.TYPE_INSTRUMENT
        elif currency:
            self.type = ReportItem.TYPE_CURRENCY
        elif transaction_class:
            if transaction_class.id == TransactionClass.TRANSACTION_PL:
                self.type = ReportItem.TYPE_TRANSACTION_PL
            elif transaction_class.id == TransactionClass.FX_TRADE:
                self.type = ReportItem.TYPE_FX_TRADE

        self.instrument = instrument  # -> Instrument
        self.currency = currency  # -> Currency
        self.transaction_class = transaction_class  # -> TransactionClass for TRANSACTION_PL and FX_TRADE

        self.portfolio = portfolio  # -> Portfolio if use_portfolio
        self.account = account  # -> Account if use_account
        self.strategy1 = strategy1  # -> Strategy1 if use_strategy1
        self.strategy2 = strategy2  # -> Strategy2 if use_strategy2
        self.strategy3 = strategy3  # -> Strategy3 if use_strategy3

        self.detail_transaction = detail_transaction  # -> Transaction if show_transaction_details

        self.custom_fields = custom_fields or []

        # # balance
        #
        # self.position_size = 0.0
        #
        # self.market_value_sys = 0.0
        # self.market_value = 0.0
        #
        # self.cost_sys = 0.0
        # self.cost = 0.0
        #
        # # P&L
        #
        # self.principal_with_sign_sys_ccy = 0.0
        # self.carry_with_sign_sys_ccy = 0.0
        # self.overheads_with_sign_sys_ccy = 0.0
        # self.total_with_sign_sys_ccy = 0.0
        #
        # self.real_pl_principal_with_sign_sys_ccy = 0.0
        # self.real_pl_carry_with_sign_sys_ccy = 0.0
        # self.real_pl_overheads_with_sign_sys_ccy = 0.0
        # self.real_pl_total_with_sign_sys_ccy = 0.0
        #
        # self.unreal_pl_principal_with_sign_sys_ccy = 0.0
        # self.unreal_pl_carry_with_sign_sys_ccy = 0.0
        # self.unreal_pl_overheads_with_sign_sys_ccy = 0.0
        # self.unreal_pl_total_with_sign_sys_ccy = 0.0
        #
        # self.principal_with_sign_res_ccy = 0.0
        # self.carry_with_sign_res_ccy = 0.0
        # self.overheads_with_sign_res_ccy = 0.0
        # self.total_with_sign_res_ccy = 0.0
        #
        # self.real_pl_principal_with_sign_res_ccy = 0.0
        # self.real_pl_carry_with_sign_res_ccy = 0.0
        # self.real_pl_overheads_with_sign_res_ccy = 0.0
        # self.real_pl_total_with_sign_res_ccy = 0.0
        #
        # self.unreal_pl_principal_with_sign_res_ccy = 0.0
        # self.unreal_pl_carry_with_sign_res_ccy = 0.0
        # self.unreal_pl_overheads_with_sign_res_ccy = 0.0
        # self.unreal_pl_total_with_sign_res_ccy = 0.0

    def __str__(self):
        return "%s #%s" % (self.__class__.__name__, self.pk,)

    @property
    def type_name(self):
        for i, n in ReportItem.TYPE_CHOICES:
            if i == self.type:
                return n
        return 'ERR'

    @property
    def type_code(self):
        if self.type == ReportItem.TYPE_UNKNOWN:
            return 'UNKN'
        elif self.type == ReportItem.TYPE_INSTRUMENT:
            return 'INSTR'
        elif self.type == ReportItem.TYPE_CURRENCY:
            return 'CCY'
        elif self.type == ReportItem.TYPE_TRANSACTION_PL:
            return 'TRN_PL'
        elif self.type == ReportItem.TYPE_FX_TRADE:
            return 'FX_TRADE'
        return 'ERR'

    @property
    def user_code(self):
        if self.type == ReportItem.TYPE_UNKNOWN:
            return '<UNKNOWN>'
        elif self.type == ReportItem.TYPE_INSTRUMENT:
            return self.instrument.user_code
        elif self.type == ReportItem.TYPE_CURRENCY:
            return self.currency.user_code
        elif self.type in [ReportItem.TYPE_TRANSACTION_PL, ReportItem.TYPE_FX_TRADE]:
            return self.transaction_class.system_code
        return '<ERROR>'

    @property
    def name(self):
        if self.type == ReportItem.TYPE_UNKNOWN:
            return '<UNKNOWN>'
        elif self.type == ReportItem.TYPE_INSTRUMENT:
            return self.instrument.name
        elif self.type == ReportItem.TYPE_CURRENCY:
            return self.currency.name
        elif self.type in [ReportItem.TYPE_TRANSACTION_PL, ReportItem.TYPE_FX_TRADE]:
            return self.transaction_class.name
        return '<ERROR>'


class ReportSummary(object):
    # balance
    market_value_sys = 0.0
    market_value = 0.0

    cost_sys = 0.0
    cost = 0.0

    # P&L

    principal_sys = 0.0
    carry_sys = 0.0
    overheads_sys = 0.0
    total_sys = 0.0

    principal = 0.0
    carry = 0.0
    overheads = 0.0
    total = 0.0

    def __init__(self):
        # balance
        # self.market_value_sys_ccy = 0.0
        # self.market_value_res_ccy = 0.0

        # self.cost_with_sign_sys_ccy = 0.0
        # self.cost_with_sign_res_ccy = 0.0

        # P&L
        # self.principal_with_sign_sys_ccy = 0.0
        # self.carry_with_sign_sys_ccy = 0.0
        # self.overheads_with_sign_sys_ccy = 0.0
        # self.total_with_sign_sys_ccy = 0.0
        #
        # self.real_pl_principal_with_sign_sys_ccy = 0.0
        # self.real_pl_carry_with_sign_sys_ccy = 0.0
        # self.real_pl_overheads_with_sign_sys_ccy = 0.0
        # self.real_pl_total_with_sign_sys_ccy = 0.0
        #
        # # self.unreal_pl_principal_with_sign_sys_ccy = 0.0
        # # self.unreal_pl_carry_with_sign_sys_ccy = 0.0
        # # self.unreal_pl_overheads_with_sign_sys_ccy = 0.0
        # self.unreal_pl_total_with_sign_sys_ccy = 0.0
        #
        # self.principal_with_sign_res_ccy = 0.0
        # self.carry_with_sign_res_ccy = 0.0
        # self.overheads_with_sign_res_ccy = 0.0
        # self.total_with_sign_res_ccy = 0.0
        #
        # self.real_pl_principal_with_sign_res_ccy = 0.0
        # self.real_pl_carry_with_sign_res_ccy = 0.0
        # self.real_pl_overheads_with_sign_res_ccy = 0.0
        # self.real_pl_total_with_sign_res_ccy = 0.0
        #
        # # self.unreal_pl_principal_with_sign_res_ccy = 0.0
        # # self.unreal_pl_carry_with_sign_res_ccy = 0.0
        # # self.unreal_pl_overheads_with_sign_res_ccy = 0.0
        # self.unreal_pl_total_with_sign_res_ccy = 0.0
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

    def _trn_qs(self):
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

    @cached_property
    def _pricing(self):
        p = InstrumentPricingProvider(self.instance.master_user, self.instance.pricing_policy,
                                      self.instance.report_date)
        p.fill_using_transactions(self._trn_qs())
        return p

    @cached_property
    def _fx_rates(self):
        p = CurrencyFxRateProvider(self.instance.master_user, self.instance.pricing_policy, self.instance.report_date)
        p.fill_using_transactions(self._trn_qs(), currencies=[self.instance.report_currency])
        return p

    def _get_instr_pricing(self, instrument, date=None):
        return self._pricing[instrument, date]

    def _get_ccy_hist(self, currency, date=None):
        return self._fx_rates[currency, date]

    def _to_sys_ccy(self, value, ccy):
        if isclose(value, 0.0):
            return 0.0
        h = self._get_ccy_hist(ccy)
        return value * h.fx_rate

    def _to_res_ccy(self, value):
        if isclose(value, 0.0):
            return 0.0
        h = self._get_ccy_hist(self.instance.report_currency)
        if isclose(h.fx_rate, 0.0):
            return 0.0
        else:
            return value / h.fx_rate

    def _show_transaction_details(self, case, acc):
        if case in [1, 2] and self.instance.show_transaction_details:
            return acc and acc.type and acc.type.show_transaction_details
        return False

    def _make_key(self, instr=None, ccy=None, prtfl=None, acc=None, strg1=None, strg2=None, strg3=None, detail_trn=None,
                  trn_cls=None):
        return ','.join((
            'i=%s' % getattr(instr, 'pk', -1),
            'c=%s' % getattr(ccy, 'pk', -1),
            'p=%s' % getattr(prtfl, 'pk', -1),
            'a=%s' % getattr(acc, 'pk', -1),
            's1=%s' % getattr(strg1, 'pk', -1),
            's2=%s' % getattr(strg2, 'pk', -1),
            's3=%s' % getattr(strg3, 'pk', -1),
            'dt=%s' % getattr(detail_trn, 'pk', -1),
            'tc=%s' % getattr(trn_cls, 'pk', -1),
        ))

    def _get_item(self, items, trn, instr=None, ccy=None, prtfl=None, acc=None, strg1=None, strg2=None, strg3=None,
                  trn_cls=None):
        t_instr = instr
        t_ccy = ccy

        if self._detail_by_portfolio:
            t_prtfl = prtfl
        else:
            t_prtfl = None

        if self._detail_by_account:
            t_acc = acc
        else:
            t_acc = None

        if self._detail_by_strategy1:
            t_strg1 = strg1
        else:
            t_strg1 = None

        if self._detail_by_strategy2:
            t_strg2 = strg2
        else:
            t_strg2 = None

        if self._detail_by_strategy3:
            t_strg3 = strg3
        else:
            t_strg3 = None

        if acc and self._show_transaction_details(trn.r_case, acc):
            if isinstance(trn, VirtualTransaction):
                t_detail_trn = trn.transaction
            else:
                t_detail_trn = trn
        else:
            t_detail_trn = None

        if trn_cls:
            t_trn_cls = trn_cls
            t_instr = None
            t_ccy = None
            t_detail_trn = None
        else:
            t_trn_cls = None

        pk = self._make_key(instr=t_instr, ccy=t_ccy, prtfl=t_prtfl, acc=t_acc, strg1=t_strg1, strg2=t_strg2,
                            strg3=t_strg3, detail_trn=t_detail_trn, trn_cls=t_trn_cls)

        try:
            return items[pk]
        except KeyError:
            item = ReportItem(pk=pk, instrument=t_instr, currency=t_ccy, portfolio=t_prtfl, account=t_acc,
                              strategy1=t_strg1, strategy2=t_strg2, strategy3=t_strg3, detail_transaction=t_detail_trn,
                              transaction_class=t_trn_cls)
            items[pk] = item
            return item

    @cached_property
    def transactions(self):
        if self._transactions:
            return self._transactions

        transactions = [t for t in self._trn_qs()]

        self._annotate_multiplier(transactions)

        transactions1 = []
        for t in transactions:
            if t.accounting_date <= self._report_date < t.cash_date:  # default
                t.r_case = 1
            elif t.cash_date <= self._report_date < t.accounting_date:
                t.r_case = 2
            else:
                t.r_case = 0

            self._annotate_transaction_hist(t)

            t_class = t.transaction_class_id
            if t_class == TransactionClass.TRANSFER:
                if t.position_size_with_sign >= 0:
                    t1 = VirtualTransaction(
                        transaction=t,
                        pk='%s:sell' % t.pk,
                        overrides={
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
                        overrides={
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
                        overrides={
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
                        overrides={
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
                    overrides={
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
                    overrides={
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

    def _annotate_transaction_hist(self, t):
        if t.instrument:
            t.r_instr_price_rep = self._get_instr_pricing(t.instrument)

            t.r_instr_pricing_ccy_rep = self._get_ccy_hist(t.instrument.pricing_currency)
            t.r_instr_accrued_ccy_rep = self._get_ccy_hist(t.instrument.accrued_currency)

        if t.transaction_currency:
            t.r_trn_ccy_hist = self._get_ccy_hist(t.transaction_currency, t.accounting_date)
            t.r_trn_ccy_rep = self._get_ccy_hist(t.transaction_currency)

        if t.settlement_currency:
            t.r_stlmnt_ccy_hist = self._get_ccy_hist(t.settlement_currency, t.cash_date)
            t.r_stlmnt_ccy_rep = self._get_ccy_hist(t.settlement_currency)

    def _transactions_frame(self):
        columns = [
            ('pk', 'pk'),
            ('trn', 'self'),
            ('cls', 'transaction_class'),
            ('cls_id', 'transaction_class__id'),

            ('case', ''),
            ('multiplier', ''),

            ('instr', 'instrument'),
            # ('instr_id', 'instrument_id'),

            ('trn_ccy', 'transaction_currency'),
            # ('trn_ccy_id', 'transaction_currency_id'),

            ('pos_size', 'position_size_with_sign'),

            ('stl_ccy', 'settlement_currency'),
            # ('stl_ccy_id', 'settlement_currency_id'),

            ('cash', 'cash_consideration'),
            ('principal', 'principal_with_sign'),
            ('carry', 'carry_with_sign'),
            ('overheads', 'overheads_with_sign'),

            ('acc_date', 'accounting_date'),
            ('cash_date', 'cash_date'),

            ('prtfl', 'portfolio'),
            # ('prtfl_id', 'portfolio_id'),

            ('acc_pos', 'account_position'),
            # ('acc_pos_id', 'account_position_id'),
            ('acc_cash', 'account_cash'),
            # ('acc_cash_id', 'account_cash_id'),
            ('acc_interim', 'account_interim'),
            # ('acc_interim_id', 'account_interim_id'),

            ('str1_pos', 'strategy1_position'),
            # ('str1_pos_id', 'strategy1_position_id'),
            ('str1_cash', 'strategy1_cash'),
            # ('str1_cash_id', 'strategy1_cash_id'),

            ('str2_pos', 'strategy2_position'),
            # ('str2_pos_id', 'strategy2_position_id'),
            ('str2_cash', 'strategy2_cash'),
            # ('str2_cash_id', 'strategy2_cash_id'),

            ('str3_pos', 'strategy3_position'),
            # ('str3_pos_id', 'strategy3_position_id'),
            ('str3_cash', 'strategy3_cash'),
            # ('str3_cash_id', 'strategy3_cash_id'),
        ]
        data = []
        for t in self.transactions:
            row = []
            for col, attr in columns:
                if attr == 'self':
                    v = t
                elif attr:
                    v = t
                    for p in attr.split('__'):
                        v = getattr(v, p, None)
                        if p in ['id', 'pk']:
                            v = str(v)
                else:
                    v = None
                row.append(v)
            data.append(row)

        df = pandas.DataFrame(data=data, columns=[col for col, attr in columns])

        for i, row in df.iterrows():
            if row['acc_date'] <= self._report_date < row['cash_date']:
                df.ix[i, 'case'] = 1
            elif row['cash_date'] <= self._report_date < row['acc_date']:
                df.ix[i, 'case'] = 2
            else:
                df.ix[i, 'case'] = 0

            instr = row['instr']
            if instr:
                # pricing

                df.ix[i, 'instr_price_mul'] = instr.price_multiplier
                df.ix[i, 'instr_accrued_mul'] = instr.accrued_multiplier

                p = self._pricing[instr]
                df.ix[i, 'instr_cur_principal_price'] = p.principal_price
                df.ix[i, 'instr_cur_accrued_price'] = p.accrued_price
                df.ix[i, 'instr_cur'] = p
                # df.ix[i, 'instr_cur_id'] = p.id

                # pricing_currency

                df.ix[i, 'instr_pricing_ccy'] = instr.pricing_currency
                # df.ix[i, 'instr_pricing_ccy_id'] = instr.pricing_currency_id

                fx = self._fx_rates[instr.pricing_currency]
                df.ix[i, 'instr_pricing_ccy_cur_fx'] = fx.fx_rate
                df.ix[i, 'instr_pricing_ccy_cur'] = fx
                # df.ix[i, 'instr_pricing_ccy_cur_id'] = fx.id

                # accrued_currency

                df.ix[i, 'instr_accrued_ccy'] = instr.accrued_currency
                # df.ix[i, 'instr_accrued_ccy_id'] = instr.accrued_currency_id

                fx = self._fx_rates[instr.accrued_currency]
                df.ix[i, 'instr_accrued_ccy_cur_fx'] = fx.fx_rate
                df.ix[i, 'instr_accrued_ccy_cur'] = fx
                # df.ix[i, 'instr_accrued_ccy_cur_id'] = fx.id

            trn_ccy = row['trn_ccy']
            if trn_ccy:
                fx = self._fx_rates[trn_ccy]
                df.ix[i, 'trn_ccy_cur_fx'] = fx.fx_rate
                df.ix[i, 'trn_ccy_cur'] = fx
                # df.ix[i, 'trn_ccy_cur_id'] = fx.id

                fx = self._fx_rates[trn_ccy, row['acc_date']]
                df.ix[i, 'trn_ccy_hist_fx'] = fx.fx_rate
                df.ix[i, 'trn_ccy_hist'] = fx
                # df.ix[i, 'trn_ccy_hist_id'] = fx.id

            stl_ccy = row['stl_ccy']
            if stl_ccy:
                fx = self._fx_rates[stl_ccy]
                df.ix[i, 'stl_ccy_cur_fx'] = fx.fx_rate
                df.ix[i, 'stl_ccy_cur'] = fx
                # df.ix[i, 'stl_ccy_cur_id'] = fx.id

                fx = self._fx_rates[stl_ccy, row['cash_date']]
                df.ix[i, 'stl_ccy_hist_fx'] = fx.fx_rate
                df.ix[i, 'stl_ccy_hist'] = fx
                # df.ix[i, 'stl_ccy_hist_id'] = fx.id

        df['case'] = 0
        df['multiplier'] = 0.0
        df['total'] = df['principal'] + df['carry'] + df['overheads']

        df['principal_sys'] = df['principal'] * df['stl_ccy_cur_fx']
        df['carry_sys'] = df['carry'] * df['stl_ccy_cur_fx']
        df['overheads_sys'] = df['overheads'] * df['stl_ccy_cur_fx']
        df['total_sys'] = df['principal_sys'] + df['carry_sys'] + df['overheads_sys']

        df['total_unreal_sys'] = 0.0
        df['total_real_sys'] = 0.0

        print(df)
        # df['cls_id'] = df['cls'].id
        self._multipliers(df)

        print(df)

        return df

    def _multipliers(self, df):
        rolling_positions = Counter()
        items = defaultdict(list)

        multipliers_delta = []

        def _set_multiplier(i_, row_, multiplier):
            # if isclose(t.r_multiplier, multiplier):
            #     return
            multipliers_delta.append((i_, row_, multiplier - row_['multiplier']))
            row_['multiplier'] = multiplier
            df.ix[i_, 'multiplier'] = multiplier

        for i, row in df.iterrows():
            cls_id = int(row['cls_id'])
            if cls_id not in [TransactionClass.BUY, TransactionClass.SELL]:
                df.ix[i, 'multiplier'] = 1.0
                continue

            # do not use strategy!!!
            # t_key = self._make_key(
            #     instr=row['instr'],
            #     prtfl=row['prtfl'] if self._detail_by_portfolio else None,
            #     acc=row['acc_pos'] if self._detail_by_account else None
            # )
            t_key = self._make_key(
                instr=row['instr'],
                prtfl=row['prtfl'],
                acc=row['acc_pos'],
            )

            # df.ix[i, 'multiplier'] = 0.0
            # t.r_total_real = 0.0

            multipliers_delta.clear()
            rolling_position = rolling_positions[t_key]

            if isclose(rolling_position, 0.0):
                k = -1
            else:
                k = - row['pos_size'] / rolling_position

            if self.instance.cost_method.id == CostMethod.AVCO:

                if k > 1.0:
                    if t_key in items:
                        for i0, row0 in items[t_key]:
                            _set_multiplier(i0, row0, 1.0)
                        items[t_key].clear()
                    items[t_key].append((i, row))
                    _set_multiplier(i, row, 1.0 / k)
                    rolling_position = row['pos_size'] * (1.0 - row['multiplier'])

                elif isclose(k, 1.0):
                    if t_key in items:
                        for i0, row0 in items[t_key]:
                            _set_multiplier(i0, row0, 1.0)
                        del items[t_key]
                    _set_multiplier(i, row, 1.0)
                    rolling_position = 0.0

                elif k > 0.0:
                    if t_key in items:
                        for i0, row0 in items[t_key]:
                            _set_multiplier(i0, row0, row0['multiplier'] + k * (1.0 - row0['multiplier']))
                    _set_multiplier(i, row, 1.0)
                    rolling_position += row['pos_size']

                else:
                    items[t_key].append((i, row))
                    rolling_position += row['pos_size']

            elif self.instance.cost_method.id == CostMethod.FIFO:

                if k > 1.0:
                    if t_key in items:
                        for i0, row0 in items[t_key]:
                            _set_multiplier(i0, row0, 1.0)
                        items[t_key].clear()
                    items[t_key].append((i, row))
                    _set_multiplier(i, row, 1.0 / k)
                    rolling_position = row['pos_size'] * (1.0 - row['multiplier'])

                elif isclose(k, 1.0):
                    if t_key in items:
                        for i0, row0 in items[t_key]:
                            _set_multiplier(i0, row0, 1.0)
                        del items[t_key]
                    _set_multiplier(i, row, 1.0)
                    rolling_position = 0.0

                elif k > 0.0:
                    position = row['pos_size']
                    if t_key in items:
                        t_items = items[t_key]
                        for i0, row0 in t_items:
                            remaining = row0['pos_size'] * (1.0 - row0['multiplier'])
                            k0 = - position / remaining
                            if k0 > 1.0:
                                _set_multiplier(i0, row0, 1.0)
                                position += remaining
                            elif isclose(k0, 1.0):
                                _set_multiplier(i0, row0, 1.0)
                                position += remaining
                            elif k0 > 0.0:
                                position += remaining * k0
                                _set_multiplier(i0, row0, row0['multiplier'] + k0 * (1.0 - row0['multiplier']))
                            # else:
                            #     break
                            if isclose(position, 0.0):
                                break
                        t_items = [(i0, row0) for i0, row0 in t_items if not isclose(row0['multiplier'], 1.0)]
                        if t_items:
                            items[t_key] = t_items
                        else:
                            del items[t_key]

                    _set_multiplier(i, row, abs((row['pos_size'] - position) / row['pos_size']))
                    rolling_position += row['pos_size'] * row['multiplier']

                else:
                    items[t_key].append((i, row))
                    rolling_position += row['pos_size']

            rolling_positions[t_key] = rolling_position
            # print('i =', i, ', rolling_positions =', rolling_position)

            if multipliers_delta:
                init_mult = 1.0 - self.instance.pl_real_unreal_end_multiplier
                end_mult = self.instance.pl_real_unreal_end_multiplier

                i, row, inc_multiplier = multipliers_delta[-1]

                # sum_principal = 0.0
                # sum_carry = 0.0
                # sum_overheads = 0.0
                sum_total_sys = 0.0
                for i0, row0, inc_multiplier0 in multipliers_delta:
                    # sum_principal += t0.principal_with_sign * inc_multiplier0
                    # sum_carry += t0.carry_with_sign * inc_multiplier0
                    # sum_overheads += t0.overheads_with_sign * inc_multiplier0
                    sum_total_sys += inc_multiplier0 * (
                        row0['principal_sys'] + row0['carry_sys'] + row0['overheads_sys'])

                for i0, row0, inc_multiplier0 in multipliers_delta:
                    mult = end_mult if row0['pk'] == row['pk'] else init_mult

                    matched = abs((row0['pos_size'] * inc_multiplier0) / (row['pos_size'] * inc_multiplier))
                    # adj = matched * mult

                    # t0.real_pl_principal_with_sign += sum_principal * matched * mult
                    # t0.real_pl_carry_with_sign += sum_carry * matched * mult
                    # t0.real_pl_overheads_with_sign += sum_overheads * matched * mult

                    # t0.r_total_real += sum_total * matched * mult
                    df.ix[i0, 'total_real_sys'] += sum_total_sys * matched * mult

    def _annotate_multiplier(self, transactions):
        rolling_positions = Counter()
        items = defaultdict(list)

        multipliers_delta = []

        def _set_multiplier(t0, multiplier):
            # if isclose(t.r_multiplier, multiplier):
            #     return
            multipliers_delta.append((t0, multiplier - t0.r_multiplier))
            t0.r_multiplier = multiplier

        for i, t in enumerate(transactions):
            if t.transaction_class_id not in [TransactionClass.BUY, TransactionClass.SELL]:
                continue

            # do not use strategy!!!
            t_key = self._make_key(
                instr=t.instrument,
                prtfl=t.portfolio if self._detail_by_portfolio else None,
                acc=t.account_position if self._detail_by_account else  None
            )

            t.r_multiplier = 0.0
            t.r_total_real = 0.0

            multipliers_delta.clear()
            rolling_position = rolling_positions[t_key]

            if isclose(rolling_position, 0.0):
                k = -1
            else:
                k = - t.position_size_with_sign / rolling_position

            if self.instance.cost_method.id == CostMethod.AVCO:

                if k > 1.0:
                    if t_key in items:
                        for t0 in items[t_key]:
                            _set_multiplier(t0, 1.0)
                        del items[t_key]
                    items[t_key].append(t)
                    _set_multiplier(t, 1.0 / k)
                    rolling_position = t.position_size_with_sign * (1.0 - t.r_multiplier)

                elif isclose(k, 1.0):
                    if t_key in items:
                        for t0 in items[t_key]:
                            _set_multiplier(t0, 1.0)
                        del items[t_key]
                    _set_multiplier(t, 1.0)
                    rolling_position = 0.0

                elif k > 0.0:
                    if t_key in items:
                        for t0 in items[t_key]:
                            _set_multiplier(t0, t0.r_multiplier + k * (1.0 - t0.r_multiplier))
                    _set_multiplier(t, 1.0)
                    rolling_position += t.position_size_with_sign

                else:
                    items[t_key].append(t)
                    rolling_position += t.position_size_with_sign

            elif self.instance.cost_method.id == CostMethod.FIFO:

                if k > 1.0:
                    if t_key in items:
                        for t0 in items[t_key]:
                            _set_multiplier(t0, 1.0)
                        items[t_key].clear()
                    items[t_key].append(t)
                    _set_multiplier(t, 1.0 / k)
                    rolling_position = t.position_size_with_sign * (1.0 - t.r_multiplier)

                elif isclose(k, 1.0):
                    if t_key in items:
                        for t0 in items[t_key]:
                            _set_multiplier(t0, 1.0)
                        del items[t_key]
                    _set_multiplier(t, 1.0)
                    rolling_position = 0.0

                elif k > 0.0:
                    position = t.position_size_with_sign
                    if t_key in items:
                        t_items = items[t_key]
                        for t0 in t_items:
                            remaining = t0.position_size_with_sign * (1.0 - t0.r_multiplier)
                            k0 = - position / remaining
                            if k0 > 1.0:
                                _set_multiplier(t0, 1.0)
                                position += remaining
                            elif isclose(k0, 1.0):
                                _set_multiplier(t0, 1.0)
                                position += remaining
                            elif k0 > 0.0:
                                position += remaining * k0
                                _set_multiplier(t0, t0.multiplier + k0 * (1.0 - t0.r_multiplier))
                            # else:
                            #     break
                            if isclose(position, 0.0):
                                break
                        t_items = [t0 for t0 in t_items if not isclose(t0.r_multiplier, 1.0)]
                        if t_items:
                            items[t_key] = t_items
                        else:
                            del items[t_key]

                    _set_multiplier(t, abs((t.position_size_with_sign - position) / t.position_size_with_sign))
                    rolling_position += t.position_size_with_sign * t.r_multiplier

                else:
                    items[t_key].append(t)
                    rolling_position += t.position_size_with_sign

            rolling_positions[t_key] = rolling_position
            # print('i =', i, ', rolling_positions =', rolling_position)

            if multipliers_delta:
                init_mult = 1.0 - self.instance.pl_real_unreal_end_multiplier
                end_mult = self.instance.pl_real_unreal_end_multiplier

                t, inc_multiplier = multipliers_delta[-1]

                # sum_principal = 0.0
                # sum_carry = 0.0
                # sum_overheads = 0.0
                sum_total = 0.0
                for t0, inc_multiplier0 in multipliers_delta:
                    # sum_principal += t0.principal_with_sign * inc_multiplier0
                    # sum_carry += t0.carry_with_sign * inc_multiplier0
                    # sum_overheads += t0.overheads_with_sign * inc_multiplier0
                    sum_total += inc_multiplier0 * (
                        t0.principal_with_sign + t0.carry_with_sign + t0.overheads_with_sign)

                for t0, inc_multiplier0 in multipliers_delta:
                    mult = end_mult if t0.id == t.id else init_mult

                    matched = abs((t0.position_size_with_sign * inc_multiplier0) / (
                        t.position_size_with_sign * inc_multiplier))
                    # adj = matched * mult

                    # t0.real_pl_principal_with_sign += sum_principal * matched * mult
                    # t0.real_pl_carry_with_sign += sum_carry * matched * mult
                    # t0.real_pl_overheads_with_sign += sum_overheads * matched * mult
                    t0.r_total_real += sum_total * matched * mult

        for t in transactions:
            if t.transaction_class_id not in [TransactionClass.BUY, TransactionClass.SELL]:
                continue
            t.r_position_size = t.position_size_with_sign * (1.0 - t.r_multiplier)
            t.r_cost = t.principal_with_sign * (1.0 - t.r_multiplier)

    def build(self):
        trns_df = self._transactions_frame()

        instr_map = {}
        ccy_map = {}
        prtfl_map = {}
        acc_map = {}
        str1_map = {}
        str2_map = {}
        str3_map = {}

        item_row = OrderedDict()
        item_row['type'] = 'UNKNOWN'
        item_row['trn_cls'] = None
        item_row['trn_cls_id'] = None
        item_row['trn'] = None
        item_row['user_code'] = ''
        item_row['instr'] = None
        item_row['instr_id'] = ''
        item_row['ccy'] = None
        item_row['ccy_id'] = ''
        item_row['prtfl'] = None
        item_row['prtfl_id'] = ''
        item_row['acc'] = None
        item_row['acc_id'] = ''
        item_row['str1'] = None
        item_row['str1_id'] = ''
        item_row['str2'] = None
        item_row['str2_id'] = ''
        item_row['str3'] = None
        item_row['str3_id'] = ''
        item_row['pos_size'] = 0

        def _instr(trn):
            row = item_row.copy()

            instr = trn['instr']
            prtfl = trn['prtfl']
            acc = trn['acc_pos']
            str1 = trn['str1_pos']
            str2 = trn['str2_pos']
            str3 = trn['str3_pos']

            row['type'] = 'INSTR'
            row['trn_cls'] = trn['cls']
            row['trn_cls_id'] = str(trn['cls_id'])
            row['trn'] = trn['trn']
            row['user_code'] = instr.user_code

            row['instr'] = instr
            row['instr_id'] = str(instr.id)

            row['prtfl'] = prtfl
            row['prtfl_id'] = str(prtfl.id)

            row['acc'] = acc
            row['acc_id'] = str(acc.id)

            row['str1'] = str1
            row['str1_id'] = str(str1.id)

            row['str2'] = str2
            row['str2_id'] = str(str2.id)

            row['str3'] = str3
            row['str3_id'] = str(str3.id)

            row['pos_size'] = trn['pos_size'] * (1 - trn['multiplier'])

            instr_map[instr.id] = instr

            return row.values()

        def _cash(trn, ccy=None, pos_size=None, is_interim=False, is_pos=False):
            row = item_row.copy()

            ccy = ccy or trn['stl_ccy']
            prtfl = trn['prtfl']
            if is_interim:
                acc = trn['acc_interim']
            elif is_pos:
                acc = trn['acc_pos']
            else:
                acc = trn['acc_cash']
            str1 = trn['str1_pos'] if is_pos else trn['str1_cash']
            str2 = trn['str2_pos'] if is_pos else trn['str1_cash']
            str3 = trn['str3_pos'] if is_pos else trn['str1_cash']

            row['type'] = 'CCY'
            row['trn_cls'] = trn['cls']
            row['trn_cls_id'] = trn['cls_id']
            row['trn'] = trn['trn']
            row['user_code'] = ccy.user_code

            row['ccy'] = ccy
            row['ccy_id'] = str(ccy.id)

            row['prtfl'] = prtfl
            row['prtfl_id'] = str(prtfl.id)

            row['acc'] = acc
            row['acc_id'] = str(acc.id)

            row['str1'] = str1
            row['str1_id'] = str(str1.id)

            row['str2'] = str2
            row['str2_id'] = str(str2.id)

            row['str3'] = str3
            row['str3_id'] = str(str3.id)

            row['pos_size'] = pos_size

            return row.values()

        data = []
        for i, trn in trns_df.iterrows():
            trn_cls = int(trn['cls_id'])
            case = trn['case']
            if trn_cls in [TransactionClass.BUY, TransactionClass.SELL]:
                if case == 0:
                    data.append(_instr(trn))
                    data.append(_cash(trn, pos_size=trn['cash']))
                elif case == 1:
                    data.append(_instr(trn))
                    data.append(_cash(trn, is_interim=True))
                elif case == 2:
                    data.append(_cash(trn, pos_size=trn['cash']))
                    data.append(_cash(trn, pos_size=-trn['cash'], is_interim=True))

        items_df = pandas.DataFrame(data=data, columns=item_row.keys())
        # for i, row in items_df.iterrows():
        #     items_df.ix[i, 'instr_id'] = getattr(row['instr'], 'id', -1)
        #     items_df.ix[i, 'ccy_id'] = getattr(row['ccy'], 'id', -1)
        #     items_df.ix[i, 'prtfl_id'] = getattr(row['prtfl'], 'id', -1)
        #     items_df.ix[i, 'acc_id'] = getattr(row['acc'], 'id', -1)
        #     items_df.ix[i, 'str1_id'] = getattr(row['str1'], 'id', -1)
        #     items_df.ix[i, 'str2_id'] = getattr(row['str2'], 'id', -1)
        #     items_df.ix[i, 'str3_id'] = getattr(row['str3'], 'id', -1)

        print('00000')
        print(items_df)

        print('11111')
        grouped = items_df.groupby(['type', 'instr_id', 'ccy_id', 'user_code'])

        for name, group in grouped:
            print(name)
            print(group)

        print('22222')

        print(grouped.agg({
            'pos_size': 'sum'
        }))

        print('33333')

        for trn in self.transactions:
            if trn.transaction_class_id in [TransactionClass.BUY, TransactionClass.SELL]:
                self._add_instr(self._items, trn, value=trn.r_position_size)
                self._add_cash(self._items, trn, value=trn.cash_consideration, ccy=trn.settlement_currency)

            elif trn.transaction_class_id == TransactionClass.FX_TRADE:
                # TODO: Что используем для strategy?
                self._add_cash(self._items, trn, value=trn.position_size_with_sign, ccy=trn.transaction_currency,
                               acc=trn.account_position, strg1=trn.strategy1_position,
                               strg2=trn.strategy2_position, strg3=trn.strategy3_position, )

                self._add_cash(self._items, trn, value=trn.cash_consideration, ccy=trn.settlement_currency)

                # P&L
                item = self._get_item(self._items, trn, prtfl=trn.portfolio, acc=trn.account_position,
                                      strg1=trn.strategy1_position, strg2=trn.strategy2_position,
                                      strg3=trn.strategy3_position, trn_cls=trn.transaction_class)
                item.principal_with_sign_sys_ccy += \
                    self._to_sys_ccy(trn.position_size_with_sign, trn.transaction_currency) + \
                    self._to_sys_ccy(trn.principal_with_sign, trn.settlement_currency)
                # item.carry_with_sign_sys_ccy += self._to_sys_ccy(trn.carry_with_sign, trn.settlement_currency)
                item.overheads_with_sign_sys_ccy += self._to_sys_ccy(trn.overheads_with_sign, trn.settlement_currency)

            elif trn.transaction_class_id == TransactionClass.INSTRUMENT_PL:
                self._add_instr(self._items, trn, value=trn.position_size_with_sign)
                self._add_cash(self._items, trn, value=trn.cash_consideration, ccy=trn.settlement_currency)

            elif trn.transaction_class_id == TransactionClass.TRANSACTION_PL:
                item = self._get_item(self._items, trn, prtfl=trn.portfolio, acc=trn.account_position,
                                      strg1=trn.strategy1_position, strg2=trn.strategy2_position,
                                      strg3=trn.strategy3_position, trn_cls=trn.transaction_class)

                self._add_cash(self._items, trn, value=trn.cash_consideration, ccy=trn.settlement_currency)

                item.principal_with_sign_sys_ccy += self._to_sys_ccy(trn.principal_with_sign, trn.settlement_currency)
                item.carry_with_sign_sys_ccy += self._to_sys_ccy(trn.carry_with_sign, trn.settlement_currency)
                item.overheads_with_sign_sys_ccy += self._to_sys_ccy(trn.overheads_with_sign, trn.settlement_currency)

            elif trn.transaction_class_id == TransactionClass.TRANSFER:
                raise RuntimeError('Virtual transaction must be created')

            elif trn.transaction_class_id == TransactionClass.FX_TRANSFER:
                raise RuntimeError('Virtual transaction must be created')

            elif trn.transaction_class_id in [TransactionClass.CASH_INFLOW, TransactionClass.CASH_OUTFLOW]:
                self._add_cash(self._items, trn, value=trn.position_size_with_sign, ccy=trn.transaction_currency,
                               acc=trn.account_position, strg1=trn.strategy1_position, strg2=trn.strategy2_position,
                               strg3=trn.strategy3_position)

                # invested cash
                self._add_cash(self._invested_items, trn, value=trn.position_size_with_sign,
                               ccy=trn.transaction_currency,
                               acc=trn.account_position, strg1=trn.strategy1_position, strg2=trn.strategy2_position,
                               strg3=trn.strategy3_position)

            else:
                raise RuntimeError('Invalid transaction class: %s' % trn.transaction_class_id)

        self._process_final(self._invested_items.values())
        self.instance.invested_items = sorted([i for i in self._invested_items.values()], key=lambda x: x.pk)

        self._process_final(self._items.values())
        self.instance.items = sorted([i for i in self._items.values()], key=lambda x: x.pk)
        self._process_summary(self.instance.summary, self.instance.items)

        self._process_custom_fields(self.instance.items)

        return self.instance

    def _add_instr(self, items, trn, value, prtfl=None, acc=None, strg1=None, strg2=None, strg3=None):
        if prtfl is None:
            prtfl = trn.portfolio
        if acc is None:
            acc = trn.account_position
        if strg1 is None:
            strg1 = trn.strategy1_position
        if strg2 is None:
            strg2 = trn.strategy2_position
        if strg3 is None:
            strg3 = trn.strategy3_position

        if trn.r_case == 0:
            item = self._get_item(items, trn, instr=trn.instrument, prtfl=prtfl, acc=acc,
                                  strg1=strg1, strg2=strg2, strg3=strg3)
        elif trn.r_case == 1:
            item = self._get_item(items, trn, instr=trn.instrument, prtfl=prtfl, acc=acc,
                                  strg1=strg1, strg2=strg2, strg3=strg3)

        elif trn.r_case == 2:
            return

        else:
            raise RuntimeError('Invalid transaction case: %s' % trn.case)

        if item:
            ccy = trn.settlement_currency
            # balance
            item.position_size += value
            item.cost_sys += self._to_sys_ccy(trn.r_cost, ccy)

            #  P&L
            item.principal_sys += self._to_sys_ccy(trn.principal_with_sign, ccy)
            item.carry_sys += self._to_sys_ccy(trn.carry_with_sign, ccy)
            item.overheads_sys += self._to_sys_ccy(trn.overheads_with_sign, ccy)

            # item.real_pl_principal_with_sign_sys_ccy += self._to_sys_ccy(trn.real_pl_principal_with_sign, ccy)
            # item.real_pl_carry_with_sign_sys_ccy += self._to_sys_ccy(trn.real_pl_carry_with_sign, ccy)
            # item.real_pl_overheads_with_sign_sys_ccy += self._to_sys_ccy(trn.real_pl_overheads_with_sign, ccy)
            item.total_real_sys += self._to_sys_ccy(trn.r_total_real, ccy)

            # item.unreal_pl_principal_with_sign_sys_ccy += self._to_sys_ccy(trn.unreal_pl_principal_with_sign,ccy)
            # item.unreal_pl_carry_with_sign_sys_ccy += self._to_sys_ccy(trn.unreal_pl_carry_with_sign,ccy)
            # item.unreal_pl_overheads_with_sign_sys_ccy += self._to_sys_ccy(trn.unreal_pl_overheads_with_sign,ccy)
            # item.unreal_pl_total_with_sign_sys_ccy += self._to_sys_ccy(trn.unreal_pl_total_with_sign,ccy)
            pass

    def _add_cash(self, items, trn, value, ccy, prtfl=None, acc=None, acc_interim=None, strg1=None, strg2=None,
                  strg3=None):

        if prtfl is None:
            prtfl = trn.portfolio
        if acc is None:
            acc = trn.account_cash
        if acc_interim is None:
            acc_interim = trn.account_interim
        if strg1 is None:
            strg1 = trn.strategy1_cash
        if strg2 is None:
            strg2 = trn.strategy2_cash
        if strg3 is None:
            strg3 = trn.strategy3_cash

        if trn.r_case == 0:
            item = self._get_item(items, trn, ccy=ccy, prtfl=prtfl, acc=acc,
                                  strg1=strg1, strg2=strg2, strg3=strg3)
            item.position_size += value

        elif trn.r_case == 1:
            item = self._get_item(items, trn, ccy=ccy, prtfl=prtfl, acc=acc_interim,
                                  strg1=strg1, strg2=strg2, strg3=strg3)
            item.position_size += value

        elif trn.r_case == 2:
            item = self._get_item(items, trn, ccy=ccy, prtfl=prtfl, acc=acc,
                                  strg1=strg1, strg2=strg2, strg3=strg3)
            item.position_size += value

            item = self._get_item(items, trn, ccy=ccy, prtfl=prtfl, acc=acc_interim,
                                  strg1=strg1, strg2=strg2, strg3=strg3)
            item.position_size += -value

        else:
            raise RuntimeError('Invalid transaction case: %s' % trn.case)

    def _process_final(self, items):
        for item in items:
            if item.instrument:
                price = self._get_instr_pricing(item.instrument)

                principal = item.position_size * item.instrument.price_multiplier * price.principal_price
                accrued = item.position_size * item.instrument.accrued_multiplier * price.accrued_price

                item.instr_principal_sys = self._to_sys_ccy(principal, item.instrument.pricing_currency)
                item.instr_accrued_sys = self._to_sys_ccy(accrued, item.instrument.accrued_currency)

                # balance
                item.market_value_sys = item.instr_principal_sys + item.instr_accrued_sys

                # P&L
                item.principal_sys += item.instr_principal_sys
                item.carry_sys += item.instr_accrued_sys

            elif item.currency:
                # balance
                item.market_value_sys = self._to_sys_ccy(item.position_size, item.currency)

                # P&L
                pass

            # balance
            item.market_value = self._to_res_ccy(item.market_value_sys)
            item.cost = self._to_res_ccy(item.cost_sys)

            # P&L
            item.total_sys = item.principal_sys + item.carry_sys + item.carry_sys

            item.instr_principal = self._to_res_ccy(item.instr_principal_sys)
            item.instr_accrued = self._to_res_ccy(item.instr_accrued_sys)
            item.principal = self._to_res_ccy(item.principal)
            item.carry = self._to_res_ccy(item.carry_sys)
            item.overheads = self._to_res_ccy(item.overheads_sys)
            item.total = self._to_res_ccy(item.total)

            if item.instrument:
                # # item.real_pl_principal_with_sign_res_ccy = self._to_res_ccy(item.real_pl_principal_with_sign_sys_ccy)
                # # item.real_pl_carry_with_sign_res_ccy = self._to_res_ccy(item.real_pl_carry_with_sign_sys_ccy)
                # # item.real_pl_overheads_with_sign_res_ccy = self._to_res_ccy(item.real_pl_overheads_with_sign_sys_ccy)
                item.total_real = self._to_res_ccy(item.total_real_sys)

                # item.unreal_pl_principal_with_sign_res_ccy = self._to_res_ccy(
                #     item.unreal_pl_principal_with_sign_sys_ccy)
                # item.unreal_pl_carry_with_sign_res_ccy = self._to_res_ccy(
                #     item.unreal_pl_carry_with_sign_sys_ccy)
                # item.unreal_pl_overheads_with_sign_res_ccy = self._to_res_ccy(
                #     item.unreal_pl_overheads_with_sign_sys_ccy)
                item.total_unreal_sys = item.market_value_sys + item.cost_sys
                item.total_unreal = self._to_res_ccy(item.total_unreal_sys)

    def _process_summary(self, summary, items):
        for item in items:
            summary.market_value_sys += item.market_value_sys
            summary.market_value += item.market_value

            summary.cost_sys += item.cost_sys
            summary.cost += item.cost

            # P&L
            summary.principal_sys += item.principal_sys
            summary.carry_sys += item.carry_sys
            summary.overheads_sys += item.overheads_sys
            summary.total_sys += item.total_sys

            summary.principal += item.principal
            summary.carry += item.carry
            summary.overheads += item.overheads
            summary.total += item.total

            # # summary.real_pl_principal_with_sign_sys_ccy += item.real_pl_principal_with_sign_sys_ccy
            # # summary.real_pl_carry_with_sign_sys_ccy += item.real_pl_carry_with_sign_sys_ccy
            # # summary.real_pl_overheads_with_sign_sys_ccy += item.real_pl_overheads_with_sign_sys_ccy
            # summary.real_pl_total_with_sign_sys_ccy += item.real_pl_total_with_sign_sys_ccy
            #
            # # summary.unreal_pl_principal_with_sign_sys_ccy += item.unreal_pl_principal_with_sign_sys_ccy
            # # summary.unreal_pl_carry_with_sign_sys_ccy += item.unreal_pl_carry_with_sign_sys_ccy
            # # summary.unreal_pl_overheads_with_sign_sys_ccy += item.unreal_pl_overheads_with_sign_sys_ccy
            # summary.unreal_pl_total_with_sign_sys_ccy += item.unreal_pl_total_with_sign_sys_ccy
            #
            # # summary.real_pl_principal_with_sign_res_ccy += item.real_pl_principal_with_sign_res_ccy
            # # summary.real_pl_carry_with_sign_res_ccy += item.real_pl_carry_with_sign_res_ccy
            # # summary.real_pl_overheads_with_sign_res_ccy += item.real_pl_overheads_with_sign_res_ccy
            # summary.real_pl_total_with_sign_res_ccy += item.real_pl_total_with_sign_res_ccy
            #
            # # summary.unreal_pl_principal_with_sign_res_ccy += item.unreal_pl_principal_with_sign_res_ccy
            # # summary.unreal_pl_carry_with_sign_res_ccy += item.unreal_pl_carry_with_sign_res_ccy
            # # summary.unreal_pl_overheads_with_sign_res_ccy += item.unreal_pl_overheads_with_sign_res_ccy
            # summary.unreal_pl_total_with_sign_res_ccy += item.unreal_pl_total_with_sign_res_ccy
            pass

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
