# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division

import copy
import logging
from collections import Counter, defaultdict
from datetime import timedelta
from itertools import groupby

from django.conf import settings
from django.db.models import Q
from django.utils.functional import cached_property
from django.utils.translation import ugettext, ugettext_lazy

from poms.accounts.models import Account, AccountType
from poms.common import formula
from poms.common.utils import date_now, isclose
from poms.currencies.models import Currency
from poms.instruments.models import Instrument, InstrumentType, CostMethod
from poms.obj_attrs.utils import get_attributes_prefetch
from poms.obj_perms.utils import get_permissions_prefetch_lookups
from poms.portfolios.models import Portfolio
from poms.reports.pricing import FakeInstrumentPricingProvider, FakeCurrencyFxRateProvider, CurrencyFxRateProvider
from poms.reports.pricing import InstrumentPricingProvider
from poms.reports.utils import sprint_table
from poms.strategies.models import Strategy1, Strategy2, Strategy3, Strategy1Subgroup, Strategy1Group, \
    Strategy2Subgroup, Strategy2Group, Strategy3Subgroup, Strategy3Group
from poms.tags.utils import get_tag_prefetch
from poms.transactions.models import TransactionClass, Transaction, ComplexTransaction

_l = logging.getLogger('poms.reports')


class _Base:
    report = None
    pricing_provider = None
    fx_rate_provider = None

    dump_columns = []

    def __init__(self, report, pricing_provider, fx_rate_provider):
        self.report = report
        self.pricing_provider = pricing_provider
        self.fx_rate_provider = fx_rate_provider

    def clone(self):
        return copy.copy(self)

    # def __getattr__(self, item):
    #     if item.endswith('_rep'):
    #         # automatic make value in report ccy
    #         item_sys = '%s_sys' % item[:-4]
    #         # if hasattr(self, item_sys):
    #         #     val = getattr(self, item_sys)
    #         #     if self.report_ccy_is_sys:
    #         #         return val
    #         #     else:
    #         #         fx = self.report_ccy_rep_fx
    #         #         if isclose(fx, 0.0):
    #         #             return 0.0
    #         #         return val / fx
    #         return getattr(self, item_sys)
    #     raise AttributeError(item)

    def dump_values(self, columns=None):
        if columns is None:
            columns = self.dump_columns
        row = []
        for f in columns:
            row.append(getattr(self, f))
        return row

    @classmethod
    def dumps(cls, items, columns=None):
        if columns is None:
            columns = cls.dump_columns

        data = []
        for item in items:
            data.append(item.dump_values(columns=columns))
        print(sprint_table(data, columns))
        # from io import StringIO
        # r = StringIO()
        # df.to_csv(r, sep=';')
        # print(r.getvalue())
        pass


