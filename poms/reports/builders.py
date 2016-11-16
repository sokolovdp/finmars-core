# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division

import copy
import logging
from collections import Counter, defaultdict
from datetime import timedelta
from functools import partial
from itertools import groupby

from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import ugettext

from poms.common import formula
from poms.common.utils import isclose, date_now
from poms.instruments.models import CostMethod
from poms.reports.pricing import CurrencyFxRateProvider, InstrumentPricingProvider, FakeInstrumentPricingProvider, \
    FakeCurrencyFxRateProvider
from poms.transactions.models import Transaction, TransactionClass

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

    def __getattr__(self, item):
        if item.endswith('_rep'):
            # automatic make value in report ccy
            item_sys = '%s_sys' % item[:-4]
            if hasattr(self, item_sys):
                val = getattr(self, item_sys)
                if self.report_ccy_is_sys:
                    return val
                else:
                    fx = self.report_ccy_rep_fx
                    if isclose(fx, 0.0):
                        return 0.0
                    return val / fx
        raise AttributeError(item)

    def dump_values(self):
        row = []
        for f in self.dump_columns:
            row.append(getattr(self, f))
        return row

    @classmethod
    def dumps(cls, items):
        import pandas

        data = []
        for item in items:
            data.append(item.dump_values())

        print(pandas.DataFrame(data=data, columns=cls.dump_columns))