class VirtualTransaction(_Base):
    trn = None
    pk = None
    is_hidden = False  # if True it is not involved in the calculations
    is_mismatch = True
    trn_code = None
    trn_cls = None
    # case = 0
    multiplier = 1.0
    closed_by = None

    # Position related
    instr = None
    trn_ccy = None
    pos_size = None

    # Cash related
    stl_ccy = None
    cash = None

    # P&L related
    principal = None
    carry = None
    overheads = None

    ref_fx = None

    # accounting dates
    trn_date = None
    acc_date = None
    cash_date = None

    # portfolio
    prtfl = None

    # accounts
    acc_pos = None
    acc_cash = None
    acc_interim = None

    # strategies
    str1_pos = None
    str1_cash = None
    str2_pos = None
    str2_cash = None
    str3_pos = None
    str3_cash = None

    # linked instrument
    link_instr = None

    # allocations
    alloc_bl = None
    alloc_pl = None

    # total_real_res = 0.0
    # total_unreal_res = 0.0

    # calculated ----------------------------------------------------
    case = 0

    # report ccy ----------------------------------------------------
    report_ccy_cur = None
    report_ccy_cur_fx = 0.0
    report_ccy_cash_hist = None
    report_ccy_cash_hist_fx = 0.0
    report_ccy_acc_hist = None
    report_ccy_acc_hist_fx = 0.0

    # instr
    instr_price_cur = None
    instr_price_cur_principal_price = 0.0
    instr_price_cur_accrued_price = 0.0
    instr_pricing_ccy_cur = None
    instr_pricing_ccy_cur_fx = 0.0
    instr_accrued_ccy_cur = None
    instr_accrued_ccy_cur_fx = 0.0

    # trn ccy ----------------------------------------------------
    trn_ccy_cash_hist = None
    trn_ccy_cash_hist_fx = 0.0
    trn_ccy_acc_hist = None
    trn_ccy_acc_hist_fx = 0.0
    trn_ccy_cur = None
    trn_ccy_cur_fx = 0.0

    # stl ccy ----------------------------------------------------
    stl_ccy_cash_hist = None
    stl_ccy_cash_hist_fx = 0.0
    stl_ccy_acc_hist = None
    stl_ccy_acc_hist_fx = 0.0
    stl_ccy_cur = None
    stl_ccy_cur_fx = 0.0

    # general ----------------------------------------------------

    mismatch = 0.0

    instr_principal = 0.0
    instr_principal_res = 0.0
    instr_accrued = 0.0
    instr_accrued_res = 0.0

    # Cash related ----------------------------------------------------

    cash_res = 0.0

    # full P&L related ----------------------------------------------------
    total = 0.0

    principal_res = 0.0
    carry_res = 0.0
    overheads_res = 0.0
    total_res = 0.0

    # full / closed ----------------------------------------------------
    principal_closed_res = 0.0
    carry_closed_res = 0.0
    overheads_closed_res = 0.0
    total_closed_res = 0.0

    # full / opened ----------------------------------------------------
    principal_opened_res = 0.0
    carry_opened_res = 0.0
    overheads_opened_res = 0.0
    total_opened_res = 0.0

    # fx ----------------------------------------------------
    pl_fx_mul = 0.0
    principal_fx_res = 0.0
    carry_fx_res = 0.0
    overheads_fx_res = 0.0
    total_fx_res = 0.0

    # fx / closed ----------------------------------------------------
    principal_fx_closed_res = 0.0
    carry_fx_closed_res = 0.0
    overheads_fx_closed_res = 0.0
    total_fx_closed_res = 0.0

    # fx / opened ----------------------------------------------------
    principal_fx_opened_res = 0.0
    carry_fx_opened_res = 0.0
    overheads_fx_opened_res = 0.0
    total_fx_opened_res = 0.0

    # fixed ----------------------------------------------------
    pl_fixed_mul = 0.0
    principal_fixed_res = 0.0
    carry_fixed_res = 0.0
    overheads_fixed_res = 0.0
    total_fixed_res = 0.0

    # fixed / closed ----------------------------------------------------
    principal_fixed_closed_res = 0.0
    carry_fixed_closed_res = 0.0
    overheads_fixed_closed_res = 0.0
    total_fixed_closed_res = 0.0

    # fixed / opened ----------------------------------------------------
    principal_fixed_opened_res = 0.0
    carry_fixed_opened_res = 0.0
    overheads_fixed_opened_res = 0.0
    total_fixed_opened_res = 0.0

    dump_columns = [
        'pk',
        'is_hidden',
        'is_mismatch',
        'trn_cls',
        # 'case',
        'multiplier',
        # 'acc_date',
        # 'cash_date',
        'instr',
        'trn_ccy',
        'stl_ccy',
        # 'prtfl',
        # 'acc_pos',
        # 'acc_cash',
        # 'acc_interim',
        # 'str1_pos',
        # 'str1_cash',
        # 'str2_pos',
        # 'str2_cash',
        # 'str3_pos',
        # 'str3_cash',
        # 'link_instr',
        'alloc_bl',
        'alloc_pl',
        'pos_size',
        'cash',
        # 'principal',
        # 'carry',
        # 'overheads',
        'total',
        # 'mismatch',
        # 'ref_fx',
        # 'trn_ccy_acc_hist_fx',
        # 'trn_ccy_cash_hist_fx',
        # 'trn_ccy_cur_fx',
        # 'stl_ccy_acc_hist_fx',
        # 'stl_ccy_cur_fx',
        # 'report_ccy_cash_hist_fx',
        # 'report_ccy_acc_hist_fx',
        # 'report_ccy_cur_fx',

        # 'instr_principal_res',
        # 'instr_accrued_res',

        # full ----------------------------------------------------
        # 'principal_res',
        # 'carry_res',
        # 'overheads_res',
        'total_res',

        # full / closed ----------------------------------------------------
        # 'principal_closed_res',
        # 'carry_closed_res',
        # 'overheads_closed_res',
        'total_closed_res',

        # full / opened ----------------------------------------------------
        # 'principal_opened_res',
        # 'carry_opened_res',
        # 'overheads_opened_res',
        'total_opened_res',

        # fx ----------------------------------------------------
        # 'principal_fx_res',
        # 'carry_fx_res',
        # 'overheads_fx_res',
        'total_fx_res',

        # fx / closed ----------------------------------------------------
        # 'principal_fx_closed_res',
        # 'carry_fx_closed_res',
        # 'overheads_fx_closed_res',
        'total_fx_closed_res',

        # fx / opened ----------------------------------------------------
        # 'principal_fx_opened_res',
        # 'carry_fx_opened_res',
        # 'overheads_fx_opened_res',
        'total_fx_opened_res',

        # fixed ----------------------------------------------------
        # 'principal_fixed_res',
        # 'carry_fixed_res',
        # 'overheads_fixed_res',
        'total_fixed_res',

        # fixed / closed ----------------------------------------------------
        # 'principal_fixed_closed_res',
        # 'carry_fixed_closed_res',
        # 'overheads_fixed_closed_res',
        'total_fixed_closed_res',

        # fixed / opened ----------------------------------------------------
        # 'principal_fixed_opened_res',
        # 'carry_fixed_opened_res',
        # 'overheads_fixed_opened_res',
        'total_fixed_opened_res',
    ]

    def __init__(self, report, pricing_provider, fx_rate_provider, trn, overrides=None):
        super(VirtualTransaction, self).__init__(report, pricing_provider, fx_rate_provider)
        overrides = overrides or {}
        self.trn = trn
        self.pk = overrides.get('pk', trn.pk)
        self.trn_code = overrides.get('transaction_code', trn.transaction_code)
        self.trn_cls = overrides.get('transaction_class', trn.transaction_class)

        self.instr = overrides.get('instrument', trn.instrument)
        self.trn_ccy = overrides.get('transaction_currency', trn.transaction_currency)
        self.pos_size = overrides.get('position_size_with_sign', trn.position_size_with_sign)

        self.stl_ccy = overrides.get('settlement_currency', trn.settlement_currency)
        self.cash = overrides.get('cash_consideration', trn.cash_consideration)

        self.principal = overrides.get('principal_with_sign', trn.principal_with_sign)
        self.carry = overrides.get('carry_with_sign', trn.carry_with_sign)
        self.overheads = overrides.get('overheads_with_sign', trn.overheads_with_sign)

        self.ref_fx = overrides.get('reference_fx_rate', trn.reference_fx_rate)

        self.trn_date = overrides.get('transaction_date', trn.transaction_date)
        self.acc_date = overrides.get('accounting_date', trn.accounting_date)
        self.cash_date = overrides.get('cash_date', trn.cash_date)

        self.prtfl = overrides.get('portfolio', trn.portfolio)

        self.acc_pos = overrides.get('account_position', trn.account_position)
        self.acc_cash = overrides.get('account_cash', trn.account_cash)
        self.acc_interim = overrides.get('account_interim', trn.account_interim)

        self.str1_pos = overrides.get('strategy1_position', trn.strategy1_position)
        self.str1_cash = overrides.get('strategy1_cash', trn.strategy1_cash)
        self.str2_pos = overrides.get('strategy2_position', trn.strategy2_position)
        self.str2_cash = overrides.get('strategy2_cash', trn.strategy2_cash)
        self.str3_pos = overrides.get('strategy3_position', trn.strategy3_position)
        self.str3_cash = overrides.get('strategy3_cash', trn.strategy3_cash)

        self.link_instr = overrides.get('linked_instrument', trn.linked_instrument)

        self.alloc_bl = overrides.get('allocation_balance', trn.allocation_balance)
        self.alloc_pl = overrides.get('allocation_pl', trn.allocation_pl)

        # ----

        if self.acc_date <= self.report.report_date < self.cash_date:
            self.case = 1
        elif self.cash_date <= self.report.report_date < self.acc_date:
            self.case = 2
        else:
            self.case = 0

    def __str__(self):
        return str(self.pk)

    def pricing(self):
        # report ccy ----------------------------------------------------
        self.report_ccy_cur = self.fx_rate_provider[self.report.report_currency]
        self.report_ccy_cur_fx = self.report_ccy_cur.fx_rate
        self.report_ccy_cash_hist = self.fx_rate_provider[self.report.report_currency, self.acc_date]
        self.report_ccy_cash_hist_fx = self.report_ccy_cash_hist.fx_rate
        self.report_ccy_acc_hist = self.fx_rate_provider[self.report.report_currency, self.cash_date]
        self.report_ccy_acc_hist_fx = self.report_ccy_acc_hist.fx_rate

        try:
            report_ccy_cur_fx = 1.0 / self.report_ccy_cur_fx
        except ZeroDivisionError:
            report_ccy_cur_fx = 0.0

        try:
            report_ccy_cash_hist_fx = 1.0 / self.report_ccy_cash_hist_fx
        except ZeroDivisionError:
            report_ccy_cash_hist_fx = 0.0

        try:
            report_ccy_acc_hist_fx = 1.0 / self.report_ccy_acc_hist_fx
        except ZeroDivisionError:
            report_ccy_acc_hist_fx = 0.0

        # instr ----------------------------------------------------
        if self.instr:
            self.instr_price_cur = self.pricing_provider[self.instr]
            self.instr_price_cur_principal_price = self.instr_price_cur.principal_price
            self.instr_price_cur_accrued_price = self.instr_price_cur.accrued_price
            self.instr_pricing_ccy_cur = self.fx_rate_provider[self.instr.pricing_currency]
            self.instr_pricing_ccy_cur_fx = self.instr_pricing_ccy_cur.fx_rate * report_ccy_cur_fx
            self.instr_accrued_ccy_cur = self.fx_rate_provider[self.instr.accrued_currency]
            self.instr_accrued_ccy_cur_fx = self.instr_accrued_ccy_cur.fx_rate * report_ccy_cur_fx

        # trn ccy ----------------------------------------------------
        if self.trn_ccy:
            self.trn_ccy_cash_hist = self.fx_rate_provider[self.trn_ccy, self.cash_date]
            self.trn_ccy_cash_hist_fx = self.trn_ccy_cash_hist.fx_rate * report_ccy_cash_hist_fx
            self.trn_ccy_acc_hist = self.fx_rate_provider[self.trn_ccy, self.acc_date]
            self.trn_ccy_acc_hist_fx = self.trn_ccy_acc_hist.fx_rate * report_ccy_acc_hist_fx
            self.trn_ccy_cur = self.fx_rate_provider[self.trn_ccy]
            self.trn_ccy_cur_fx = self.trn_ccy_cur.fx_rate * report_ccy_cur_fx

        # stl ccy ----------------------------------------------------
        if self.stl_ccy:
            self.stl_ccy_cash_hist = self.fx_rate_provider[self.stl_ccy, self.cash_date]
            self.stl_ccy_cash_hist_fx = self.stl_ccy_cash_hist.fx_rate * report_ccy_cash_hist_fx
            self.stl_ccy_acc_hist = self.fx_rate_provider[self.stl_ccy, self.acc_date]
            self.stl_ccy_acc_hist_fx = self.stl_ccy_acc_hist.fx_rate * report_ccy_cash_hist_fx
            self.stl_ccy_cur = self.fx_rate_provider[self.stl_ccy]
            self.stl_ccy_cur_fx = self.stl_ccy_cur.fx_rate * report_ccy_cur_fx

    def calc(self):
        # if not self.is_hidden:
        #     print(1)
        if self.trn_cls.id in [TransactionClass.BUY, TransactionClass.SELL, TransactionClass.TRANSACTION_PL,
                               TransactionClass.INSTRUMENT_PL, TransactionClass.FX_TRADE]:
            if self.instr:
                self.instr_principal = self.pos_size * self.instr.price_multiplier * self.instr_price_cur_principal_price
                self.instr_principal_res = self.instr_principal * self.instr_pricing_ccy_cur_fx

                self.instr_accrued = self.pos_size * self.instr.accrued_multiplier * self.instr_price_cur_accrued_price
                self.instr_accrued_res = self.instr_accrued * self.instr_pricing_ccy_cur_fx

            # Cash related ----------------------------------------------------

            self.cash_res = self.cash * self.stl_ccy_cur_fx

            # full P&L related ----------------------------------------------------
            self.total = self.principal + self.carry + self.overheads

            self.principal_res = self.principal * self.stl_ccy_cur_fx
            self.carry_res = self.carry * self.stl_ccy_cur_fx
            self.overheads_res = self.overheads * self.stl_ccy_cur_fx
            self.total_res = self.total * self.stl_ccy_cur_fx

            self.pl_fx_mul = self.stl_ccy_cur_fx - self.ref_fx * self.trn_ccy_cash_hist_fx
            self.pl_fixed_mul = self.ref_fx * self.trn_ccy_cash_hist_fx

            # full / closed ----------------------------------------------------
            self.principal_closed_res = self.principal_res * self.multiplier
            self.carry_closed_res = self.carry_res * self.multiplier
            self.overheads_closed_res = self.overheads_res * self.multiplier
            self.total_closed_res = self.total_res * self.multiplier

            # full / opened ----------------------------------------------------
            self.principal_opened_res = self.principal_res * (1.0 - self.multiplier)
            self.carry_opened_res = self.carry_res * (1.0 - self.multiplier)
            self.overheads_opened_res = self.overheads_res * (1.0 - self.multiplier)
            self.total_opened_res = self.total_res * (1.0 - self.multiplier)

            # fx ----------------------------------------------------
            self.principal_fx_res = self.principal * self.pl_fx_mul
            self.carry_fx_res = self.carry * self.pl_fx_mul
            self.overheads_fx_res = self.overheads * self.pl_fx_mul
            self.total_fx_res = self.total * self.pl_fx_mul

            # fx / closed ----------------------------------------------------
            self.principal_fx_closed_res = self.principal_fx_res * self.multiplier
            self.carry_fx_closed_res = self.carry_fx_res * self.multiplier
            self.overheads_fx_closed_res = self.overheads_fx_res * self.multiplier
            self.total_fx_closed_res = self.total_fx_res * self.multiplier

            # fx / opened ----------------------------------------------------
            self.principal_fx_opened_res = self.principal_fx_res * (1.0 - self.multiplier)
            self.carry_fx_opened_res = self.carry_fx_res * (1.0 - self.multiplier)
            self.overheads_fx_opened_res = self.overheads_fx_res * (1.0 - self.multiplier)
            self.total_fx_opened_res = self.total_fx_res * (1.0 - self.multiplier)

            # fixed ----------------------------------------------------
            self.principal_fixed_res = self.principal * self.pl_fixed_mul
            self.carry_fixed_res = self.carry * self.pl_fixed_mul
            self.overheads_fixed_res = self.overheads * self.pl_fixed_mul
            self.total_fixed_res = self.total * self.pl_fixed_mul

            # fixed / closed ----------------------------------------------------
            self.principal_fixed_closed_res = self.principal_fixed_res * self.multiplier
            self.carry_fixed_closed_res = self.carry_fixed_res * self.multiplier
            self.overheads_fixed_closed_res = self.overheads_fixed_res * self.multiplier
            self.total_fixed_closed_res = self.total_fixed_res * self.multiplier

            # fixed / opened ----------------------------------------------------
            self.principal_fixed_opened_res = self.principal_fixed_res * (1.0 - self.multiplier)
            self.carry_fixed_opened_res = self.carry_fixed_res * (1.0 - self.multiplier)
            self.overheads_fixed_opened_res = self.overheads_fixed_res * (1.0 - self.multiplier)
            self.total_fixed_opened_res = self.total_fixed_res * (1.0 - self.multiplier)

        elif self.trn_cls.id in [TransactionClass.CASH_INFLOW, TransactionClass.CASH_OUTFLOW]:
            self.pl_fx_mul = self.stl_ccy_cur_fx - self.ref_fx * self.trn_ccy_acc_hist_fx
            self.pl_fixed_mul = self.ref_fx * self.trn_ccy_acc_hist_fx

            self.principal_res = self.cash * self.pl_fx_mul
            self.principal_closed_res = self.principal_res
            self.principal_fx_res = self.principal_res
            self.principal_fx_closed_res = self.principal_res

        if self.trn_cls.id in [TransactionClass.CASH_INFLOW, TransactionClass.CASH_OUTFLOW]:
            self.mismatch = 0.0
        else:
            self.mismatch = self.cash - self.total

    @staticmethod
    def approach_clone(cur, closed, mul_delta):

        # def _t1_a(attr):
        #     setattr(t1, attr, -(getattr(closed, attr) * abm + getattr(cur, attr) * aem))
        #
        # def _t1_pl(principal_attr, carry_attr, overheads_attr, total_attr):
        #     _t1_a(principal_attr)
        #     _t1_a(carry_attr)
        #     _t1_a(overheads_attr)
        #     setattr(t1, total_attr,
        #             getattr(t1, principal_attr) + getattr(t1, carry_attr) + getattr(t1, overheads_attr))
        #
        # def _t2_a(attr):
        #     setattr(t2, attr, - getattr(t1, attr))
        #
        # def _t2_pl(principal_attr, carry_attr, overheads_attr, total_attr):
        #     _t2_a(principal_attr)
        #     _t2_a(carry_attr)
        #     _t2_a(overheads_attr)
        #     _t2_a(total_attr)

        def _clean(t):
            t.is_mismatch = False

            t.report_ccy_cur = None
            t.report_ccy_cur_fx = float('nan')
            t.report_ccy_cash_hist = None
            t.report_ccy_cash_hist_fx = float('nan')
            t.report_ccy_acc_hist = None
            t.report_ccy_acc_hist_fx = float('nan')

            t.instr_price_cur = None
            t.instr_price_cur_principal_price = float('nan')
            t.instr_price_cur_accrued_price = float('nan')
            t.instr_pricing_ccy_cur = None
            t.instr_pricing_ccy_cur_fx = float('nan')
            t.instr_accrued_ccy_cur = None
            t.instr_accrued_ccy_cur_fx = float('nan')

            t.trn_ccy_cash_hist = None
            t.trn_ccy_cash_hist_fx = float('nan')
            t.trn_ccy_acc_hist = None
            t.trn_ccy_acc_hist_fx = float('nan')
            t.trn_ccy_cur = None
            t.trn_ccy_cur_fx = float('nan')

            t.stl_ccy_cash_hist = None
            t.stl_ccy_cash_hist_fx = float('nan')
            t.stl_ccy_acc_hist = None
            t.stl_ccy_acc_hist_fx = float('nan')
            t.stl_ccy_cur = None
            t.stl_ccy_cur_fx = float('nan')

            t.mismatch = 0.0
            t.multiplier = 1.0
            t.cash = 0.0
            t.cash_res = 0.0

            t.instr_principal = float('nan')
            t.instr_principal_res = 0.0
            t.instr_accrued = float('nan')
            t.instr_accrued_res = 0.0

            t.principal = float('nan')
            t.carry = float('nan')
            t.overheads = float('nan')
            t.total = float('nan')

            t.pl_fx_mul = float('nan')
            t.pl_fixed_mul = float('nan')

        pos_size = abs(closed.pos_size * mul_delta)

        try:
            abm = closed.report.approach_begin_multiplier * abs(pos_size / closed.pos_size)
        except ZeroDivisionError:
            abm = 0.0
        try:
            aem = closed.report.approach_end_multiplier * abs(pos_size / cur.pos_size)
        except ZeroDivisionError:
            aem = 0.0

        # abm = closed.report.approach_begin_multiplier * closed1.multiplier
        # aem = closed.report.approach_end_multiplier * cur1.multiplier
        # abm = closed.report.approach_begin_multiplier
        # aem = closed.report.approach_end_multiplier

        closed1 = closed
        # closed1 = closed.clone()
        # closed1.multiplier = abs(pos_size / closed.pos_size)
        # closed1.principal_res = closed.principal_res * closed1.multiplier
        # closed1.carry_res = closed.principal_res * closed1.multiplier
        # closed1.overheads_res = closed.principal_res * closed1.multiplier
        # closed1.total_res = closed.principal_res * closed1.multiplier
        # closed1.calc()

        cur1 = cur
        # cur1 = cur.clone()
        # cur1.multiplier = abs(pos_size / cur.pos_size)
        # cur1.principal_res = cur.principal_res * cur1.multiplier
        # cur1.carry_res = cur.principal_res * cur1.multiplier
        # cur1.overheads_res = cur.principal_res * cur1.multiplier
        # cur1.total_res = cur.principal_res * cur1.multiplier
        # cur1.calc()

        # t1 ----
        t1 = closed1.clone()
        t1.trn_cls = cur1.trn_cls
        t1.pk = 'a1,%s,%s,%s' % (closed1.pk, cur1.pk, t1.trn_cls)

        _clean(t1)

        t1.pos_size = -pos_size

        t1.principal_res = -(closed1.principal_res * abm + cur1.principal_res * aem)
        t1.carry_res = -(closed1.carry_res * abm + cur1.carry_res * aem)
        t1.overheads_res = -(closed1.overheads_res * abm + cur1.overheads_res * aem)
        t1.total_res = t1.principal_res + t1.carry_res + t1.overheads_res

        # t1.principal_closed_res = -(closed1.principal_closed_res * abm + cur1.principal_closed_res * aem)
        # t1.carry_closed_res = -(closed1.carry_closed_res * abm + cur1.carry_closed_res * aem)
        # t1.overheads_closed_res = -(closed1.overheads_closed_res * abm + cur1.overheads_closed_res * aem)
        # t1.total_closed_res = t1.principal_closed_res + t1.carry_closed_res + t1.overheads_closed_res
        t1.principal_closed_res = t1.principal_res
        t1.carry_closed_res = t1.carry_res
        t1.overheads_closed_res = t1.overheads_res
        t1.total_closed_res = t1.total_res

        # t1.principal_opened_res = -(closed1.principal_opened_res * abm + cur1.principal_opened_res * aem)
        # t1.carry_opened_res = -(closed1.carry_opened_res * abm + cur1.carry_opened_res * aem)
        # t1.overheads_opened_res = -(closed1.overheads_opened_res * abm + cur1.overheads_opened_res * aem)
        # t1.total_opened_res = t1.principal_opened_res + t1.carry_opened_res + t1.overheads_opened_res
        t1.principal_opened_res = 0.0
        t1.carry_opened_res = 0.0
        t1.overheads_opened_res = 0.0
        t1.total_opened_res = 0.0

        t1.principal_fx_res = -(closed1.principal_fx_res * abm + cur1.principal_fx_res * aem)
        t1.carry_fx_res = -(closed1.carry_fx_res * abm + cur1.carry_fx_res * aem)
        t1.overheads_fx_res = -(closed1.overheads_fx_res * abm + cur1.overheads_fx_res * aem)
        t1.total_fx_res = t1.principal_fx_res + t1.carry_fx_res + t1.overheads_fx_res

        # t1.principal_fx_closed_res = -(closed1.principal_fx_closed_res * abm + cur1.principal_fx_closed_res * aem)
        # t1.carry_fx_closed_res = -(closed1.carry_fx_closed_res * abm + cur1.carry_fx_closed_res * aem)
        # t1.overheads_fx_closed_res = -(closed1.overheads_fx_closed_res * abm + cur1.overheads_fx_closed_res * aem)
        # t1.total_fx_closed_res = t1.principal_fx_closed_res + t1.carry_fx_closed_res + t1.overheads_fx_closed_res
        t1.principal_fx_closed_res = t1.principal_fx_res
        t1.carry_fx_closed_res = t1.carry_fx_res
        t1.overheads_fx_closed_res = t1.overheads_fx_res
        t1.total_fx_closed_res = t1.total_fx_res

        # t1.principal_fx_opened_res = -(closed1.principal_fx_opened_res * abm + cur1.principal_fx_opened_res * aem)
        # t1.carry_fx_opened_res = -(closed1.carry_fx_opened_res * abm + cur1.carry_fx_opened_res * aem)
        # t1.overheads_fx_opened_res = -(closed1.overheads_fx_opened_res * abm + cur1.overheads_fx_opened_res * aem)
        # t1.total_fx_opened_res = t1.principal_fx_opened_res + t1.carry_fx_opened_res + t1.overheads_fx_opened_res
        t1.principal_fx_opened_res = 0.0
        t1.carry_fx_opened_res = 0.0
        t1.overheads_fx_opened_res = 0.0
        t1.total_fx_opened_res = 0.0

        t1.principal_fixed_res = -(closed1.principal_fixed_res * abm + cur1.principal_fixed_res * aem)
        t1.carry_fixed_res = -(closed1.carry_fixed_res * abm + cur1.carry_fixed_res * aem)
        t1.overheads_fixed_res = -(closed1.overheads_fixed_res * abm + cur1.overheads_fixed_res * aem)
        t1.total_fixed_res = t1.principal_fixed_res + t1.carry_fixed_res + t1.overheads_fixed_res

        # t1.principal_fixed_closed_res = -(
        #     closed1.principal_fixed_closed_res * abm + cur1.principal_fixed_closed_res * aem)
        # t1.carry_fixed_closed_res = -(closed1.carry_fixed_closed_res * abm + cur1.carry_fixed_closed_res * aem)
        # t1.overheads_fixed_closed_res = -(
        #     closed1.overheads_fixed_closed_res * abm + cur1.overheads_fixed_closed_res * aem)
        # t1.total_fixed_closed_res = t1.principal_fixed_closed_res + t1.carry_fixed_closed_res + t1.overheads_fixed_closed_res
        t1.principal_fixed_closed_res = t1.principal_fixed_res
        t1.carry_fixed_closed_res = t1.carry_fixed_res
        t1.overheads_fixed_closed_res = t1.overheads_fixed_res
        t1.total_fixed_closed_res = t1.total_fixed_res

        # t1.principal_fixed_opened_res = -(
        #     closed1.principal_fixed_opened_res * abm + cur1.principal_fixed_opened_res * aem)
        # t1.carry_fixed_opened_res = -(closed1.carry_fixed_opened_res * abm + cur1.carry_fixed_opened_res * aem)
        # t1.overheads_fixed_opened_res = -(
        #     closed1.overheads_fixed_opened_res * abm + cur1.overheads_fixed_opened_res * aem)
        # t1.total_fixed_opened_res = t1.principal_fixed_opened_res + t1.carry_fixed_opened_res + t1.overheads_fixed_opened_res
        t1.principal_fixed_opened_res = 0.0
        t1.carry_fixed_opened_res = 0.0
        t1.overheads_fixed_opened_res = 0.0
        t1.total_fixed_opened_res = 0.0

        # t2 ----
        t2 = cur1.clone()
        t2.trn_cls = closed1.trn_cls
        t2.pk = 'a2,%s,%s,%s' % (closed1.pk, cur1.pk, t2.trn_cls)

        _clean(t2)

        t2.pos_size = -t1.pos_size

        t2.principal_res = -t1.principal_res
        t2.carry_res = -t1.carry_res
        t2.overheads_res = -t1.overheads_res
        t2.total_res = -t1.total_res

        t2.principal_closed_res = -t1.principal_closed_res
        t2.carry_closed_res = -t1.carry_closed_res
        t2.overheads_closed_res = -t1.overheads_closed_res
        t2.total_closed_res = -t1.total_closed_res

        t2.principal_opened_res = -t1.principal_opened_res
        t2.carry_opened_res = -t1.carry_opened_res
        t2.overheads_opened_res = -t1.overheads_opened_res
        t2.total_opened_res = -t1.total_opened_res

        t2.principal_fx_res = -t1.principal_fx_res
        t2.carry_fx_res = -t1.carry_fx_res
        t2.overheads_fx_res = -t1.overheads_fx_res
        t2.total_fx_res = -t1.total_fx_res

        t2.principal_fx_closed_res = -t1.principal_fx_closed_res
        t2.carry_fx_closed_res = -t1.carry_fx_closed_res
        t2.overheads_fx_closed_res = -t1.overheads_fx_closed_res
        t2.total_fx_closed_res = -t1.total_fx_closed_res

        t2.principal_fx_opened_res = -t1.principal_fx_opened_res
        t2.carry_fx_opened_res = -t1.carry_fx_opened_res
        t2.overheads_fx_opened_res = -t1.overheads_fx_opened_res
        t2.total_fx_opened_res = -t1.total_fx_opened_res

        t2.principal_fixed_res = -t1.principal_fixed_res
        t2.carry_fixed_res = -t1.carry_fixed_res
        t2.overheads_fixed_res = -t1.overheads_fixed_res
        t2.total_fixed_res = -t1.total_fixed_res

        t2.principal_fixed_closed_res = -t1.principal_fixed_closed_res
        t2.carry_fixed_closed_res = -t1.carry_fixed_closed_res
        t2.overheads_fixed_closed_res = -t1.overheads_fixed_closed_res
        t2.total_fixed_closed_res = -t1.total_fixed_closed_res

        t2.principal_fixed_opened_res = -t1.principal_fixed_opened_res
        t2.carry_fixed_opened_res = -t1.carry_fixed_opened_res
        t2.overheads_fixed_opened_res = -t1.overheads_fixed_opened_res
        t2.total_fixed_opened_res = -t1.total_fixed_opened_res

        return t1, t2

    def transfer_clone(self, t1_cls, t2_cls, t1_pos_sign=-1.0, t1_cash_sign=1.0):
        # t1
        t1 = self.clone()
        t1.is_mismatch = False
        t1.trn_cls = t1_cls
        t1.acc_pos = self.acc_cash
        t1.acc_cash = self.acc_cash
        t1.str1_pos = self.str1_cash
        t1.str1_cash = self.str1_cash
        t1.str2_pos = self.str2_cash
        t1.str2_cash = self.str2_cash
        t1.str3_pos = self.str2_cash
        t1.str3_cash = self.str3_cash

        t1.pos_size = self.pos_size * t1_pos_sign
        t1.cash = self.pos_size * t1_pos_sign
        t1.principal = self.pos_size * t1_cash_sign
        t1.carry = self.pos_size * t1_cash_sign
        t1.overheads = self.pos_size * t1_cash_sign
        t1.calc()

        # t2
        t2 = self.clone()
        t2.is_mismatch = False
        t2.trn_cls = t2_cls
        t2.acc_pos = self.acc_cash
        t2.acc_cash = self.acc_cash
        t2.str1_pos = self.str1_cash
        t2.str1_cash = self.str1_cash
        t2.str2_pos = self.str2_cash
        t2.str2_cash = self.str2_cash
        t2.str3_pos = self.str2_cash
        t2.str3_cash = self.str3_cash

        t2.pos_size = -t1.pos_size
        t2.cash = -t1.pos_size
        t2.principal = -t1.pos_size
        t2.carry = -t1.pos_size
        t2.overheads = -t1.pos_size
        t2.calc()
        return t1, t2

    def fx_trade_clone(self):
        # t1
        t1 = self.clone()
        t1.is_hidden = False
        t1.is_mismatch = False
        t1.trn_ccy = self.trn_ccy
        t1.stl_ccy = self.trn_ccy
        t1.principal = self.pos_size
        t1.cash = self.pos_size
        t1.ref_fx = 1.0
        t1.pricing()
        t1.calc()

        # t2
        t2 = self.clone()
        t2.is_hidden = False
        t2.is_mismatch = False
        t2.trn_ccy = self.trn_ccy
        t2.stl_ccy = self.stl_ccy
        t2.pos_size = self.principal
        t2.cash = self.principal
        t2.principal = self.principal
        try:
            t2.ref_fx = abs(self.pos_size / self.principal)
        except ZeroDivisionError:
            t2.ref_fx = 0.0
        t2.pricing()
        t2.calc()
        return t1, t2

    # globals ----------------------------------------------------

    def is_show_details(self, acc):
        if self.case in [1, 2] and self.report.show_transaction_details:
            return acc and acc.type and acc.type.show_transaction_details
        return False