class VirtualTransaction(_Base):
    trn = None
    pk = None
    trn_code = None
    trn_cls = None
    # case = 0
    multiplier = 0.0

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

    total_real_sys = 0.0
    total_unreal_sys = 0.0

    dump_columns = [
        'pk',
        'trn_cls',
        # 'case',
        'multiplier',
        # 'acc_date',
        # 'cash_date',
        'instr',
        # 'trn_ccy',
        'pos_size',
        'stl_ccy',
        'cash',
        'principal',
        'carry',
        'overheads',
        'total',
        # 'mismatch',
        # 'ref_fx',
        'prtfl',
        'acc_pos',
        'acc_cash',
        'acc_interim',
        'str1_pos',
        'str1_cash',
        'str2_pos',
        'str2_cash',
        'str3_pos',
        'str3_cash',
        # 'link_instr',
        'alloc_bl',
        'alloc_pl',

        # 'instr_principal_sys',
        # 'instr_accrued_sys',
        #
        # # real / unreal
        #
        # 'total_real_sys',
        # 'total_unreal_sys',

        # full ----------------------------------------------------
        'principal_sys',
        'carry_sys',
        'overheads_sys',
        'total_sys',

        # # full / closed ----------------------------------------------------
        # 'principal_closed_sys',
        # 'carry_closed_sys',
        # 'overheads_closed_sys',
        # 'total_closed_sys',
        #
        # # full / opened ----------------------------------------------------
        # 'principal_opened_sys',
        # 'carry_opened_sys',
        # 'overheads_opened_sys',
        # 'total_opened_sys',
        #
        # # fx ----------------------------------------------------
        #
        # 'principal_fx_sys',
        # 'carry_fx_sys',
        # 'overheads_fx_sys',
        # 'total_fx_sys',
        #
        # # fx / closed ----------------------------------------------------
        # 'principal_fx_closed_sys',
        # 'carry_fx_closed_sys',
        # 'overheads_fx_closed_sys',
        # 'total_fx_closed_sys',
        #
        # # fx / opened ----------------------------------------------------
        # 'principal_fx_opened_sys',
        # 'carry_fx_opened_sys',
        # 'overheads_fx_opened_sys',
        # 'total_fx_opened_sys',
        #
        # # fixed ----------------------------------------------------
        # 'principal_fixed_sys',
        # 'carry_fixed_sys',
        # 'overheads_fixed_sys',
        # 'total_fixed_sys',
        #
        # # fixed / closed ----------------------------------------------------
        # 'principal_fixed_closed_sys',
        # 'carry_fixed_closed_sys',
        # 'overheads_fixed_closed_sys',
        # 'total_fixed_closed_sys',
        #
        # # fixed / opened ----------------------------------------------------
        # 'principal_fixed_opened_sys',
        # 'carry_fixed_opened_sys',
        # 'overheads_fixed_opened_sys',
        # 'total_fixed_opened_sys',
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

    # globals ----------------------------------------------------

    @property
    def case(self):
        if self.acc_date <= self.report.report_date < self.cash_date:
            return 1
        elif self.cash_date <= self.report.report_date < self.acc_date:
            return 2
        else:
            return 0

    def is_show_details(self, acc):
        if self.case in [1, 2] and self.report.show_transaction_details:
            return acc and acc.type and acc.type.show_transaction_details
        return False

    # report ccy ----------------------------------------------------

    @property
    def report_ccy_is_sys(self):
        return self.report.report_currency.is_system

    @property
    def report_ccy_rep(self):
        return self.fx_rate_provider[self.report.report_currency]

    @property
    def report_ccy_rep_fx(self):
        return getattr(self.report_ccy_rep, 'fx_rate', float('nan'))

    # instr ----------------------------------------------------

    @property
    def instr_price_rep(self):
        if self.instr:
            return self.pricing_provider[self.instr]
        return None

    @property
    def instr_pricing_ccy_rep(self):
        if self.instr:
            return self.fx_rate_provider[self.instr.pricing_currency]
        return None

    @property
    def instr_pricing_ccy_rep_fx(self):
        return getattr(self.instr_pricing_ccy_rep, 'fx_rate', float('nan'))

    @property
    def instr_pricing_ccy_hist(self):
        if self.instr:
            return self.fx_rate_provider[self.instr.pricing_currency]
        return None

    @property
    def instr_pricing_ccy_hist_fx(self):
        return getattr(self.instr_pricing_ccy_hist, 'fx_rate', float('nan'))

    @property
    def instr_accrued_ccy_rep(self):
        if self.instr:
            return self.fx_rate_provider[self.instr.accrued_currency]
        return None

    @property
    def instr_accrued_ccy_rep_fx(self):
        return getattr(self.instr_accrued_ccy_rep, 'fx_rate', float('nan'))

    @property
    def instr_accrued_ccy_hist(self):
        if self.instr:
            return self.fx_rate_provider[self.instr.accrued_currency]
        return None

    @property
    def instr_accrued_ccy_hist_fx(self):
        return getattr(self.instr_accrued_ccy_hist, 'fx_rate', float('nan'))

    @property
    def instr_principal(self):
        if self.instr:
            price = self.instr_price_rep
            return self.pos_size * self.instr.price_multiplier * price.principal_price
        return float('nan')

    @property
    def instr_principal_sys(self):
        if self.instr:
            return self.instr_principal * self.instr_pricing_ccy_rep_fx
        return float('nan')

    @property
    def instr_accrued(self):
        if self.instr:
            price = self.instr_price_rep
            return self.pos_size * self.instr.accrued_multiplier * price.accrued_price
        return float('nan')

    @property
    def instr_accrued_sys(self):
        if self.instr:
            return self.instr_accrued * self.instr_pricing_ccy_rep_fx
        return float('nan')

    # trn ccy ----------------------------------------------------

    @property
    def trn_ccy_hist(self):
        if self.trn_ccy:
            return self.fx_rate_provider[self.trn_ccy, self.acc_date]
        return None

    @property
    def trn_ccy_hist_fx(self):
        return getattr(self.trn_ccy_hist, 'fx_rate', float('nan'))

    @property
    def trn_ccy_rep(self):
        if self.trn_ccy:
            return self.fx_rate_provider[self.trn_ccy]
        return None

    @property
    def trn_ccy_rep_fx(self):
        return getattr(self.trn_ccy_rep, 'fx_rate', float('nan'))

    # stl ccy ----------------------------------------------------

    @property
    def stl_ccy_hist(self):
        if self.stl_ccy:
            return self.fx_rate_provider[self.stl_ccy, self.cash_date]
        return None

    @property
    def stl_ccy_hist_fx(self):
        return getattr(self.stl_ccy_hist, 'fx_rate', float('nan'))

    @property
    def stl_ccy_rep(self):
        if self.stl_ccy:
            return self.fx_rate_provider[self.stl_ccy]
        return None

    @property
    def stl_ccy_rep_fx(self):
        return getattr(self.stl_ccy_rep, 'fx_rate', float('nan'))

    # props ----------------------------------------------------

    @property
    def mismatch(self):
        return self.cash - self.total

    @property
    def pos_size_sys(self):
        if self.trn_ccy:
            return self.pos_size * self.trn_ccy_rep_fx
        return float('nan')

    # Cash related ----------------------------------------------------

    @property
    def cash_sys(self):
        return self.cash * self.stl_ccy_rep_fx

    # full P&L related ----------------------------------------------------

    @property
    def principal_sys(self):
        return self.principal * self.stl_ccy_rep_fx

    @property
    def carry_sys(self):
        return self.carry * self.stl_ccy_rep_fx

    @property
    def overheads_sys(self):
        return self.overheads * self.stl_ccy_rep_fx

    @property
    def total(self):
        return self.principal + self.carry + self.overheads

    @property
    def total_sys(self):
        return self.total * self.stl_ccy_rep_fx

    # cash flow ----------------------------------------------------

    @property
    def cash_flow_real(self):
        return self.total * self.multiplier

    @property
    def cash_flow_unreal(self):
        return self.total * (1.0 - self.multiplier)

    @property
    def cash_flow_real_sys(self):
        return self.total_sys * self.multiplier

    @property
    def cash_flow_unreal_sys(self):
        return self.total_sys * (1.0 - self.multiplier)

    # full / closed ----------------------------------------------------

    @property
    def principal_closed_sys(self):
        return self.principal_sys * self.multiplier

    @property
    def carry_closed_sys(self):
        return self.carry_sys * self.multiplier

    @property
    def overheads_closed_sys(self):
        return self.overheads_sys * self.multiplier

    @property
    def total_closed_sys(self):
        return self.total_sys * self.multiplier

    # full / opened ----------------------------------------------------

    @property
    def principal_opened_sys(self):
        return self.principal_sys * (1.0 - self.multiplier)

    @property
    def carry_opened_sys(self):
        return self.carry_sys * (1.0 - self.multiplier)

    @property
    def overheads_opened_sys(self):
        return self.overheads_sys * (1.0 - self.multiplier)

    @property
    def total_opened_sys(self):
        return self.total_sys * (1.0 - self.multiplier)

    # fx ----------------------------------------------------

    @property
    def principal_fx_sys(self):
        return self.principal * (self.stl_ccy_rep_fx - self.ref_fx * self.stl_ccy_hist_fx)

    @property
    def carry_fx_sys(self):
        return self.carry * (self.stl_ccy_rep_fx - self.ref_fx * self.stl_ccy_hist_fx)

    @property
    def overheads_fx_sys(self):
        return self.overheads * (self.stl_ccy_rep_fx - self.ref_fx * self.stl_ccy_hist_fx)

    @property
    def total_fx_sys(self):
        return self.total * (self.stl_ccy_rep_fx - self.ref_fx * self.stl_ccy_hist_fx)

    # fx / closed ----------------------------------------------------

    @property
    def principal_fx_closed_sys(self):
        return self.principal_fx_sys * self.multiplier

    @property
    def carry_fx_closed_sys(self):
        return self.carry_fx_sys * self.multiplier

    @property
    def overheads_fx_closed_sys(self):
        return self.overheads_fx_sys * self.multiplier

    @property
    def total_fx_closed_sys(self):
        return self.total_fx_sys * self.multiplier

    # fx / opened ----------------------------------------------------

    @property
    def principal_fx_opened_sys(self):
        return self.principal_fx_sys * (1.0 - self.multiplier)

    @property
    def carry_fx_opened_sys(self):
        return self.carry_fx_sys * (1.0 - self.multiplier)

    @property
    def overheads_fx_opened_sys(self):
        return self.overheads_fx_sys * (1.0 - self.multiplier)

    @property
    def total_fx_opened_sys(self):
        return self.total_fx_sys * (1.0 - self.multiplier)

    # fixed ----------------------------------------------------

    @property
    def principal_fixed_sys(self):
        return self.principal * self.ref_fx * self.stl_ccy_hist_fx

    @property
    def carry_fixed_sys(self):
        return self.carry * self.ref_fx * self.stl_ccy_hist_fx

    @property
    def overheads_fixed_sys(self):
        return self.overheads * self.ref_fx * self.stl_ccy_hist_fx

    @property
    def total_fixed_sys(self):
        return self.total * self.ref_fx * self.stl_ccy_hist_fx

    # fixed / closed ----------------------------------------------------

    @property
    def principal_fixed_closed_sys(self):
        return self.principal_fixed_sys * self.multiplier

    @property
    def carry_fixed_closed_sys(self):
        return self.carry_fixed_sys * self.multiplier

    @property
    def overheads_fixed_closed_sys(self):
        return self.overheads_fixed_sys * self.multiplier

    @property
    def total_fixed_closed_sys(self):
        return self.total_fixed_sys * self.multiplier

    # fixed / opened ----------------------------------------------------

    @property
    def principal_fixed_opened_sys(self):
        return self.principal_fixed_sys * (1.0 - self.multiplier)

    @property
    def carry_fixed_opened_sys(self):
        return self.carry_fixed_sys * (1.0 - self.multiplier)

    @property
    def overheads_fixed_opened_sys(self):
        return self.overheads_fixed_sys * (1.0 - self.multiplier)

    @property
    def total_fixed_opened_sys(self):
        return self.total_fixed_sys * (1.0 - self.multiplier)


class ReportItem(_Base):
    TYPE_UNKNOWN = 0
    TYPE_INSTRUMENT = 1
    TYPE_CURRENCY = 2
    TYPE_TRANSACTION_PL = 3
    TYPE_FX_TRADE = 4
    TYPE_MISMATCH = 5  # Linked instrument
    TYPE_SUMMARY = 100
    TYPE_INVESTED_CURRENCY = 200
    TYPE_INVESTED_SUMMARY = 201
    TYPE_CHOICES = (
        (TYPE_UNKNOWN, 'Unknown'),
        (TYPE_INSTRUMENT, 'Instrument'),
        (TYPE_CURRENCY, 'Currency'),
        (TYPE_TRANSACTION_PL, 'Transaction PL'),
        (TYPE_FX_TRADE, 'FX-Trade'),
        (TYPE_MISMATCH, 'Mismatch'),
        (TYPE_SUMMARY, 'Summary'),
        (TYPE_INVESTED_CURRENCY, 'Invested'),
        (TYPE_INVESTED_SUMMARY, 'Invested summary'),
    )

    type = None
    trn = None

    instr = None
    ccy = None
    prtfl = None
    acc = None
    str1 = None
    str2 = None
    str3 = None
    # detail_trn = None
    # custom_fields = []

    mismatch = 0.0
    mismatch_ccy = None
    mismatch_prtfl = None
    mismatch_acc = None

    # balance
    pos_size = 0.0

    market_value_sys = 0.0

    cost_sys = 0.0

    # P&L

    cash_flow_real_sys = 0.0
    cash_flow_unreal_sys = 0.0

    total_real_sys = 0.0
    total_unreal_sys = 0.0

    # full ----------------------------------------------------
    principal_sys = 0.0
    carry_sys = 0.0
    overheads_sys = 0.0
    # total_sys = 0.0

    # full / closed ----------------------------------------------------
    principal_closed_sys = 0.0
    carry_closed_sys = 0.0
    overheads_closed_sys = 0.0
    # total_closed_sys = 0.0

    # full / opened ----------------------------------------------------
    principal_opened_sys = 0.0
    carry_opened_sys = 0.0
    overheads_opened_sys = 0.0
    # total_opened_sys = 0.0

    # fx ----------------------------------------------------
    principal_fx_sys = 0.0
    carry_fx_sys = 0.0
    overheads_fx_sys = 0.0
    # total_fx_sys = 0.0

    # fx / closed ----------------------------------------------------
    principal_fx_closed_sys = 0.0
    carry_fx_closed_sys = 0.0
    overheads_fx_closed_sys = 0.0
    # total_fx_closed_sys = 0.0

    # fx / opened ----------------------------------------------------
    principal_fx_opened_sys = 0.0
    carry_fx_opened_sys = 0.0
    overheads_fx_opened_sys = 0.0
    # total_fx_opened_sys = 0.0

    # fixed ----------------------------------------------------
    principal_fixed_sys = 0.0
    carry_fixed_sys = 0.0
    overheads_fixed_sys = 0.0
    # total_fixed_sys = 0.0

    # fixed / closed ----------------------------------------------------
    principal_fixed_closed_sys = 0.0
    carry_fixed_closed_sys = 0.0
    overheads_fixed_closed_sys = 0.0
    # total_fixed_closed_sys = 0.0

    # fixed / opened ----------------------------------------------------
    principal_fixed_opened_sys = 0.0
    carry_fixed_opened_sys = 0.0
    overheads_fixed_opened_sys = 0.0

    # total_fixed_opened_sys = 0.0

    dump_columns = [
        'type_code',
        'user_code',
        'prtfl',
        'acc',
        'str1',
        'str2',
        'str3',
        # 'detail_trn',
        # 'instr',
        # 'ccy',
        'pos_size',
        'market_value_sys',
        # 'mismatch_ccy',
        # 'mismatch',
        # 'cost_sys',
        # 'total_real_sys',
        # 'total_unreal_sys',
        # 'instr_principal_sys',
        # 'instr_accrued_sys',

        # full ----------------------------------------------------
        'principal_sys',
        'carry_sys',
        'overheads_sys',
        'total_sys',

        # # full / closed ----------------------------------------------------
        # 'principal_closed_sys',
        # 'carry_closed_sys',
        # 'overheads_closed_sys',
        # 'total_closed_sys',
        #
        # # full / opened ----------------------------------------------------
        # 'principal_opened_sys',
        # 'carry_opened_sys',
        # 'overheads_opened_sys',
        # 'total_opened_sys',
        #
        # # fx ----------------------------------------------------
        #
        # 'principal_fx_sys',
        # 'carry_fx_sys',
        # 'overheads_fx_sys',
        # 'total_fx_sys',
        #
        # # fx / closed ----------------------------------------------------
        # 'principal_fx_closed_sys',
        # 'carry_fx_closed_sys',
        # 'overheads_fx_closed_sys',
        # 'total_fx_closed_sys',
        #
        # # fx / opened ----------------------------------------------------
        # 'principal_fx_opened_sys',
        # 'carry_fx_opened_sys',
        # 'overheads_fx_opened_sys',
        # 'total_fx_opened_sys',
        #
        # # fixed ----------------------------------------------------
        # 'principal_fixed_sys',
        # 'carry_fixed_sys',
        # 'overheads_fixed_sys',
        # 'total_fixed_sys',
        #
        # # fixed / closed ----------------------------------------------------
        # 'principal_fixed_closed_sys',
        # 'carry_fixed_closed_sys',
        # 'overheads_fixed_closed_sys',
        # 'total_fixed_closed_sys',
        #
        # # fixed / opened ----------------------------------------------------
        # 'principal_fixed_opened_sys',
        # 'carry_fixed_opened_sys',
        # 'overheads_fixed_opened_sys',
        # 'total_fixed_opened_sys',
    ]

    def __init__(self, report, pricing_provider, fx_rate_provider, type):
        super(ReportItem, self).__init__(report, pricing_provider, fx_rate_provider)
        self.type = type

    @classmethod
    def from_trn(cls, report, pricing_provider, fx_rate_provider, type, trn, instr=None, ccy=None,
                 prtfl=None, acc=None, str1=None, str2=None, str3=None, val=None):
        item = cls(report, pricing_provider, fx_rate_provider, type)
        item.trn = trn

        # item.instr = instr  # -> Instrument
        # item.ccy = ccy  # -> Currency
        item.prtfl = prtfl or trn.prtfl  # -> Portfolio

        if item.type == ReportItem.TYPE_INSTRUMENT:
            item.acc = acc or trn.acc_pos
            item.str1 = str1 or trn.str1_pos
            item.str2 = str2 or trn.str1_pos
            item.str3 = str3 or trn.str1_pos
            item.instr = instr or trn.instr

            item.pos_size = trn.pos_size * (1.0 - trn.multiplier)
            item.cost_sys = trn.principal_sys * (1.0 - trn.multiplier)

            item.cash_flow_real_sys = trn.cash_flow_real_sys
            item.cash_flow_unreal_sys = trn.cash_flow_unreal_sys

            item.total_real_sys = trn.total_real_sys
            item.total_unreal_sys = trn.total_unreal_sys

            # full ----------------------------------------------------
            item.principal_sys = trn.principal_sys
            item.carry_sys = trn.carry_sys
            item.overheads_sys = trn.overheads_sys

            # full / closed ----------------------------------------------------
            item.principal_closed_sys = trn.principal_closed_sys
            item.carry_closed_sys = trn.carry_closed_sys
            item.overheads_closed_sys = trn.overheads_closed_sys

            # full / opened ----------------------------------------------------
            item.principal_opened_sys = trn.principal_opened_sys
            item.carry_opened_sys = trn.carry_opened_sys
            item.overheads_opened_sys = trn.overheads_opened_sys

            # fx ----------------------------------------------------
            item.principal_fx_sys = trn.principal_fx_sys
            item.carry_fx_sys = trn.carry_fx_sys
            item.overheads_fx_sys = trn.overheads_fx_sys

            # fx / closed ----------------------------------------------------
            item.principal_fx_closed_sys = trn.principal_fx_closed_sys
            item.carry_fx_closed_sys = trn.carry_fx_closed_sys
            item.overheads_fx_closed_sys = trn.overheads_fx_closed_sys

            # fx / opened ----------------------------------------------------
            item.principal_fx_opened_sys = trn.principal_fx_opened_sys
            item.carry_fx_opened_sys = trn.carry_fx_opened_sys
            item.overheads_fx_opened_sys = trn.overheads_fx_opened_sys

            # fixed ----------------------------------------------------
            item.principal_fixed_sys = trn.principal_fixed_sys
            item.carry_fixed_sys = trn.carry_fixed_sys
            item.overheads_fixed_sys = trn.overheads_fixed_sys

            # fixed / closed ----------------------------------------------------
            item.principal_fixed_closed_sys = trn.principal_fixed_closed_sys
            item.carry_fixed_closed_sys = trn.carry_fixed_closed_sys
            item.overheads_fixed_closed_sys = trn.overheads_fixed_closed_sys

            # fixed / opened ----------------------------------------------------
            item.principal_fixed_opened_sys = trn.principal_fixed_opened_sys
            item.carry_fixed_opened_sys = trn.carry_fixed_opened_sys
            item.overheads_fixed_opened_sys = trn.overheads_fixed_opened_sys

        elif item.type == ReportItem.TYPE_CURRENCY:
            item.acc = acc or trn.acc_cash
            item.str1 = str1 or trn.str1_cash
            item.str2 = str2 or trn.str1_cash
            item.str3 = str3 or trn.str1_cash
            item.ccy = ccy or trn.trn_ccy

            item.pos_size = val

        elif item.type == ReportItem.TYPE_FX_TRADE:
            # item.principal_sys = trn.pos_size_sys + trn.principal_sys
            item.carry_sys = trn.carry_sys
            item.overheads_sys = trn.overheads_sys

        elif item.type == ReportItem.TYPE_TRANSACTION_PL:
            item.principal_sys = trn.principal_sys
            item.carry_sys = trn.carry_sys
            item.overheads_sys = trn.overheads_sys

        elif item.type == ReportItem.TYPE_MISMATCH:
            item.acc = trn.acc_pos
            item.instr = trn.link_instr
            item.str1 = str1
            item.str2 = str2
            item.str3 = str3
            item.mismatch_ccy = trn.stl_ccy
            item.mismatch = trn.mismatch

        # if trn.is_show_details(acc):
        #     item.detail_trn = trn

        return item

    @classmethod
    def from_item(cls, src):
        item = cls(src.report, src.pricing_provider, src.fx_rate_provider, src.type)

        item.instr = src.instr  # -> Instrument
        item.ccy = src.ccy  # -> Currency
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

        item.mismatch_ccy = src.mismatch_ccy

        return item

    #  ----------------------------------------------------

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

        elif self.type == ReportItem.TYPE_MISMATCH:
            return 'MISMATCH'

        elif self.type == ReportItem.TYPE_SUMMARY:
            return 'SUMMARY'

        elif self.type == ReportItem.TYPE_INVESTED_CURRENCY:
            return '$_CCY'

        elif self.type == ReportItem.TYPE_INVESTED_SUMMARY:
            return '$_SUMMARY'

        return 'ERR'

    @property
    def user_code(self):
        if self.type == ReportItem.TYPE_UNKNOWN:
            return '<UNKNOWN>'

        elif self.type == ReportItem.TYPE_INSTRUMENT:
            return self.instr.user_code

        elif self.type == ReportItem.TYPE_CURRENCY:
            return self.ccy.user_code

        elif self.type == ReportItem.TYPE_TRANSACTION_PL:
            return 'TRANSACTION_PL'

        elif self.type == ReportItem.TYPE_FX_TRADE:
            return 'FX_TRADE'

        elif self.type == ReportItem.TYPE_MISMATCH:
            return self.instr.user_code

        elif self.type == ReportItem.TYPE_SUMMARY:
            return 'SUMMARY'

        elif self.type == ReportItem.TYPE_INVESTED_CURRENCY:
            return self.ccy.user_code

        elif self.type == ReportItem.TYPE_INVESTED_SUMMARY:
            return 'INVESTED_SUMMARY'

        return '<ERROR>'

    @property
    def name(self):
        if self.type == ReportItem.TYPE_UNKNOWN:
            return '<UNKNOWN>'

        elif self.type == ReportItem.TYPE_INSTRUMENT:
            return self.instr.name

        elif self.type == ReportItem.TYPE_CURRENCY:
            return self.ccy.name

        elif self.type == ReportItem.TYPE_TRANSACTION_PL:
            return ugettext('Transaction PL')

        elif self.type == ReportItem.TYPE_FX_TRADE:
            return ugettext('FX-Trade')

        elif self.type == ReportItem.TYPE_MISMATCH:
            return self.link_instr.name

        elif self.type == ReportItem.TYPE_SUMMARY:
            return ugettext('Summary')

        elif self.type == ReportItem.TYPE_INVESTED_CURRENCY:
            return self.ccy.name

        elif self.type == ReportItem.TYPE_INVESTED_SUMMARY:
            return ugettext('Invested summary')

        return '<ERROR>'

    @property
    def detail(self):
        if self.detail_trn:
            expr = self.acc.type.transaction_details_expr
            if expr:
                try:
                    value = formula.safe_eval(expr, names={'item': self})
                except formula.InvalidExpression:
                    value = ugettext('Invalid expression')
                return value
        return None

    @staticmethod
    def sort_key(report, item):
        return (
            item.type,
            getattr(item.prtfl, 'id', None),
            getattr(item.acc, 'id', None),
            getattr(item.str1, 'id', None),
            getattr(item.str2, 'id', None),
            getattr(item.str3, 'id', None),
            getattr(item.detail_trn, 'id', None),
            getattr(item.instr, 'id', None),
            getattr(item.ccy, 'id', None),
        )

    @staticmethod
    def group_key(report, item):
        return (
            item.type,
            getattr(item.prtfl, 'id', None) if report.detail_by_portfolio else None,
            getattr(item.acc, 'id', None) if report.detail_by_account else None,
            getattr(item.str1, 'id', None) if report.detail_by_strategy1 else None,
            getattr(item.str2, 'id', None) if report.detail_by_strategy2 else None,
            getattr(item.str3, 'id', None) if report.detail_by_strategy3 else None,
            getattr(item.detail_trn, 'id', None) if report.show_transaction_details else None,
            getattr(item.instr, 'id', None),
            getattr(item.ccy, 'id', None),
        )

    @staticmethod
    def mismatch_sort_key(report, item):
        return (
            item.type,
            getattr(item.prtfl, 'id', None),
            getattr(item.acc, 'id', None),
            getattr(item.instr, 'id', None),
            getattr(item.mismatch_ccy, 'id', None),
        )

    @staticmethod
    def mismatch_group_key(report, item):
        return (
            item.type,
            getattr(item.prtfl, 'id', None) if report.detail_by_portfolio else None,
            getattr(item.acc, 'id', None) if report.detail_by_account else None,
            getattr(item.instr, 'id', None),
            getattr(item.mismatch_ccy, 'id', None),
        )

    @property
    def trn_cls(self):
        return getattr(self.trn, 'trn_cls', None)

    @property
    def detail_trn(self):
        if self.trn and self.acc and self.trn.is_show_details(self.acc):
            return self.trn
        return None

    @property
    def custom_fields(self):
        res = []
        for cf in self.report.custom_fields:
            if cf.expr:
                try:
                    value = formula.safe_eval(cf.expr, names={'item': self})
                except formula.InvalidExpression:
                    value = ugettext('Invalid expression')
            else:
                value = None
            res.append({
                'custom_field': cf,
                'value': value
            })
        return res

    # instr

    @property
    def instr_price_rep(self):
        if self.instr:
            return self.pricing_provider[self.instr]
        return None

    @property
    def instr_pricing_ccy_rep(self):
        if self.instr:
            return self.fx_rate_provider[self.instr.pricing_currency]
        return None

    @property
    def instr_pricing_ccy_rep_fx(self):
        return getattr(self.instr_pricing_ccy_rep, 'fx_rate', float('nan'))

    @property
    def instr_accrued_ccy_rep(self):
        if self.instr:
            return self.fx_rate_provider[self.instr.accrued_currency]
        return None

    @property
    def instr_accrued_ccy_rep_fx(self):
        return getattr(self.instr_accrued_ccy_rep, 'fx_rate', float('nan'))

    @property
    def instr_principal_sys(self):
        if self.instr:
            price = self.instr_price_rep
            return (self.pos_size * self.instr.price_multiplier * price.principal_price) * self.instr_pricing_ccy_rep_fx
        return 0.0

    @property
    def instr_accrued_sys(self):
        if self.instr:
            price = self.instr_price_rep
            return (self.pos_size * self.instr.accrued_multiplier * price.accrued_price) * self.instr_pricing_ccy_rep_fx
        return 0.0

    # report ccy

    @property
    def report_ccy_is_sys(self):
        return self.report.report_currency.is_system

    @property
    def report_ccy_rep(self):
        return self.fx_rate_provider[self.report.report_currency]

    @property
    def report_ccy_rep_fx(self):
        return getattr(self.report_ccy_rep, 'fx_rate', float('nan'))

    # ccy

    @property
    def ccy_rep(self):
        if self.ccy:
            return self.fx_rate_provider[self.ccy]
        return None

    @property
    def ccy_rep_fx(self):
        return getattr(self.ccy_rep, 'fx_rate', float('nan'))

    # full ----------------------------------------------------

    @property
    def total_sys(self):
        return self.principal_sys + self.carry_sys + self.overheads_sys

    # full / closed ----------------------------------------------------
    @property
    def total_closed_sys(self):
        return self.principal_closed_sys + self.carry_closed_sys + self.overheads_closed_sys

    # full / opened ----------------------------------------------------
    @property
    def total_opened_sys(self):
        return self.principal_opened_sys + self.carry_opened_sys + self.overheads_opened_sys

    # fx ----------------------------------------------------
    @property
    def total_fx_sys(self):
        return self.principal_fx_sys + self.carry_fx_sys + self.overheads_fx_sys

    # fx / closed ----------------------------------------------------
    @property
    def total_fx_closed_sys(self):
        return self.principal_fx_closed_sys + self.carry_fx_closed_sys + self.overheads_fx_closed_sys

    # fx / opened ----------------------------------------------------
    @property
    def total_fx_opened_sys(self):
        return self.principal_fx_opened_sys + self.carry_fx_opened_sys + self.overheads_fx_opened_sys

    # fixed ----------------------------------------------------
    @property
    def total_fixed_sys(self):
        return self.principal_fixed_sys + self.carry_fixed_sys + self.overheads_fixed_sys

    # fixed / closed ----------------------------------------------------
    @property
    def total_fixed_closed_sys(self):
        return self.principal_fixed_closed_sys + self.carry_fixed_closed_sys + self.overheads_fixed_closed_sys

    # fixed / opened ----------------------------------------------------
    @property
    def total_fixed_opened_sys(self):
        return self.principal_fixed_opened_sys + self.carry_fixed_opened_sys + self.overheads_fixed_opened_sys

    # functions

    def add(self, o):
        # TODO: in TYPE_INSTRUMENT or global
        # full ----------------------------------------------------
        self.principal_sys += o.principal_sys
        self.carry_sys += o.carry_sys
        self.overheads_sys += o.overheads_sys

        # full / closed ----------------------------------------------------
        self.principal_closed_sys += o.principal_closed_sys
        self.carry_closed_sys += o.carry_closed_sys
        self.overheads_closed_sys += o.overheads_closed_sys

        # full / opened ----------------------------------------------------
        self.principal_opened_sys += o.principal_opened_sys
        self.carry_opened_sys += o.carry_opened_sys
        self.overheads_opened_sys += o.overheads_opened_sys

        # fx ----------------------------------------------------
        self.principal_fx_sys += o.principal_fx_sys
        self.carry_fx_sys += o.carry_fx_sys
        self.overheads_fx_sys += o.overheads_fx_sys

        # fx / closed ----------------------------------------------------
        self.principal_fx_closed_sys += o.principal_fx_closed_sys
        self.carry_fx_closed_sys += o.carry_fx_closed_sys
        self.overheads_fx_closed_sys += o.overheads_fx_closed_sys

        # fx / opened ----------------------------------------------------
        self.principal_fx_opened_sys += o.principal_fx_opened_sys
        self.carry_fx_opened_sys += o.carry_fx_opened_sys
        self.overheads_fx_opened_sys += o.overheads_fx_opened_sys

        # fixed ----------------------------------------------------
        self.principal_fixed_sys += o.principal_fixed_sys
        self.carry_fixed_sys += o.carry_fixed_sys
        self.overheads_fixed_sys += o.overheads_fixed_sys

        # fixed / closed ----------------------------------------------------
        self.principal_fixed_closed_sys += o.principal_fixed_closed_sys
        self.carry_fixed_closed_sys += o.carry_fixed_closed_sys
        self.overheads_fixed_closed_sys += o.overheads_fixed_closed_sys

        # fixed / opened ----------------------------------------------------
        self.principal_fixed_opened_sys += o.principal_fixed_opened_sys
        self.carry_fixed_opened_sys += o.carry_fixed_opened_sys
        self.overheads_fixed_opened_sys += o.overheads_fixed_opened_sys

        if self.type == ReportItem.TYPE_CURRENCY or self.type == ReportItem.TYPE_INVESTED_CURRENCY:
            self.pos_size += o.pos_size

            # self.market_value_sys += o.pos_size * o.ccy_rep_fx

        elif self.type == ReportItem.TYPE_INSTRUMENT:
            self.pos_size += o.pos_size

            # self.principal_sys += o.instr_principal_sys
            # self.carry_sys += o.instr_accrued_sys

            # self.market_value_sys += o.instr_principal_sys + o.instr_accrued_sys
            self.cost_sys += o.cost_sys

            self.total_real_sys += o.total_real_sys
            # self.total_unreal_sys += o.market_value_sys + o.cost_sys
            # self.total_unreal_sys += (o.instr_principal_sys + o.instr_accrued_sys) + o.cost_sys

        elif self.type == ReportItem.TYPE_SUMMARY or self.type == ReportItem.TYPE_INVESTED_SUMMARY:
            self.market_value_sys += o.market_value_sys
            self.total_real_sys += o.total_real_sys
            self.total_unreal_sys += o.total_unreal_sys

        elif self.type == ReportItem.TYPE_MISMATCH:
            self.mismatch += o.mismatch

    def close(self):
        if self.type == ReportItem.TYPE_CURRENCY or self.type == ReportItem.TYPE_INVESTED_CURRENCY:
            self.market_value_sys = self.pos_size * self.ccy_rep_fx

        elif self.type == ReportItem.TYPE_INSTRUMENT:
            self.market_value_sys = self.instr_principal_sys + self.instr_accrued_sys

            self.total_unreal_sys = self.market_value_sys + self.cost_sys

            # full ----------------------------------------------------
            self.principal_sys += self.instr_principal_sys
            self.carry_sys += self.instr_accrued_sys

            # full / closed ----------------------------------------------------
            pass

            # full / opened ----------------------------------------------------
            self.principal_opened_sys += self.instr_principal_sys
            self.carry_opened_sys += self.instr_accrued_sys

            # fx ----------------------------------------------------
            pass

            # fx / closed ----------------------------------------------------
            pass

            # fx / opened ----------------------------------------------------
            pass

            # fixed ----------------------------------------------------
            self.principal_fixed_sys += self.instr_principal_sys
            self.carry_fixed_sys += self.instr_accrued_sys

            # fixed / closed ----------------------------------------------------
            pass

            # fixed / opened ----------------------------------------------------
            self.principal_fixed_opened_sys += self.instr_principal_sys
            self.carry_fixed_opened_sys += self.instr_accrued_sys


class Report(object):
    def __init__(self, id=None, master_user=None, task_id=None, task_status=None,
                 report_date=None, report_currency=None, pricing_policy=None, cost_method=None,
                 allocation_end_multiplier=0.5, pl_real_unreal_end_multiplier=0.5,
                 detail_by_portfolio=False, detail_by_account=False, detail_by_strategy1=False,
                 detail_by_strategy2=False, detail_by_strategy3=False,
                 show_transaction_details=False,
                 portfolios=None, accounts=None, strategies1=None, strategies2=None, strategies3=None,
                 transaction_classes=None, date_field=None,
                 custom_fields=None, items=None):
        self.id = id
        self.task_id = task_id
        self.task_status = task_status

        self.master_user = master_user
        self.pricing_policy = pricing_policy
        self.report_date = report_date or (date_now() - timedelta(days=1))
        self.report_currency = report_currency or master_user.system_currency
        self.cost_method = cost_method or CostMethod.objects.get(pk=CostMethod.AVCO)
        self.pl_real_unreal_end_multiplier = pl_real_unreal_end_multiplier if pl_real_unreal_end_multiplier is not None else 0.5
        self.allocation_end_multiplier = allocation_end_multiplier if allocation_end_multiplier is not None else 0.5

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
        self.transactions = []

    def __str__(self):
        return "%s for %s @ %s" % (self.__class__.__name__, self.master_user, self.report_date)


class ReportBuilder(object):
    def __init__(self, instance=None, queryset=None, transactions=None):
        self.instance = instance
        self._queryset = queryset
        self._transactions = transactions

        # self._filter_date_attr = self.instance.date_field
        # self._now = timezone.now().date()
        # self._report_date = self.instance.report_date or self._now

        # self._detail_by_portfolio = self.instance.detail_by_portfolio
        # self._detail_by_account = self.instance.detail_by_account
        # self._detail_by_strategy1 = self.instance.detail_by_strategy1
        # self._detail_by_strategy2 = self.instance.detail_by_strategy2
        # self._detail_by_strategy3 = self.instance.detail_by_strategy3
        # self._any_details = self._detail_by_portfolio or self._detail_by_account or self._detail_by_strategy1 or self._detail_by_strategy2 or self._detail_by_strategy3

        self._items = []

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
            p.fill_using_transactions(self._trn_qs())
            return p

    @cached_property
    def _fx_rate_provider(self):
        if self.instance.pricing_policy is None:
            return FakeCurrencyFxRateProvider(None, None, self.instance.report_date)
        else:
            p = CurrencyFxRateProvider(self.instance.master_user, self.instance.pricing_policy,
                                       self.instance.report_date)
            p.fill_using_transactions(self._trn_qs(), currencies=[self.instance.report_currency])
            return p

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

    @cached_property
    def transactions(self):
        if self._transactions:
            return self._transactions

        res = []
        for t in self._trn_qs():
            overrides = {}
            # self._detail_by_portfolio = self.instance.detail_by_portfolio
            # self._detail_by_account = self.instance.detail_by_account
            # self._detail_by_strategy1 = self.instance.detail_by_strategy1
            # self._detail_by_strategy2 = self.instance.detail_by_strategy2
            # self._detail_by_strategy3 = self.instance.detail_by_strategy3
            if not self.instance.detail_by_portfolio:
                overrides['portfolio'] = self.instance.master_user.portfolio

            if not self.instance.detail_by_account:
                overrides['account_position'] = self.instance.master_user.account
                overrides['account_cash'] = self.instance.master_user.account
                overrides['account_interim'] = self.instance.master_user.account

            if not self.instance.detail_by_strategy1:
                overrides['strategy1_position'] = self.instance.master_user.strategy1
                overrides['strategy1_cash'] = self.instance.master_user.strategy1

            if not self.instance.detail_by_strategy1:
                overrides['strategy1_position'] = self.instance.master_user.strategy1
                overrides['strategy1_cash'] = self.instance.master_user.strategy1

            if not self.instance.detail_by_strategy2:
                overrides['strategy2_position'] = self.instance.master_user.strategy2
                overrides['strategy2_cash'] = self.instance.master_user.strategy2

            if not self.instance.detail_by_strategy3:
                overrides['strategy3_position'] = self.instance.master_user.strategy3
                overrides['strategy3_cash'] = self.instance.master_user.strategy3

            t = VirtualTransaction(
                report=self.instance,
                pricing_provider=self._pricing_provider,
                fx_rate_provider=self._fx_rate_provider,
                trn=t,
                overrides=overrides
            )
            res.append(t)

        res = self._multipliers(res)
        res = self._transfers(res)

        return res

    def _multipliers(self, src):
        rolling_positions = Counter()
        items = defaultdict(list)

        multipliers_delta = []

        def _set_multiplier(t0, multiplier):
            # if isclose(t.r_multiplier, multiplier):
            #     return
            multipliers_delta.append((t0, multiplier - t0.multiplier))
            t0.multiplier = multiplier

        res = []
        for t in src:
            res.append(t)

            if t.trn_cls.id not in [TransactionClass.BUY, TransactionClass.SELL]:
                continue

            # do not use strategy!!!
            t_key = self._make_key(
                instr=t.instr,
                prtfl=t.prtfl,
                acc=t.acc_pos
            )

            multipliers_delta.clear()
            t.multiplier = 0.0
            rolling_position = rolling_positions[t_key]

            if isclose(rolling_position, 0.0):
                k = -1
            else:
                k = - t.pos_size / rolling_position

            if self.instance.cost_method.id == CostMethod.AVCO:

                if k > 1.0:
                    if t_key in items:
                        for t0 in items[t_key]:
                            _set_multiplier(t0, 1.0)
                        del items[t_key]
                    items[t_key].append(t)
                    _set_multiplier(t, 1.0 / k)
                    rolling_position = t.pos_size * (1.0 - t.multiplier)

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
                            _set_multiplier(t0, t0.multiplier + k * (1.0 - t0.multiplier))
                    _set_multiplier(t, 1.0)
                    rolling_position += t.pos_size

                else:
                    items[t_key].append(t)
                    rolling_position += t.pos_size

            elif self.instance.cost_method.id == CostMethod.FIFO:

                if k > 1.0:
                    if t_key in items:
                        for t0 in items[t_key]:
                            _set_multiplier(t0, 1.0)
                        items[t_key].clear()
                    items[t_key].append(t)
                    _set_multiplier(t, 1.0 / k)
                    rolling_position = t.pos_size * (1.0 - t.multiplier)

                elif isclose(k, 1.0):
                    if t_key in items:
                        for t0 in items[t_key]:
                            _set_multiplier(t0, 1.0)
                        del items[t_key]
                    _set_multiplier(t, 1.0)
                    rolling_position = 0.0

                elif k > 0.0:
                    position = t.pos_size
                    if t_key in items:
                        t_items = items[t_key]
                        for t0 in t_items:
                            remaining = t0.pos_size * (1.0 - t0.multiplier)
                            k0 = - position / remaining
                            if k0 > 1.0:
                                _set_multiplier(t0, 1.0)
                                position += remaining
                            elif isclose(k0, 1.0):
                                _set_multiplier(t0, 1.0)
                                position += remaining
                            elif k0 > 0.0:
                                position += remaining * k0
                                _set_multiplier(t0, t0.multiplier + k0 * (1.0 - t0.multiplier))
                            # else:
                            #     break
                            if isclose(position, 0.0):
                                break
                        t_items = [t0 for t0 in t_items if not isclose(t0.multiplier, 1.0)]
                        if t_items:
                            items[t_key] = t_items
                        else:
                            del items[t_key]

                    _set_multiplier(t, abs((t.pos_size - position) / t.pos_size))
                    rolling_position += t.pos_size * t.multiplier

                else:
                    items[t_key].append(t)
                    rolling_position += t.pos_size

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
                    sum_total += inc_multiplier0 * t0.total_sys

                for t0, inc_multiplier0 in multipliers_delta:
                    mult = end_mult if t0.pk == t.pk else init_mult

                    matched = abs((t0.pos_size * inc_multiplier0) / (
                        t.pos_size * inc_multiplier))
                    # adj = matched * mult

                    # t0.real_pl_principal_with_sign += sum_principal * matched * mult
                    # t0.real_pl_carry_with_sign += sum_carry * matched * mult
                    # t0.real_pl_overheads_with_sign += sum_overheads * matched * mult
                    t0.total_real_sys += sum_total * matched * mult

        # for t in transactions:
        #     if t.trn_cls.id not in [TransactionClass.BUY, TransactionClass.SELL]:
        #         continue
        #     # t.r_position_size = t.pos_size * (1.0 - t.multiplier)
        #     # t.r_cost = t.principal_ * (1.0 - t.multiplier)
        #     pass
        return res

    def _transfers(self, src):
        res = []
        for t in src:

            if t.trn_cls.id == TransactionClass.TRANSFER:

                if t.position_size_with_sign >= 0:
                    t1 = VirtualTransaction(
                        report=self.instance,
                        pricing_provider=self._pricing_provider,
                        fx_rate_provider=self._fx_rate_provider,
                        trn=t.trn,
                        overrides={
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
                        report=self.instance,
                        pricing_provider=self._pricing_provider,
                        fx_rate_provider=self._fx_rate_provider,
                        trn=t.trn,
                        overrides={
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
                        report=self.instance,
                        pricing_provider=self._pricing_provider,
                        fx_rate_provider=self._fx_rate_provider,
                        trn=t.trn,
                        overrides={
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
                        report=self.instance,
                        pricing_provider=self._pricing_provider,
                        fx_rate_provider=self._fx_rate_provider,
                        trn=t.trn,
                        overrides={
                            'transaction_class': self._transaction_class_sell,
                            'account_position': t.account_position,
                            'account_cash': t.account_position,

                            'position_size_with_sign': t.position_size_with_sign,
                            'cash_consideration': -t.cash_consideration,
                            'principal_with_sign': -t.principal_with_sign,
                            'carry_with_sign': -t.carry_with_sign,
                            'overheads_with_sign': -t.overheads_with_sign,
                        })
                res.append(t1)
                res.append(t2)

            elif t.trn_cls.id == TransactionClass.FX_TRANSFER:
                t1 = VirtualTransaction(
                    report=self.instance,
                    pricing_provider=self._pricing_provider,
                    fx_rate_provider=self._fx_rate_provider,
                    trn=t.trn,
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
                    report=self.instance,
                    pricing_provider=self._pricing_provider,
                    fx_rate_provider=self._fx_rate_provider,
                    trn=t.trn,
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
                res.append(t1)
                res.append(t2)

            else:
                res.append(t)
        return res

    def build(self):
        mismatch_items = []
        for trn in self.transactions:
            if trn.link_instr and not isclose(trn.mismatch, 0.0):
                item = ReportItem.from_trn(self.instance, self._pricing_provider, self._fx_rate_provider,
                                           ReportItem.TYPE_MISMATCH, trn,
                                           str1=self.instance.master_user.strategy1,
                                           str2=self.instance.master_user.strategy2,
                                           str3=self.instance.master_user.strategy3,
                                           )
                mismatch_items.append(item)

            if trn.trn_cls.id in [TransactionClass.BUY, TransactionClass.SELL]:
                self._add_instr(trn)
                self._add_cash(trn, val=trn.cash, ccy=trn.stl_ccy)

            elif trn.trn_cls.id == TransactionClass.FX_TRADE:
                # TODO: Что используем для strategy?
                self._add_cash(trn, val=trn.pos_size, ccy=trn.trn_ccy, acc=trn.acc_pos, str1=trn.str1_pos,
                               str2=trn.str2_pos, str3=trn.str3_pos)

                self._add_cash(trn, val=trn.cash, ccy=trn.stl_ccy)

                # P&L
                item = ReportItem.from_trn(self.instance, self._pricing_provider, self._fx_rate_provider,
                                           ReportItem.TYPE_FX_TRADE, trn, acc=trn.acc_pos,
                                           str1=trn.str1_pos, str2=trn.str2_pos, str3=trn.str3_pos)
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

            elif trn.trn_cls.id == TransactionClass.TRANSFER:
                raise RuntimeError('Virtual transaction must be created')

            elif trn.trn_cls.id == TransactionClass.FX_TRANSFER:
                raise RuntimeError('Virtual transaction must be created')

            elif trn.trn_cls.id in [TransactionClass.CASH_INFLOW, TransactionClass.CASH_OUTFLOW]:
                self._add_cash(trn, val=trn.pos_size, ccy=trn.trn_ccy,
                               acc=trn.acc_pos, str1=trn.str1_pos, str2=trn.str2_pos,
                               str3=trn.str3_pos)

            else:
                raise RuntimeError('Invalid transaction class: %s' % trn.transaction_class_id)

        _items = sorted(self._items, key=partial(ReportItem.sort_key, self.instance))

        res_items = []
        invested_items = []

        for k, g in groupby(_items, key=partial(ReportItem.group_key, self.instance)):
            res_item = None
            invested_item = None

            for item in g:
                if item.type in [ReportItem.TYPE_INSTRUMENT, ReportItem.TYPE_CURRENCY, ReportItem.TYPE_TRANSACTION_PL,
                                 ReportItem.TYPE_FX_TRADE]:
                    if res_item is None:
                        res_item = ReportItem.from_item(item)
                    res_item.add(item)

                if item.trn and item.trn.trn_cls.id in [TransactionClass.CASH_INFLOW, TransactionClass.CASH_OUTFLOW]:
                    if invested_item is None:
                        invested_item = ReportItem.from_item(item)
                        invested_item.type = ReportItem.TYPE_INVESTED_CURRENCY
                    invested_item.add(item)

            if res_item:
                res_item.close()
                res_items.append(res_item)

            if invested_item:
                invested_item.close()
                invested_items.append(invested_item)

        mismatch_items0 = sorted(mismatch_items, key=partial(ReportItem.mismatch_sort_key, self.instance))
        mismatch_items = []
        for k, g in groupby(mismatch_items0, key=partial(ReportItem.mismatch_group_key, self.instance)):
            mismatch_item = None
            for item in g:
                if mismatch_item is None:
                    mismatch_item = ReportItem.from_item(item)
                mismatch_item.add(item)
            if mismatch_item:
                mismatch_item.close()
                mismatch_items.append(mismatch_item)

        summary = ReportItem(self.instance, self._pricing_provider, self._fx_rate_provider, ReportItem.TYPE_SUMMARY)
        for item in res_items:
            if item.type in [ReportItem.TYPE_INSTRUMENT, ReportItem.TYPE_CURRENCY, ReportItem.TYPE_TRANSACTION_PL,
                             ReportItem.TYPE_FX_TRADE]:
                summary.add(item)

        invested_summary = ReportItem(self.instance, self._pricing_provider, self._fx_rate_provider,
                                      ReportItem.TYPE_INVESTED_SUMMARY)
        for item in invested_items:
            if item.type in [ReportItem.TYPE_INVESTED_CURRENCY]:
                invested_summary.add(item)

        self.instance.items = res_items + mismatch_items + invested_items + [summary, invested_summary]

        print('0' * 100)
        VirtualTransaction.dumps(self.transactions)
        print('1' * 100)
        ReportItem.dumps(self._items)
        print('2' * 100)
        ReportItem.dumps(self.instance.items)
        print('3' * 100)

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