class ReportItem(_Base):
    TYPE_UNKNOWN = 0
    TYPE_INSTRUMENT = 1
    TYPE_CURRENCY = 2
    TYPE_TRANSACTION_PL = 3
    TYPE_FX_TRADE = 4
    TYPE_CASH_IN_OUT = 5
    TYPE_MISMATCH = 100  # Linked instrument
    TYPE_SUMMARY = 200
    # TYPE_INVESTED_CURRENCY = 300
    # TYPE_INVESTED_SUMMARY = 301
    TYPE_CHOICES = (
        (TYPE_UNKNOWN, ugettext_lazy('Unknown')),
        (TYPE_INSTRUMENT, ugettext_lazy('Instrument')),
        (TYPE_CURRENCY, ugettext_lazy('Currency')),
        (TYPE_TRANSACTION_PL, ugettext_lazy('Transaction PL')),
        (TYPE_FX_TRADE, ugettext_lazy('FX-Trade')),
        (TYPE_CASH_IN_OUT, ugettext_lazy('Cash In/Out')),
        (TYPE_MISMATCH, ugettext_lazy('Mismatch')),
        (TYPE_SUMMARY, ugettext_lazy('Summary')),
        # (TYPE_INVESTED_CURRENCY, 'Invested'),
        # (TYPE_INVESTED_SUMMARY, 'Invested summary'),
    )

    type = None
    trn = None

    instr = None
    ccy = None
    trn_ccy = None  # for FX_TRADE
    prtfl = None
    acc = None
    str1 = None
    str2 = None
    str3 = None
    # detail_trn = None
    custom_fields = []
    is_empty = False

    # link
    mismatch = 0.0
    # mismatch_ccy = None
    mismatch_prtfl = None
    mismatch_acc = None

    # allocations
    alloc_bl = None
    alloc_pl = None

    # pricing
    report_ccy_cur = None
    report_ccy_cur_fx = 0.0
    instr_price_cur = None
    instr_price_cur_principal_price = 0.0
    instr_price_cur_accrued_price = 0.0
    instr_pricing_ccy_cur = None
    instr_pricing_ccy_cur_fx = 0.0
    instr_accrued_ccy_cur = None
    instr_accrued_ccy_cur_fx = 0.0
    ccy_cur = None
    ccy_cur_fx = 0.0

    # instr

    instr_principal_res = 0.0
    instr_accrued_res = 0.0
    exposure_res = 0.0

    # balance
    pos_size = 0.0
    market_value_res = 0.0
    cost_res = 0.0

    # full ----------------------------------------------------
    principal_res = 0.0
    carry_res = 0.0
    overheads_res = 0.0
    total_res = 0.0

    # full / closed ----------------------------------------------------
    principal_closed_res = 0.0
    carry_closed_res = 0.0
    overheads_closed_res = 0.0
    total_closed_res = 0.0

    # full / opened ----------------------------------------------------
    principal_opened_res = 0.0
    carry_opened_res = 0.0
    overheads_opened_res = 0.0
    total_opened_res = 0.0

    # fx ----------------------------------------------------
    principal_fx_res = 0.0
    carry_fx_res = 0.0
    overheads_fx_res = 0.0
    total_fx_res = 0.0

    # fx / closed ----------------------------------------------------
    principal_fx_closed_res = 0.0
    carry_fx_closed_res = 0.0
    overheads_fx_closed_res = 0.0
    total_fx_closed_res = 0.0

    # fx / opened ----------------------------------------------------
    principal_fx_opened_res = 0.0
    carry_fx_opened_res = 0.0
    overheads_fx_opened_res = 0.0
    total_fx_opened_res = 0.0

    # fixed ----------------------------------------------------
    principal_fixed_res = 0.0
    carry_fixed_res = 0.0
    overheads_fixed_res = 0.0
    total_fixed_res = 0.0

    # fixed / closed ----------------------------------------------------
    principal_fixed_closed_res = 0.0
    carry_fixed_closed_res = 0.0
    overheads_fixed_closed_res = 0.0
    total_fixed_closed_res = 0.0

    # fixed / opened ----------------------------------------------------
    principal_fixed_opened_res = 0.0
    carry_fixed_opened_res = 0.0
    overheads_fixed_opened_res = 0.0
    total_fixed_opened_res = 0.0

    dump_columns = [
        'type_code',
        'user_code',
        'short_name',
        'name',
        # 'trn',
        # 'prtfl',
        # 'acc',
        # 'str1',
        # 'str2',
        # 'str3',
        # 'detail_trn',
        'instr',
        'ccy',
        'trn_ccy',
        # 'alloc_bl',
        # 'alloc_pl',

        # 'mismatch_prtfl',
        # 'mismatch_acc',
        # 'mismatch_ccy',
        'mismatch',

        'pos_size',
        'market_value_res',

        # 'cost_res',
        # 'instr_principal_res',
        # 'instr_accrued_res',

        # full ----------------------------------------------------
        # 'principal_res',
        # 'carry_res',
        # 'overheads_res',
        'total_res',

        # full / closed ----------------------------------------------------
        # 'principal_closed_res',
        # 'carry_closed_res',
        # 'overheads_closed_res',
        'total_closed_res',

        # full / opened ----------------------------------------------------
        # 'principal_opened_res',
        # 'carry_opened_res',
        # 'overheads_opened_res',
        'total_opened_res',

        # fx ----------------------------------------------------
        # 'principal_fx_res',
        # 'carry_fx_res',
        # 'overheads_fx_res',
        'total_fx_res',

        # fx / closed ----------------------------------------------------
        # 'principal_fx_closed_res',
        # 'carry_fx_closed_res',
        # 'overheads_fx_closed_res',
        'total_fx_closed_res',

        # fx / opened ----------------------------------------------------
        # 'principal_fx_opened_res',
        # 'carry_fx_opened_res',
        # 'overheads_fx_opened_res',
        'total_fx_opened_res',

        # fixed ----------------------------------------------------
        # 'principal_fixed_res',
        # 'carry_fixed_res',
        # 'overheads_fixed_res',
        'total_fixed_res',

        # fixed / closed ----------------------------------------------------
        # 'principal_fixed_closed_res',
        # 'carry_fixed_closed_res',
        # 'overheads_fixed_closed_res',
        'total_fixed_closed_res',

        # fixed / opened ----------------------------------------------------
        # 'principal_fixed_opened_res',
        # 'carry_fixed_opened_res',
        # 'overheads_fixed_opened_res',
        'total_fixed_opened_res',
    ]

    def __init__(self, report, pricing_provider, fx_rate_provider, type):
        super(ReportItem, self).__init__(report, pricing_provider, fx_rate_provider)
        self.type = type

    @classmethod
    def from_trn(cls, report, pricing_provider, fx_rate_provider, type, trn, instr=None, ccy=None, trn_ccy=None,
                 prtfl=None, acc=None, str1=None, str2=None, str3=None, val=None):
        item = cls(report, pricing_provider, fx_rate_provider, type)
        item.trn = trn

        # item.instr = instr  # -> Instrument
        # item.ccy = ccy  # -> Currency
        item.prtfl = prtfl or trn.prtfl  # -> Portfolio
        item.alloc_bl = trn.alloc_bl
        item.alloc_pl = trn.alloc_pl

        if type in [ReportItem.TYPE_INSTRUMENT, ReportItem.TYPE_TRANSACTION_PL, ReportItem.TYPE_FX_TRADE,
                    ReportItem.TYPE_CASH_IN_OUT]:
            # full ----------------------------------------------------
            item.principal_res = trn.principal_res
            item.carry_res = trn.carry_res
            item.overheads_res = trn.overheads_res
            item.total_res = trn.total_res

            # full / closed ----------------------------------------------------
            item.principal_closed_res = trn.principal_closed_res
            item.carry_closed_res = trn.carry_closed_res
            item.overheads_closed_res = trn.overheads_closed_res
            item.total_closed_res = trn.total_closed_res

            # full / opened ----------------------------------------------------
            item.principal_opened_res = trn.principal_opened_res
            item.carry_opened_res = trn.carry_opened_res
            item.overheads_opened_res = trn.overheads_opened_res
            item.total_opened_res = trn.total_opened_res

            # fx ----------------------------------------------------
            item.principal_fx_res = trn.principal_fx_res
            item.carry_fx_res = trn.carry_fx_res
            item.overheads_fx_res = trn.overheads_fx_res
            item.total_fx_res = trn.total_fx_res

            # fx / closed ----------------------------------------------------
            item.principal_fx_closed_res = trn.principal_fx_closed_res
            item.carry_fx_closed_res = trn.carry_fx_closed_res
            item.overheads_fx_closed_res = trn.overheads_fx_closed_res
            item.total_fx_closed_res = trn.total_fx_closed_res

            # fx / opened ----------------------------------------------------
            item.principal_fx_opened_res = trn.principal_fx_opened_res
            item.carry_fx_opened_res = trn.carry_fx_opened_res
            item.overheads_fx_opened_res = trn.overheads_fx_opened_res
            item.total_fx_opened_res = trn.total_fx_opened_res

            # fixed ----------------------------------------------------
            item.principal_fixed_res = trn.principal_fixed_res
            item.carry_fixed_res = trn.carry_fixed_res
            item.overheads_fixed_res = trn.overheads_fixed_res
            item.total_fixed_res = trn.total_fixed_res

            # fixed / closed ----------------------------------------------------
            item.principal_fixed_closed_res = trn.principal_fixed_closed_res
            item.carry_fixed_closed_res = trn.carry_fixed_closed_res
            item.overheads_fixed_closed_res = trn.overheads_fixed_closed_res
            item.total_fixed_closed_res = trn.total_fixed_closed_res

            # fixed / opened ----------------------------------------------------
            item.principal_fixed_opened_res = trn.principal_fixed_opened_res
            item.carry_fixed_opened_res = trn.carry_fixed_opened_res
            item.overheads_fixed_opened_res = trn.overheads_fixed_opened_res
            item.total_fixed_opened_res = trn.total_fixed_opened_res

        if item.type == ReportItem.TYPE_INSTRUMENT:
            item.acc = acc or trn.acc_pos
            item.str1 = str1 or trn.str1_pos
            item.str2 = str2 or trn.str2_pos
            item.str3 = str3 or trn.str3_pos
            item.instr = instr or trn.instr

            item.pos_size = trn.pos_size * (1.0 - trn.multiplier)
            item.cost_res = trn.principal_res * (1.0 - trn.multiplier)

        elif item.type == ReportItem.TYPE_CURRENCY:
            item.acc = acc or trn.acc_cash
            item.str1 = str1 or trn.str1_cash
            item.str2 = str2 or trn.str2_cash
            item.str3 = str3 or trn.str3_cash
            item.ccy = ccy or trn.trn_ccy

            item.pos_size = val

        elif item.type == ReportItem.TYPE_FX_TRADE:
            item.acc = acc or trn.acc_cash
            item.str1 = str1 or trn.str1_cash
            item.str2 = str2 or trn.str2_cash
            item.str3 = str3 or trn.str3_cash
            item.ccy = ccy
            item.trn_ccy = trn_ccy

        elif item.type == ReportItem.TYPE_CASH_IN_OUT:
            item.acc = acc or trn.acc_cash
            item.str1 = str1 or trn.str1_cash
            item.str2 = str2 or trn.str2_cash
            item.str3 = str3 or trn.str3_cash
            item.ccy = ccy

        elif item.type == ReportItem.TYPE_TRANSACTION_PL:
            # item.principal_res = trn.principal_res
            # item.carry_res = trn.carry_res
            # item.overheads_res = trn.overheads_res
            pass

        elif item.type == ReportItem.TYPE_MISMATCH:
            item.prtfl = item.report.master_user.mismatch_portfolio
            item.acc = item.report.master_user.mismatch_account
            item.str1 = item.report.master_user.strategy1
            item.str2 = item.report.master_user.strategy2
            item.str3 = item.report.master_user.strategy3
            item.instr = trn.link_instr
            item.ccy = trn.stl_ccy
            item.mismatch_prtfl = trn.prtfl
            item.mismatch_acc = trn.acc_cash
            item.mismatch = trn.mismatch

        # elif item.type in [ReportItem.TYPE_SUMMARY, ReportItem.TYPE_INVESTED_SUMMARY]:
        elif item.type in [ReportItem.TYPE_SUMMARY, ]:
            item.pos_size = float('nan')

        # if trn.is_show_details(acc):
        #     item.detail_trn = trn

        return item

    @classmethod
    def from_item(cls, src):
        item = cls(src.report, src.pricing_provider, src.fx_rate_provider, src.type)

        item.instr = src.instr  # -> Instrument
        item.ccy = src.ccy  # -> Currency
        item.trn_ccy = src.trn_ccy  # -> Currency
        item.prtfl = src.prtfl  # -> Portfolio if use_portfolio
        item.instr = src.instr
        item.acc = src.acc  # -> Account if use_account
        item.str1 = src.str1  # -> Strategy1 if use_strategy1
        item.str2 = src.str2  # -> Strategy2 if use_strategy2
        item.str3 = src.str3  # -> Strategy3 if use_strategy3

        # if item.type in [ReportItem.TYPE_TRANSACTION_PL, ReportItem.TYPE_FX_TRADE]:
        #     item.trn = src.trn
        if src.detail_trn:
            item.trn = src.trn

        item.alloc_bl = src.alloc_bl
        item.alloc_pl = src.alloc_pl

        # item.mismatch_ccy = src.mismatch_ccy
        item.mismatch_prtfl = src.mismatch_prtfl
        item.mismatch_acc = src.mismatch_acc

        # if item.type in [ReportItem.TYPE_SUMMARY, ReportItem.TYPE_INVESTED_SUMMARY]:
        if item.type in [ReportItem.TYPE_SUMMARY]:
            item.pos_size = float('nan')

        return item

    def pricing(self):
        self.report_ccy_cur = self.fx_rate_provider[self.report.report_currency]
        self.report_ccy_cur_fx = self.report_ccy_cur.fx_rate

        try:
            report_ccy_cur_fx = 1.0 / self.report_ccy_cur_fx
        except ZeroDivisionError:
            report_ccy_cur_fx = 0.0

        if self.instr:
            self.instr_price_cur = self.pricing_provider[self.instr]
            self.instr_price_cur_principal_price = self.instr_price_cur.principal_price
            self.instr_price_cur_accrued_price = self.instr_price_cur.accrued_price
            self.instr_pricing_ccy_cur = self.fx_rate_provider[self.instr.pricing_currency]
            self.instr_pricing_ccy_cur_fx = self.instr_pricing_ccy_cur.fx_rate * report_ccy_cur_fx
            self.instr_accrued_ccy_cur = self.fx_rate_provider[self.instr.accrued_currency]
            self.instr_accrued_ccy_cur_fx = self.instr_accrued_ccy_cur.fx_rate * report_ccy_cur_fx

        if self.ccy:
            self.ccy_cur = self.fx_rate_provider[self.ccy]
            self.ccy_cur_fx = self.ccy_cur.fx_rate * report_ccy_cur_fx

    def add(self, o):
        # TODO: in TYPE_INSTRUMENT or global
        # full ----------------------------------------------------
        self.principal_res += o.principal_res
        self.carry_res += o.carry_res
        self.overheads_res += o.overheads_res

        # full / closed ----------------------------------------------------
        self.principal_closed_res += o.principal_closed_res
        self.carry_closed_res += o.carry_closed_res
        self.overheads_closed_res += o.overheads_closed_res

        # full / opened ----------------------------------------------------
        self.principal_opened_res += o.principal_opened_res
        self.carry_opened_res += o.carry_opened_res
        self.overheads_opened_res += o.overheads_opened_res

        # fx ----------------------------------------------------
        self.principal_fx_res += o.principal_fx_res
        self.carry_fx_res += o.carry_fx_res
        self.overheads_fx_res += o.overheads_fx_res

        # fx / closed ----------------------------------------------------
        self.principal_fx_closed_res += o.principal_fx_closed_res
        self.carry_fx_closed_res += o.carry_fx_closed_res
        self.overheads_fx_closed_res += o.overheads_fx_closed_res

        # fx / opened ----------------------------------------------------
        self.principal_fx_opened_res += o.principal_fx_opened_res
        self.carry_fx_opened_res += o.carry_fx_opened_res
        self.overheads_fx_opened_res += o.overheads_fx_opened_res

        # fixed ----------------------------------------------------
        self.principal_fixed_res += o.principal_fixed_res
        self.carry_fixed_res += o.carry_fixed_res
        self.overheads_fixed_res += o.overheads_fixed_res

        # fixed / closed ----------------------------------------------------
        self.principal_fixed_closed_res += o.principal_fixed_closed_res
        self.carry_fixed_closed_res += o.carry_fixed_closed_res
        self.overheads_fixed_closed_res += o.overheads_fixed_closed_res

        # fixed / opened ----------------------------------------------------
        self.principal_fixed_opened_res += o.principal_fixed_opened_res
        self.carry_fixed_opened_res += o.carry_fixed_opened_res
        self.overheads_fixed_opened_res += o.overheads_fixed_opened_res

        # if self.type == ReportItem.TYPE_CURRENCY or self.type == ReportItem.TYPE_INVESTED_CURRENCY:
        if self.type == ReportItem.TYPE_CURRENCY:
            self.pos_size += o.pos_size

            # self.market_value_res += o.pos_size * o.ccy_cur_fx

        elif self.type == ReportItem.TYPE_INSTRUMENT:
            self.pos_size += o.pos_size

            # self.principal_res += o.instr_principal_res
            # self.carry_res += o.instr_accrued_res

            # self.market_value_res += o.instr_principal_res + o.instr_accrued_res
            self.cost_res += o.cost_res

            # self.total_real_res += o.total_real_res
            # self.total_unreal_res += o.market_value_res + o.cost_res
            # self.total_unreal_res += (o.instr_principal_res + o.instr_accrued_res) + o.cost_res

        # elif self.type == ReportItem.TYPE_SUMMARY or self.type == ReportItem.TYPE_INVESTED_SUMMARY:
        elif self.type == ReportItem.TYPE_SUMMARY:
            self.market_value_res += o.market_value_res
            # self.total_real_res += o.total_real_res
            # self.total_unreal_res += o.total_unreal_res

        elif self.type == ReportItem.TYPE_MISMATCH:
            self.mismatch += o.mismatch

    def close(self):
        # if self.type == ReportItem.TYPE_CURRENCY or self.type == ReportItem.TYPE_INVESTED_CURRENCY:
        if self.type == ReportItem.TYPE_CURRENCY:
            self.market_value_res = self.pos_size * self.ccy_cur_fx

        elif self.type == ReportItem.TYPE_INSTRUMENT:
            self.instr_principal_res = self.pos_size * self.instr.price_multiplier * self.instr_price_cur_principal_price * self.instr_pricing_ccy_cur_fx
            self.instr_accrued_res = self.pos_size * self.instr.accrued_multiplier * self.instr_price_cur_accrued_price * self.instr_pricing_ccy_cur_fx
            self.exposure_res = self.instr_principal_res + self.instr_accrued_res

            self.market_value_res = self.instr_principal_res + self.instr_accrued_res

            # self.total_unreal_res = self.market_value_res + self.cost_res

            # full ----------------------------------------------------
            self.principal_res += self.instr_principal_res
            self.carry_res += self.instr_accrued_res

            # full / closed ----------------------------------------------------
            pass

            # full / opened ----------------------------------------------------
            self.principal_opened_res += self.instr_principal_res
            self.carry_opened_res += self.instr_accrued_res

            # fx ----------------------------------------------------
            pass

            # fx / closed ----------------------------------------------------
            pass

            # fx / opened ----------------------------------------------------
            pass

            # fixed ----------------------------------------------------
            self.principal_fixed_res += self.instr_principal_res
            self.carry_fixed_res += self.instr_accrued_res

            # fixed / closed ----------------------------------------------------
            pass

            # fixed / opened ----------------------------------------------------
            self.principal_fixed_opened_res += self.instr_principal_res
            self.carry_fixed_opened_res += self.instr_accrued_res

        elif self.type == ReportItem.TYPE_MISMATCH:
            # self.market_value_res = self.pos_size * self.ccy_cur_fx
            #
            # self.is_empty = isclose(self.pos_size, 0.0)
            pass

        self.total_res = self.principal_res + self.carry_res + self.overheads_res
        self.total_closed_res = self.principal_closed_res + self.carry_closed_res + self.overheads_closed_res
        self.total_opened_res = self.principal_opened_res + self.carry_opened_res + self.overheads_opened_res
        self.total_fx_res = self.principal_fx_res + self.carry_fx_res + self.overheads_fx_res
        self.total_fx_closed_res = self.principal_fx_closed_res + self.carry_fx_closed_res + self.overheads_fx_closed_res
        self.total_fx_opened_res = self.principal_fx_opened_res + self.carry_fx_opened_res + self.overheads_fx_opened_res
        self.total_fixed_res = self.principal_fixed_res + self.carry_fixed_res + self.overheads_fixed_res
        self.total_fixed_closed_res = self.principal_fixed_closed_res + self.carry_fixed_closed_res + self.overheads_fixed_closed_res
        self.total_fixed_opened_res = self.principal_fixed_opened_res + self.carry_fixed_opened_res + self.overheads_fixed_opened_res

        # is_empty

        if self.type == ReportItem.TYPE_CURRENCY:
            self.is_empty = isclose(self.pos_size, 0.0)

        elif self.type == ReportItem.TYPE_INSTRUMENT:
            self.is_empty = isclose(self.pos_size, 0.0) and \
                            isclose(self.total_res, 0.0) and \
                            isclose(self.total_closed_res, 0.0) and \
                            isclose(self.total_opened_res, 0.0)

    # ----------------------------------------------------
    # @staticmethod
    # def group_key(report, item):
    #     return (
    #         item.type,
    #         getattr(item.prtfl, 'id', None),
    #         getattr(item.acc, 'id', None),
    #         getattr(item.str1, 'id', None),
    #         getattr(item.str2, 'id', None),
    #         getattr(item.str3, 'id', None),
    #         getattr(item.alloc_bl, 'id', None),
    #         getattr(item.alloc_pl, 'id', None),
    #         getattr(item.instr, 'id', None),
    #         getattr(item.ccy, 'id', None),
    #         getattr(item.detail_trn, 'id', None),
    #     )
    #
    # @staticmethod
    # def mismatch_group_key(report, item):
    #     return (
    #         item.type,
    #         getattr(item.prtfl, 'id', None),
    #         getattr(item.acc, 'id', None),
    #         getattr(item.instr, 'id', None),
    #         getattr(item.mismatch_prtfl, 'id', None),
    #         getattr(item.mismatch_acc, 'id', None),
    #         getattr(item.mismatch_ccy, 'id', None),
    #     )

    # ----------------------------------------------------

    @property
    def type_name(self):
        for i, n in ReportItem.TYPE_CHOICES:
            if i == self.type:
                return n
        return 'ERR'

    @property
    def type_code(self):
        if self.type == ReportItem.TYPE_UNKNOWN:
            return 'UNKNOWN'

        elif self.type == ReportItem.TYPE_INSTRUMENT:
            return 'INSTR'

        elif self.type == ReportItem.TYPE_CURRENCY:
            return 'CCY'

        elif self.type == ReportItem.TYPE_TRANSACTION_PL:
            return 'TRN_PL'

        elif self.type == ReportItem.TYPE_FX_TRADE:
            return 'FX_TRADE'

        elif self.type == ReportItem.TYPE_CASH_IN_OUT:
            return 'CASH_IN_OUT'

        elif self.type == ReportItem.TYPE_MISMATCH:
            return 'MISMATCH'

        elif self.type == ReportItem.TYPE_SUMMARY:
            return 'SUMMARY'

        # elif self.type == ReportItem.TYPE_INVESTED_CURRENCY:
        #     return 'INV_CCY'
        #
        # elif self.type == ReportItem.TYPE_INVESTED_SUMMARY:
        #     return 'INV_SUMMARY'

        return 'ERR'

    @property
    def user_code(self):
        if self.type == ReportItem.TYPE_UNKNOWN:
            return '<UNKNOWN>'

        elif self.type == ReportItem.TYPE_INSTRUMENT:
            return getattr(self.instr, 'user_code', None)

        elif self.type == ReportItem.TYPE_CURRENCY:
            return getattr(self.ccy, 'user_code', None)

        elif self.type == ReportItem.TYPE_TRANSACTION_PL:
            return 'TRANSACTION_PL'

        elif self.type == ReportItem.TYPE_FX_TRADE:
            # return 'FX_TRADE'
            return '%s/%s' % (getattr(self.trn_ccy, 'user_code', None), getattr(self.ccy, 'user_code', None),)

        elif self.type == ReportItem.TYPE_CASH_IN_OUT:
            # return 'CASH_IN_OUT'
            return getattr(self.ccy, 'user_code', None)

        elif self.type == ReportItem.TYPE_MISMATCH:
            return getattr(self.ccy, 'user_code', None)

        elif self.type == ReportItem.TYPE_SUMMARY:
            return 'SUMMARY'

        # elif self.type == ReportItem.TYPE_INVESTED_CURRENCY:
        #     return getattr(self.ccy, 'user_code', None)
        #
        # elif self.type == ReportItem.TYPE_INVESTED_SUMMARY:
        #     return 'INVESTED_SUMMARY'

        return '<ERROR>'

    @property
    def short_name(self):
        if self.type == ReportItem.TYPE_UNKNOWN:
            return '<UNKNOWN>'

        elif self.type == ReportItem.TYPE_INSTRUMENT:
            return getattr(self.instr, 'short_name', None)

        elif self.type == ReportItem.TYPE_CURRENCY:
            return getattr(self.ccy, 'short_name', None)

        elif self.type == ReportItem.TYPE_TRANSACTION_PL:
            return ugettext('Transaction PL')

        elif self.type == ReportItem.TYPE_FX_TRADE:
            # return ugettext('FX-Trade')
            return ugettext('FX-Trades: %s/%s') % (getattr(self.trn_ccy, 'short_name', None),
                                                   getattr(self.ccy, 'short_name', None),)

        elif self.type == ReportItem.TYPE_CASH_IN_OUT:
            # return ugettext('Cash In/Out: %s/%s')
            return ugettext('Cash In/Out: %s') % getattr(self.ccy, 'short_name', None)

        elif self.type == ReportItem.TYPE_MISMATCH:
            return getattr(self.instr, 'short_name', None)

        elif self.type == ReportItem.TYPE_SUMMARY:
            return ugettext('Summary')

        # elif self.type == ReportItem.TYPE_INVESTED_CURRENCY:
        #     return getattr(self.ccy, 'name', None)
        #
        # elif self.type == ReportItem.TYPE_INVESTED_SUMMARY:
        #     return ugettext('Invested summary')

        return '<ERROR>'

    @property
    def name(self):
        if self.type == ReportItem.TYPE_UNKNOWN:
            return '<UNKNOWN>'

        elif self.type == ReportItem.TYPE_INSTRUMENT:
            return getattr(self.instr, 'name', None)

        elif self.type == ReportItem.TYPE_CURRENCY:
            return getattr(self.ccy, 'name', None)

        elif self.type == ReportItem.TYPE_TRANSACTION_PL:
            return ugettext('Transaction PL')

        elif self.type == ReportItem.TYPE_FX_TRADE:
            # return ugettext('FX-Trade')
            return ugettext('FX-Trades: %s/%s') % (
                getattr(self.trn_ccy, 'name', None), getattr(self.ccy, 'name', None),)

        elif self.type == ReportItem.TYPE_CASH_IN_OUT:
            # return ugettext('Cash In/Out: %s/%s')
            return ugettext('Cash In/Out: %s') % getattr(self.ccy, 'name', None)

        elif self.type == ReportItem.TYPE_MISMATCH:
            return getattr(self.instr, 'name', None)

        elif self.type == ReportItem.TYPE_SUMMARY:
            return ugettext('Summary')

        # elif self.type == ReportItem.TYPE_INVESTED_CURRENCY:
        #     return getattr(self.ccy, 'name', None)
        #
        # elif self.type == ReportItem.TYPE_INVESTED_SUMMARY:
        #     return ugettext('Invested summary')

        return '<ERROR>'

    # @property
    # def detail(self):
    #     from poms.reports.serializers import ReportItemSerializer
    #     my_data = formula.get_model_data(self, ReportItemSerializer, context=self.context)
    #
    #     try:
    #         return formula.safe_eval('item.instr', names={'item': self})
    #     except formula.InvalidExpression:
    #         return 'OLALALALALALA'
    #
    #     if self.detail_trn:
    #         expr = self.acc.type.transaction_details_expr
    #         if expr:
    #             try:
    #                 value = formula.safe_eval(expr, names={'item': self})
    #             except formula.InvalidExpression:
    #                 value = ugettext('Invalid expression')
    #             return value
    #     return None

    @property
    def trn_cls(self):
        return getattr(self.trn, 'trn_cls', None)

    @property
    def detail_trn(self):
        if self.trn and self.acc and self.trn.is_show_details(self.acc):
            return self.trn
        return None

    def eval_custom_fields(self):
        from poms.reports.serializers import ReportItemSerializer
        res = []
        for cf in self.report.custom_fields:
            if cf.expr and self.report.member:
                try:
                    names = formula.get_model_data(self, ReportItemSerializer, context={'member': self.report.member,})
                    value = formula.safe_eval(cf.expr, names=names)
                except formula.InvalidExpression:
                    value = ugettext('Invalid expression')
            else:
                value = None
            res.append({
                'custom_field': cf,
                'value': value
            })
        self.custom_fields = res


class Report(object):
    MODE_IGNORE = 0
    MODE_INDEPENDENT = 1
    MODE_INTERDEPENDENT = 2
    MODE_CHOICES = (
        (MODE_IGNORE, 'Ignore'),
        (MODE_INDEPENDENT, 'Independent'),
        (MODE_INTERDEPENDENT, 'Offsetting (Interdependent - 0/100, 100/0, 50/50)'),
    )

    def __init__(self,
                 id=None,
                 master_user=None,
                 member=None,
                 task_id=None,
                 task_status=None,
                 report_date=None,
                 report_currency=None,
                 pricing_policy=None,
                 cost_method=None,
                 portfolio_mode=MODE_INDEPENDENT,
                 account_mode=MODE_INDEPENDENT,
                 strategy1_mode=MODE_INDEPENDENT,
                 strategy2_mode=MODE_INDEPENDENT,
                 strategy3_mode=MODE_INDEPENDENT,
                 show_transaction_details=False,
                 approach_multiplier=0.5,
                 portfolios=None,
                 accounts=None,
                 strategies1=None,
                 strategies2=None,
                 strategies3=None,
                 transaction_classes=None,
                 date_field=None,
                 custom_fields=None,
                 items=None):
        self.id = id
        self.task_id = task_id
        self.task_status = task_status

        self.master_user = master_user
        self.member = member
        self.pricing_policy = pricing_policy
        self.report_date = report_date or (date_now() - timedelta(days=1))
        self.report_currency = report_currency or master_user.system_currency
        self.cost_method = cost_method or CostMethod.objects.get(pk=CostMethod.AVCO)

        self.portfolio_mode = portfolio_mode
        self.account_mode = account_mode
        self.strategy1_mode = strategy1_mode
        self.strategy2_mode = strategy2_mode
        self.strategy3_mode = strategy3_mode
        self.show_transaction_details = show_transaction_details
        self.approach_multiplier = approach_multiplier

        self.portfolios = portfolios or []
        self.accounts = accounts or []
        self.strategies1 = strategies1 or []
        self.strategies2 = strategies2 or []
        self.strategies3 = strategies3 or []
        self.transaction_classes = transaction_classes or []
        self.date_field = date_field or 'transaction_date'

        self.custom_fields = custom_fields or []

        self.items = items or []
        self.transactions = []

    def __str__(self):
        return "%s for %s @ %s" % (self.__class__.__name__, self.master_user, self.report_date)

    def close(self):
        for item in self.items:
            item.eval_custom_fields()

    @property
    def approach_begin_multiplier(self):
        return self.approach_multiplier

    @property
    def approach_end_multiplier(self):
        return 1.0 - self.approach_multiplier

    @property
    def system_ccy(self):
        return self.master_user.system_currency

    def is_system_ccy(self, ccy):
        return self.master_user.system_currency_id == ccy.id


class ReportBuilder(object):
    def __init__(self, instance=None, queryset=None, transactions=None):
        self.instance = instance
        self._queryset = queryset
        self._transactions = transactions

        self._items = []

    # @property
    # def _system_currency(self):
    #     return self.instance.master_user.system_currency

    @cached_property
    def _trn_cls_sell(self):
        return TransactionClass.objects.get(pk=TransactionClass.SELL)

    @cached_property
    def _trn_cls_buy(self):
        return TransactionClass.objects.get(pk=TransactionClass.BUY)

    @cached_property
    def _trn_cls_fx_trade(self):
        return TransactionClass.objects.get(pk=TransactionClass.FX_TRADE)

    def _trn_qs(self):
        if self._queryset is None:
            # permissions and attributes refreshed after build report
            queryset = Transaction.objects.prefetch_related(
                'master_user',
                # 'complex_transaction',
                # 'complex_transaction__transaction_type',
                'transaction_class',
                'instrument',
                # 'instrument__instrument_type',
                # 'instrument__instrument_type__instrument_class',
                'transaction_currency',
                'settlement_currency',
                'portfolio',
                'account_cash',
                # 'account_cash__type',
                'account_position',
                # 'account_position__type',
                'account_interim',
                # 'account_interim__type',
                'strategy1_position',
                # 'strategy1_position__subgroup',
                # 'strategy1_position__subgroup__group',
                'strategy1_cash',
                # 'strategy1_cash__subgroup',
                # 'strategy1_cash__subgroup__group',
                'strategy2_position',
                # 'strategy2_position__subgroup',
                # 'strategy2_position__subgroup__group',
                'strategy2_cash',
                # 'strategy2_cash__subgroup',
                # 'strategy2_cash__subgroup__group',
                'strategy3_position',
                # 'strategy3_position__subgroup',
                # 'strategy3_position__subgroup__group',
                'strategy3_cash',
                # 'strategy3_cash__subgroup',
                # 'strategy3_cash__subgroup__group',
                # 'responsible',
                # 'responsible__group',
                # 'counterparty',
                # 'counterparty__group',
                'linked_instrument',
                # 'linked_instrument__instrument_type',
                # 'linked_instrument__instrument_type__instrument_class',
                'allocation_balance',
                # 'allocation_balance__instrument_type',
                # 'allocation_balance__instrument_type__instrument_class',
                'allocation_pl',
                # 'allocation_pl__instrument_type',
                # 'allocation_pl__instrument_type__instrument_class',
            ).prefetch_related(
                #     get_attributes_prefetch_by_path('portfolio__attributes'),
                #     get_attributes_prefetch_by_path('instrument__attributes'),
                #     get_attributes_prefetch_by_path('account_cash__attributes'),
                #     get_attributes_prefetch_by_path('account_position__attributes'),
                #     get_attributes_prefetch_by_path('account_interim__attributes'),
                #     get_attributes_prefetch_by_path('transaction_currency__attributes'),
                #     get_attributes_prefetch_by_path('settlement_currency__attributes'),
                #     *get_permissions_prefetch_lookups(
                #         ('portfolio', Portfolio),
                #         ('instrument', Instrument),
                #         ('instrument__instrument_type', InstrumentType),
                #         ('account_cash', Account),
                #         ('account_cash__type', AccountType),
                #         ('account_position', Account),
                #         ('account_position__type', AccountType),
                #         ('account_interim', Account),
                #         ('account_interim__type', AccountType),
                #         ('strategy1_position', Strategy1),
                #         ('strategy1_position__subgroup', Strategy1Subgroup),
                #         ('strategy1_position__subgroup__group', Strategy1Group),
                #         ('strategy1_cash', Strategy1),
                #         ('strategy1_cash__subgroup', Strategy1Subgroup),
                #         ('strategy1_cash__subgroup__group', Strategy1Group),
                #         ('strategy2_position', Strategy2),
                #         ('strategy2_position__subgroup', Strategy2Subgroup),
                #         ('strategy2_position__subgroup__group', Strategy2Group),
                #         ('strategy2_cash', Strategy2),
                #         ('strategy2_cash__subgroup', Strategy2Subgroup),
                #         ('strategy2_cash__subgroup__group', Strategy2Group),
                #         ('strategy3_position', Strategy3),
                #         ('strategy3_position__subgroup', Strategy3Subgroup),
                #         ('strategy3_position__subgroup__group', Strategy3Group),
                #         ('strategy3_cash', Strategy3),
                #         ('strategy3_cash__subgroup', Strategy3Subgroup),
                #         ('strategy3_cash__subgroup__group', Strategy3Group),
                #         ('responsible', Responsible),
                #         ('responsible__group', ResponsibleGroup),
                #         ('counterparty', Counterparty),
                #         ('counterparty__group', CounterpartyGroup),
                #         ('linked_instrument', Instrument),
                #         ('linked_instrument__instrument_type', InstrumentType),
                #         ('allocation_balance', Instrument),
                #         ('allocation_balance__instrument_type', InstrumentType),
                #         ('allocation_pl', Instrument),
                #         ('allocation_pl__instrument_type', InstrumentType),
                #     )
            )
        else:
            queryset = self._queryset

        queryset = queryset.filter(
            master_user=self.instance.master_user,
            is_deleted=False,
        ).filter(
            Q(complex_transaction__isnull=True) | Q(complex_transaction__status=ComplexTransaction.PRODUCTION,
                                                    complex_transaction__is_deleted=False)
        )

        queryset = queryset.select_related(
            # TODO: add fields!!!
        )

        queryset = queryset.filter(**{'%s__lte' % self.instance.date_field: self.instance.report_date})

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

        queryset = queryset.order_by(self.instance.date_field, 'transaction_code', 'id')

        return queryset

    @cached_property
    def _pricing_provider(self):
        if self.instance.pricing_policy is None:
            return FakeInstrumentPricingProvider(None, None, self.instance.report_date)
        else:
            p = InstrumentPricingProvider(self.instance.master_user, self.instance.pricing_policy,
                                          self.instance.report_date)
            p.fill_using_transactions(self._trn_qs(), lazy=False)
            return p

    @cached_property
    def _fx_rate_provider(self):
        if self.instance.pricing_policy is None:
            return FakeCurrencyFxRateProvider(None, None, self.instance.report_date)
        else:
            p = CurrencyFxRateProvider(self.instance.master_user, self.instance.pricing_policy,
                                       self.instance.report_date)
            p.fill_using_transactions(self._trn_qs(), currencies=[self.instance.report_currency], lazy=False)
            return p

    @cached_property
    def transactions(self):
        if self._transactions:
            return self._transactions

        res = []
        for t in self._trn_qs():
            overrides = {}

            if self.instance.portfolio_mode == Report.MODE_IGNORE:
                overrides['portfolio'] = self.instance.master_user.portfolio

            if self.instance.account_mode == Report.MODE_IGNORE:
                overrides['account_position'] = self.instance.master_user.account
                overrides['account_cash'] = self.instance.master_user.account
                overrides['account_interim'] = self.instance.master_user.account

            if self.instance.strategy1_mode == Report.MODE_IGNORE:
                overrides['strategy1_position'] = self.instance.master_user.strategy1
                overrides['strategy1_cash'] = self.instance.master_user.strategy1

            if self.instance.strategy2_mode == Report.MODE_IGNORE:
                overrides['strategy2_position'] = self.instance.master_user.strategy2
                overrides['strategy2_cash'] = self.instance.master_user.strategy2

            if self.instance.strategy3_mode == Report.MODE_IGNORE:
                overrides['strategy3_position'] = self.instance.master_user.strategy3
                overrides['strategy3_cash'] = self.instance.master_user.strategy3

            trn = VirtualTransaction(
                report=self.instance,
                pricing_provider=self._pricing_provider,
                fx_rate_provider=self._fx_rate_provider,
                trn=t,
                overrides=overrides
            )
            trn.pricing()
            res.append(trn)

        res1 = self._multipliers(res)

        # res21 = []
        # for trn in res1:
        #     trn.calc()
        #     if trn.closed_by:
        #         for closed_by, delta in trn.closed_by:
        #             closed_by2, trn2 = VirtualTransaction.approach_clone(closed_by, trn, delta)
        #             res21.append(trn2)
        #             res21.append(closed_by2)
        # res2 = res1 + res21
        # res3 = self._transfers(res2)

        res2 = []
        for trn in res1:
            res2.append(trn)

            trn.calc()

            if trn.trn_cls.id in [TransactionClass.BUY, TransactionClass.SELL]:
                if trn.closed_by:
                    for closed_by, delta in trn.closed_by:
                        closed_by2, trn2 = VirtualTransaction.approach_clone(closed_by, trn, delta)
                        res2.append(trn2)
                        res2.append(closed_by2)

            elif trn.trn_cls.id == TransactionClass.FX_TRADE:
                trn.is_hidden = True

                trn1, trn2 = trn.fx_trade_clone()
                res2.append(trn1)
                res2.append(trn2)

            elif trn.trn_cls.id == TransactionClass.TRANSFER:
                trn.is_hidden = True
                # split TRANSFER to sell/buy or buy/sell
                if trn.pos_size >= 0:
                    trn1, trn2 = trn.transfer_clone(self._trn_cls_sell, self._trn_cls_buy)
                else:
                    trn1, trn2 = trn.transfer_clone(self._trn_cls_buy, self._trn_cls_sell)
                res2.append(trn1)
                res2.append(trn2)

            elif trn.trn_cls.id == TransactionClass.FX_TRANSFER:
                trn.is_hidden = True

                trn1, trn2 = trn.transfer_clone(self._trn_cls_fx_trade, self._trn_cls_fx_trade)
                res2.append(trn1)
                res2.append(trn2)

        return res2

    def _multipliers(self, src):
        rolling_positions = Counter()
        items = defaultdict(list)

        res = []

        # multipliers_delta = []

        # closed, closed_by, delta
        # changes = []

        def _set_mul(t0, multiplier):
            # if isclose(t.r_multiplier, multiplier):
            #     return
            delta = multiplier - t0.multiplier
            # multipliers_delta.append((t0, delta))
            t0.multiplier = multiplier
            return delta

        def _close_by(closed, cur, delta):
            # changes.append((closed, cur, delta))
            closed.closed_by.append((cur, delta))
            # cur2, closed2 = VirtualTransaction.approach_clone(cur, closed, delta)
            # res.append(cur2)
            # res.append(closed2)

        for t in src:
            res.append(t)

            if t.trn_cls.id not in [TransactionClass.BUY, TransactionClass.SELL]:
                continue

            t_key = (
                getattr(t.prtfl, 'id', None) if self.instance.portfolio_mode == Report.MODE_INDEPENDENT else None,
                getattr(t.acc_pos, 'id', None) if self.instance.account_mode == Report.MODE_INDEPENDENT else None,
                getattr(t.str1_pos, 'id', None) if self.instance.strategy1_mode == Report.MODE_INDEPENDENT else None,
                getattr(t.str2_pos, 'id', None) if self.instance.strategy2_mode == Report.MODE_INDEPENDENT else None,
                getattr(t.str3_pos, 'id', None) if self.instance.strategy3_mode == Report.MODE_INDEPENDENT else None,
                getattr(t.instr, 'id', None),
            )

            # multipliers_delta.clear()
            t.multiplier = 0.0
            t.closed_by = []
            rolling_position = rolling_positions[t_key]

            if isclose(rolling_position, 0.0):
                k = -1
            else:
                k = - t.pos_size / rolling_position

            if self.instance.cost_method.id == CostMethod.AVCO:

                if k > 1.0:
                    if t_key in items:
                        for t0 in items[t_key]:
                            delta = _set_mul(t0, 1.0)
                            _close_by(t0, t, delta)
                        del items[t_key]
                    items[t_key].append(t)
                    _set_mul(t, 1.0 / k)
                    rolling_position = t.pos_size * (1.0 - t.multiplier)

                elif isclose(k, 1.0):
                    if t_key in items:
                        for t0 in items[t_key]:
                            delta = _set_mul(t0, 1.0)
                            _close_by(t0, t, delta)
                        del items[t_key]
                    _set_mul(t, 1.0)
                    rolling_position = 0.0

                elif k > 0.0:
                    if t_key in items:
                        for t0 in items[t_key]:
                            delta = _set_mul(t0, t0.multiplier + k * (1.0 - t0.multiplier))
                            _close_by(t0, t, delta)
                    _set_mul(t, 1.0)
                    rolling_position += t.pos_size

                else:
                    items[t_key].append(t)
                    rolling_position += t.pos_size

            elif self.instance.cost_method.id == CostMethod.FIFO:

                if k > 1.0:
                    if t_key in items:
                        for t0 in items[t_key]:
                            delta = _set_mul(t0, 1.0)
                            _close_by(t0, t, delta)
                        items[t_key].clear()
                    items[t_key].append(t)
                    _set_mul(t, 1.0 / k)
                    rolling_position = t.pos_size * (1.0 - t.multiplier)

                elif isclose(k, 1.0):
                    if t_key in items:
                        for t0 in items[t_key]:
                            delta = _set_mul(t0, 1.0)
                            _close_by(t0, t, delta)
                        del items[t_key]
                    _set_mul(t, 1.0)
                    rolling_position = 0.0

                elif k > 0.0:
                    position = t.pos_size
                    if t_key in items:
                        t_items = items[t_key]
                        for t0 in t_items:
                            remaining = t0.pos_size * (1.0 - t0.multiplier)
                            k0 = - position / remaining
                            if k0 > 1.0:
                                delta = _set_mul(t0, 1.0)
                                _close_by(t0, t, delta)
                                position += remaining
                            elif isclose(k0, 1.0):
                                delta = _set_mul(t0, 1.0)
                                _close_by(t0, t, delta)
                                position += remaining
                            elif k0 > 0.0:
                                position += remaining * k0
                                delta = _set_mul(t0, t0.multiplier + k0 * (1.0 - t0.multiplier))
                                _close_by(t0, t, delta)
                            # else:
                            #     break
                            if isclose(position, 0.0):
                                break
                        t_items = [t0 for t0 in t_items if not isclose(t0.multiplier, 1.0)]
                        if t_items:
                            items[t_key] = t_items
                        else:
                            del items[t_key]

                    _set_mul(t, abs((t.pos_size - position) / t.pos_size))
                    rolling_position += t.pos_size * t.multiplier

                else:
                    items[t_key].append(t)
                    rolling_position += t.pos_size

            rolling_positions[t_key] = rolling_position
            # print('i =', i, ', rolling_positions =', rolling_position)

            # if multipliers_delta:
            #     init_mult = 1.0 - self.instance.pl_real_unreal_end_multiplier
            #     end_mult = self.instance.pl_real_unreal_end_multiplier
            #
            #     t, inc_multiplier = multipliers_delta[-1]
            #
            #     # sum_principal = 0.0
            #     # sum_carry = 0.0
            #     # sum_overheads = 0.0
            #     sum_total = 0.0
            #     for t0, inc_multiplier0 in multipliers_delta:
            #         # sum_principal += t0.principal_with_sign * inc_multiplier0
            #         # sum_carry += t0.carry_with_sign * inc_multiplier0
            #         # sum_overheads += t0.overheads_with_sign * inc_multiplier0
            #         sum_total += inc_multiplier0 * t0.total_sys
            #
            #     for t0, inc_multiplier0 in multipliers_delta:
            #         mult = end_mult if t0.pk == t.pk else init_mult
            #
            #         matched = abs((t0.pos_size * inc_multiplier0) / (
            #             t.pos_size * inc_multiplier))
            #         # adj = matched * mult
            #
            #         # t0.real_pl_principal_with_sign += sum_principal * matched * mult
            #         # t0.real_pl_carry_with_sign += sum_carry * matched * mult
            #         # t0.real_pl_overheads_with_sign += sum_overheads * matched * mult
            #         t0.total_real_sys += sum_total * matched * mult
            pass

        # for t in transactions:
        #     if t.trn_cls.id not in [TransactionClass.BUY, TransactionClass.SELL]:
        #         continue
        #     # t.r_position_size = t.pos_size * (1.0 - t.multiplier)
        #     # t.r_cost = t.principal_ * (1.0 - t.multiplier)
        #     pass
        return res

    # def _transfers(self, src):
    #     res = []
    #
    #     for t in src:
    #         res.append(t)
    #
    #         if t.trn_cls.id == TransactionClass.FX_TRADE:
    #             t.is_hidden = True
    #
    #             t1, t2 = t.fx_trade_clone()
    #             res.append(t1)
    #             res.append(t2)
    #
    #         elif t.trn_cls.id == TransactionClass.TRANSFER:
    #             t.is_hidden = True
    #             # split TRANSFER to sell/buy or buy/sell
    #
    #             if t.pos_size >= 0:
    #                 t1, t2 = t.transfer_clone(self._trn_cls_sell, self._trn_cls_buy)
    #                 res.append(t1)
    #                 res.append(t2)
    #
    #             else:
    #                 t1, t2 = t.transfer_clone(self._trn_cls_buy, self._trn_cls_sell)
    #                 res.append(t1)
    #                 res.append(t2)
    #
    #         elif t.trn_cls.id == TransactionClass.FX_TRANSFER:
    #             t.is_hidden = True
    #
    #             t1, t2 = t.transfer_clone(self._trn_cls_fx_trade, self._trn_cls_fx_trade)
    #             res.append(t1)
    #             res.append(t2)
    #
    #     return res

    def build(self, full=True):
        mismatch_items = []

        # split transactions to atomic items using transaction class, case and something else

        for trn in self.transactions:
            if trn.is_mismatch and trn.link_instr and not isclose(trn.mismatch, 0.0):
                item = ReportItem.from_trn(self.instance, self._pricing_provider, self._fx_rate_provider,
                                           ReportItem.TYPE_MISMATCH, trn)
                mismatch_items.append(item)

            if trn.is_hidden:
                continue

            if trn.trn_cls.id in [TransactionClass.BUY, TransactionClass.SELL]:
                self._add_instr(trn)
                self._add_cash(trn, val=trn.cash, ccy=trn.stl_ccy)

            elif trn.trn_cls.id in [TransactionClass.CASH_INFLOW, TransactionClass.CASH_OUTFLOW]:
                self._add_cash(trn, val=trn.cash, ccy=trn.stl_ccy,
                               acc=trn.acc_pos, str1=trn.str1_pos, str2=trn.str2_pos,
                               str3=trn.str3_pos)

                # P&L
                item = ReportItem.from_trn(self.instance, self._pricing_provider, self._fx_rate_provider,
                                           ReportItem.TYPE_CASH_IN_OUT, trn, acc=trn.acc_cash,
                                           str1=trn.str1_cash, str2=trn.str2_cash, str3=trn.str3_cash,
                                           ccy=trn.stl_ccy)
                self._items.append(item)

            elif trn.trn_cls.id == TransactionClass.INSTRUMENT_PL:
                self._add_instr(trn)
                self._add_cash(trn, val=trn.cash, ccy=trn.stl_ccy)

            elif trn.trn_cls.id == TransactionClass.TRANSACTION_PL:
                self._add_cash(trn, val=trn.cash, ccy=trn.stl_ccy)

                item = ReportItem.from_trn(self.instance, self._pricing_provider, self._fx_rate_provider,
                                           ReportItem.TYPE_TRANSACTION_PL, trn, acc=trn.acc_pos,
                                           str1=trn.str1_pos, str2=trn.str2_pos, str3=trn.str3_pos)
                self._items.append(item)

            elif trn.trn_cls.id == TransactionClass.FX_TRADE:
                # TODO: Что используем для strategy?
                self._add_cash(trn, val=trn.principal, ccy=trn.stl_ccy)

                # self._add_cash(trn, val=trn.cash, ccy=trn.stl_ccy)

                # P&L
                item = ReportItem.from_trn(self.instance, self._pricing_provider, self._fx_rate_provider,
                                           ReportItem.TYPE_FX_TRADE, trn, acc=trn.acc_cash,
                                           str1=trn.str1_cash, str2=trn.str2_cash, str3=trn.str3_cash,
                                           ccy=trn.trn.settlement_currency, trn_ccy=trn.trn_ccy)
                self._items.append(item)

            elif trn.trn_cls.id == TransactionClass.TRANSFER:
                # raise RuntimeError('Virtual transaction must be created')
                pass

            elif trn.trn_cls.id == TransactionClass.FX_TRANSFER:
                # raise RuntimeError('Virtual transaction must be created')
                pass

            else:
                raise RuntimeError('Invalid transaction class: %s' % trn.trn_cls.id)

        def _group_key(item):
            return (
                item.type,
                getattr(item.prtfl, 'id', -1),
                getattr(item.acc, 'id', -1),
                getattr(item.str1, 'id', -1),
                getattr(item.str2, 'id', -1),
                getattr(item.str3, 'id', -1),
                getattr(item.alloc_bl, 'id', -1),
                getattr(item.alloc_pl, 'id', -1),
                getattr(item.instr, 'id', -1),
                getattr(item.ccy, 'id', -1),
                getattr(item.trn_ccy, 'id', -1),
                getattr(item.detail_trn, 'id', -1),
            )

        _items = sorted(self._items, key=_group_key)

        # aggregate items

        # invested_items = []
        res_items = []
        for k, g in groupby(_items, key=_group_key):
            res_item = None
            # invested_item = None

            for item in g:
                if item.type in [ReportItem.TYPE_INSTRUMENT, ReportItem.TYPE_CURRENCY, ReportItem.TYPE_TRANSACTION_PL,
                                 ReportItem.TYPE_FX_TRADE, ReportItem.TYPE_CASH_IN_OUT, ]:
                    if res_item is None:
                        res_item = ReportItem.from_item(item)
                    res_item.add(item)

                    # if item.trn and item.type in [ReportItem.TYPE_CURRENCY] and \
                    #                 item.trn.trn_cls.id in [TransactionClass.CASH_INFLOW, TransactionClass.CASH_OUTFLOW]:
                    #     if invested_item is None:
                    #         invested_item = ReportItem.from_item(item)
                    #         invested_item.type = ReportItem.TYPE_CURRENCY
                    #     invested_item.add(item)

            if res_item:
                res_item.pricing()
                res_item.close()
                res_items.append(res_item)

            # if invested_item:
            #     invested_item.pricing()
            #     invested_item.close()
            #     invested_items.append(invested_item)
            pass

        # ReportItem.dumps(_items)

        # res_items = [item for item in res_items if not item.is_empty]

        # aggregate summary
        summaries = []
        if settings.DEBUG:
            summary = ReportItem(self.instance, self._pricing_provider, self._fx_rate_provider, ReportItem.TYPE_SUMMARY)
            for item in res_items:
                if item.type in [ReportItem.TYPE_INSTRUMENT, ReportItem.TYPE_CURRENCY, ReportItem.TYPE_TRANSACTION_PL,
                                 ReportItem.TYPE_FX_TRADE, ReportItem.TYPE_CASH_IN_OUT]:
                    summary.add(item)
            summary.close()
            summaries.append(summary)

        # mismatches

        def _mismatch_group_key(item):
            return (
                item.type,
                getattr(item.prtfl, 'id', -1),
                getattr(item.acc, 'id', -1),
                getattr(item.instr, 'id', -1),
                getattr(item.ccy, 'id', -1),
                getattr(item.mismatch_prtfl, 'id', -1),
                getattr(item.mismatch_acc, 'id', -1),
            )

        mismatch_items0 = sorted(mismatch_items, key=_mismatch_group_key)
        mismatch_items = []
        for k, g in groupby(mismatch_items0, key=_mismatch_group_key):
            mismatch_item = None
            for item in g:
                if mismatch_item is None:
                    mismatch_item = ReportItem.from_item(item)
                mismatch_item.add(item)

            if mismatch_item:
                mismatch_item.pricing()
                mismatch_item.close()
                mismatch_items.append(mismatch_item)

        # aggregate invested summary (primary for validation only)
        # invested_summary = ReportItem(self.instance, self._pricing_provider, self._fx_rate_provider,
        #                               ReportItem.TYPE_INVESTED_SUMMARY)
        # for item in invested_items:
        #     if item.type in [ReportItem.TYPE_INVESTED_CURRENCY]:
        #         invested_summary.add(item)
        # invested_summary.close()

        # self.instance.items = res_items + mismatch_items + [summary, ] + invested_items + [invested_summary, ]
        self.instance.items = res_items + mismatch_items + summaries

        if full:
            self._refresh_with_perms()

        self.instance.close()

        # print('0' * 100)
        # VirtualTransaction.dumps(self.transactions)
        # print('1' * 100)
        # ReportItem.dumps(self._items)
        # print('2' * 100)
        # ReportItem.dumps(self.instance.items)
        # print('3' * 100)

        return self.instance

    def _add_instr(self, trn):
        if trn.case == 0:
            item = ReportItem.from_trn(self.instance, self._pricing_provider, self._fx_rate_provider,
                                       ReportItem.TYPE_INSTRUMENT, trn)
            self._items.append(item)

        elif trn.case == 1:
            item = ReportItem.from_trn(self.instance, self._pricing_provider, self._fx_rate_provider,
                                       ReportItem.TYPE_INSTRUMENT, trn)
            self._items.append(item)

        elif trn.case == 2:
            pass

        else:
            raise RuntimeError('Invalid transaction case: %s' % trn.case)

    def _add_cash(self, trn, val, ccy, acc=None, acc_interim=None, str1=None, str2=None, str3=None):
        if trn.case == 0:
            item = ReportItem.from_trn(self.instance, self._pricing_provider, self._fx_rate_provider,
                                       ReportItem.TYPE_CURRENCY, trn, ccy=ccy, acc=acc,
                                       str1=str1, str2=str2, str3=str3,
                                       val=val)
            self._items.append(item)

        elif trn.case == 1:
            item = ReportItem.from_trn(self.instance, self._pricing_provider, self._fx_rate_provider,
                                       ReportItem.TYPE_CURRENCY, trn, ccy=ccy, acc=acc_interim or trn.acc_interim,
                                       str1=str1, str2=str2, str3=str3,
                                       val=val)
            self._items.append(item)

        elif trn.case == 2:
            item = ReportItem.from_trn(self.instance, self._pricing_provider, self._fx_rate_provider,
                                       ReportItem.TYPE_CURRENCY, trn, ccy=ccy, acc=acc,
                                       str1=str1, str2=str2, str3=str3,
                                       val=val)
            self._items.append(item)

            item = ReportItem.from_trn(self.instance, self._pricing_provider, self._fx_rate_provider,
                                       ReportItem.TYPE_CURRENCY, trn, ccy=ccy, acc=acc_interim or trn.acc_interim,
                                       str1=str1, str2=str2, str3=str3,
                                       val=-val)
            self._items.append(item)

        else:
            raise RuntimeError('Invalid transaction case: %s' % trn.case)

    def _refresh_with_perms(self):
        instrs = set()
        ccys = set()
        prtfls = set()
        accs = set()
        strs1 = set()
        strs2 = set()
        strs3 = set()

        for i in self.instance.items:
            if i.instr:
                instrs.add(i.instr.id)
            if i.ccy:
                ccys.add(i.ccy.id)
            if i.trn_ccy:
                ccys.add(i.trn_ccy.id)
            if i.prtfl:
                prtfls.add(i.prtfl.id)
            if i.acc:
                accs.add(i.acc.id)
            if i.str1:
                strs1.add(i.str1.id)
            if i.str2:
                strs2.add(i.str2.id)
            if i.str3:
                strs3.add(i.str3.id)

            if i.mismatch_prtfl:
                prtfls.add(i.mismatch_prtfl.id)
            if i.mismatch_acc:
                accs.add(i.mismatch_acc.id)

            if i.alloc_bl:
                instrs.add(i.alloc_bl.id)
            if i.alloc_pl:
                instrs.add(i.alloc_pl.id)

        instrs = Instrument.objects.filter(master_user=self.instance.master_user).prefetch_related(
            'master_user', 'instrument_type', 'instrument_type__instrument_class',
            'pricing_currency', 'accrued_currency', 'payment_size_detail', 'daily_pricing_model',
            'price_download_scheme', 'price_download_scheme__provider',
            get_attributes_prefetch(),
            get_tag_prefetch(),
            *get_permissions_prefetch_lookups(
                (None, Instrument),
                ('instrument_type', InstrumentType),
            )
        ).in_bulk(instrs)
        ccys = Currency.objects.filter(master_user=self.instance.master_user).prefetch_related(
            'master_user', 'daily_pricing_model', 'price_download_scheme', 'price_download_scheme__provider',
            get_attributes_prefetch(),
            get_tag_prefetch()
        ).in_bulk(ccys)
        prtfls = Portfolio.objects.filter(master_user=self.instance.master_user).prefetch_related(
            'master_user',
            get_attributes_prefetch(),
            get_tag_prefetch(),
            *get_permissions_prefetch_lookups(
                (None, Portfolio),
            )
        ).in_bulk(prtfls)
        accs = Account.objects.filter(master_user=self.instance.master_user).prefetch_related(
            'master_user', 'type',
            get_attributes_prefetch(),
            get_tag_prefetch(),
            *get_permissions_prefetch_lookups(
                (None, Account),
                ('type', AccountType),
            )
        ).in_bulk(accs)
        strs1 = Strategy1.objects.filter(master_user=self.instance.master_user).prefetch_related(
            'master_user', 'subgroup', 'subgroup__group',
            get_tag_prefetch(),
            *get_permissions_prefetch_lookups(
                (None, Strategy1),
                ('subgroup', Strategy1Subgroup),
                ('subgroup__group', Strategy1Group),
            )
        ).in_bulk(strs1)
        strs2 = Strategy2.objects.filter(master_user=self.instance.master_user).prefetch_related(
            'master_user', 'subgroup', 'subgroup__group',
            get_tag_prefetch(),
            *get_permissions_prefetch_lookups(
                (None, Strategy2),
                ('subgroup', Strategy2Subgroup),
                ('subgroup__group', Strategy2Group),
            )
        ).in_bulk(strs2)
        strs3 = Strategy3.objects.filter(master_user=self.instance.master_user).prefetch_related(
            'master_user', 'subgroup', 'subgroup__group',
            get_tag_prefetch(),
            *get_permissions_prefetch_lookups(
                (None, Strategy3),
                ('subgroup', Strategy3Subgroup),
                ('subgroup__group', Strategy3Group),
            )
        ).in_bulk(strs3)

        for i in self.instance.items:
            if i.instr:
                i.instr = instrs[i.instr.id]
            if i.ccy:
                i.ccy = ccys[i.ccy.id]
            if i.trn_ccy:
                i.trn_ccy = ccys[i.trn_ccy.id]
            if i.prtfl:
                i.prtfl = prtfls[i.prtfl.id]
            if i.acc:
                i.acc = accs[i.acc.id]
            if i.str1:
                i.str1 = strs1[i.str1.id]
            if i.str2:
                i.str2 = strs2[i.str2.id]
            if i.str3:
                i.str3 = strs3[i.str3.id]

            if i.mismatch_prtfl:
                i.mismatch_prtfl = prtfls[i.mismatch_prtfl.id]
            if i.mismatch_acc:
                i.mismatch_acc = accs[i.mismatch_acc.id]

            if i.alloc_bl:
                i.alloc_bl = instrs[i.alloc_bl.id]
            if i.alloc_pl:
                i.alloc_pl = instrs[i.alloc_pl.id]
