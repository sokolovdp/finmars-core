import logging
from datetime import timedelta

from django.utils.translation import ugettext_lazy, ugettext

from poms.common import formula
from poms.common.formula_accruals import f_duration
from poms.common.formula_accruals import f_xirr
from poms.common.utils import isclose, date_now
from poms.instruments.models import CostMethod
from poms.reports.builders.base_item import BaseReportItem
from poms.transactions.models import TransactionClass

_l = logging.getLogger('poms.reports')


class ReportItem(BaseReportItem):
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

    SUBTYPE_UNKNOWN = 0
    SUBTYPE_TOTAL = 1
    SUBTYPE_CLOSED = 2
    SUBTYPE_OPENED = 3
    SUBTYPE_CHOICES = (
        (SUBTYPE_UNKNOWN, ugettext_lazy('Unknown')),
        (SUBTYPE_TOTAL, ugettext_lazy('Total')),
        (SUBTYPE_CLOSED, ugettext_lazy('Closed')),
        (SUBTYPE_OPENED, ugettext_lazy('Opened')),
    )

    type = TYPE_UNKNOWN
    subtype = SUBTYPE_UNKNOWN
    trn = None

    instr = None
    ccy = None
    trn_ccy = None  # TODO: deprecated - for FX_TRADE
    prtfl = None
    acc = None
    str1 = None
    str2 = None
    str3 = None
    # detail_trn = None
    notes = None  # used by Transaction-PL, FX-Trade and Cash-In/Out
    custom_fields = []
    is_empty = False

    pricing_ccy = None
    last_notes = ''

    # link
    mismatch = 0.0
    # mismatch_ccy = None
    mismatch_prtfl = None
    mismatch_acc = None

    # allocations
    alloc = None
    alloc_bl = None  # TODO: deprecated
    alloc_pl = None  # TODO: deprecated

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
    pricing_ccy_cur = None
    pricing_ccy_cur_fx = 0.0

    # instr
    instr_principal_res = 0.0
    instr_accrued_res = 0.0
    exposure_res = 0.0
    exposure_loc = 0.0

    instr_accrual = None
    instr_accrual_accrued_price = 0.0

    # ----------------------------------------------------

    pos_size = 0.0
    market_value_res = 0.0
    market_value_loc = 0.0
    cost_res = 0.0
    ytm = 0.0
    modified_duration = 0.0
    ytm_at_cost = 0.0
    time_invested_days = 0.0
    time_invested = 0.0
    gross_cost_res = 0.0
    gross_cost_loc = 0.0
    net_cost_res = 0.0
    net_cost_loc = 0.0
    principal_invested_res = 0.0
    principal_invested_loc = 0.0
    amount_invested_res = 0.0
    amount_invested_loc = 0.0
    pos_return_res = 0.0
    pos_return_loc = 0.0
    net_pos_return_res = 0.0
    net_pos_return_loc = 0.0
    daily_price_change = 0.0
    mtd_price_change = 0.0

    # P&L ----------------------------------------------------

    # full ----------------------------------------------------
    principal_res = 0.0
    carry_res = 0.0
    overheads_res = 0.0
    total_res = 0.0

    principal_loc = 0.0
    carry_loc = 0.0
    overheads_loc = 0.0
    total_loc = 0.0

    # full / closed ----------------------------------------------------
    principal_closed_res = 0.0
    carry_closed_res = 0.0
    overheads_closed_res = 0.0
    total_closed_res = 0.0

    principal_closed_loc = 0.0
    carry_closed_loc = 0.0
    overheads_closed_loc = 0.0
    total_closed_loc = 0.0

    # full / opened ----------------------------------------------------
    principal_opened_res = 0.0
    carry_opened_res = 0.0
    overheads_opened_res = 0.0
    total_opened_res = 0.0

    principal_opened_loc = 0.0
    carry_opened_loc = 0.0
    overheads_opened_loc = 0.0
    total_opened_loc = 0.0

    # fx ----------------------------------------------------
    principal_fx_res = 0.0
    carry_fx_res = 0.0
    overheads_fx_res = 0.0
    total_fx_res = 0.0

    principal_fx_loc = 0.0
    carry_fx_loc = 0.0
    overheads_fx_loc = 0.0
    total_fx_loc = 0.0

    # fx / closed ----------------------------------------------------
    principal_fx_closed_res = 0.0
    carry_fx_closed_res = 0.0
    overheads_fx_closed_res = 0.0
    total_fx_closed_res = 0.0

    principal_fx_closed_loc = 0.0
    carry_fx_closed_loc = 0.0
    overheads_fx_closed_loc = 0.0
    total_fx_closed_loc = 0.0

    # fx / opened ----------------------------------------------------
    principal_fx_opened_res = 0.0
    carry_fx_opened_res = 0.0
    overheads_fx_opened_res = 0.0
    total_fx_opened_res = 0.0

    principal_fx_opened_loc = 0.0
    carry_fx_opened_loc = 0.0
    overheads_fx_opened_loc = 0.0
    total_fx_opened_loc = 0.0

    # fixed ----------------------------------------------------
    principal_fixed_res = 0.0
    carry_fixed_res = 0.0
    overheads_fixed_res = 0.0
    total_fixed_res = 0.0

    principal_fixed_loc = 0.0
    carry_fixed_loc = 0.0
    overheads_fixed_loc = 0.0
    total_fixed_loc = 0.0

    # fixed / closed ----------------------------------------------------
    principal_fixed_closed_res = 0.0
    carry_fixed_closed_res = 0.0
    overheads_fixed_closed_res = 0.0
    total_fixed_closed_res = 0.0

    principal_fixed_closed_loc = 0.0
    carry_fixed_closed_loc = 0.0
    overheads_fixed_closed_loc = 0.0
    total_fixed_closed_loc = 0.0

    # fixed / opened ----------------------------------------------------
    principal_fixed_opened_res = 0.0
    carry_fixed_opened_res = 0.0
    overheads_fixed_opened_res = 0.0
    total_fixed_opened_res = 0.0

    principal_fixed_opened_loc = 0.0
    carry_fixed_opened_loc = 0.0
    overheads_fixed_opened_loc = 0.0
    total_fixed_opened_loc = 0.0

    pl_total_fields = [
        # full ----------------------------------------------------
        ('principal_res', None),
        ('carry_res', None),
        ('overheads_res', None),
        ('total_res', None),

        ('principal_loc', None),
        ('carry_loc', None),
        ('overheads_loc', None),
        ('total_loc', None),

        # fx ----------------------------------------------------
        ('principal_fx_res', None),
        ('carry_fx_res', None),
        ('overheads_fx_res', None),
        ('total_fx_res', None),

        ('principal_fx_loc', None),
        ('carry_fx_loc', None),
        ('overheads_fx_loc', None),
        ('total_fx_loc', None),
        # fixed ----------------------------------------------------
        ('principal_fixed_res', None),
        ('carry_fixed_res', None),
        ('overheads_fixed_res', None),
        ('total_fixed_res', None),

        ('principal_fixed_loc', None),
        ('carry_fixed_loc', None),
        ('overheads_fixed_loc', None),
        ('total_fixed_loc', None),
    ]
    pl_closed_fields = [
        # full / closed ----------------------------------------------------
        ('principal_closed_res', None),
        ('carry_closed_res', None),
        ('overheads_closed_res', None),
        ('total_closed_res', None),

        ('principal_closed_loc', None),
        ('carry_closed_loc', None),
        ('overheads_closed_loc', None),
        ('total_closed_loc', None),

        # fx / closed ----------------------------------------------------
        ('principal_fx_closed_res', None),
        ('carry_fx_closed_res', None),
        ('overheads_fx_closed_res', None),
        ('total_fx_closed_res', None),

        ('principal_fx_closed_loc', None),
        ('carry_fx_closed_loc', None),
        ('overheads_fx_closed_loc', None),
        ('total_fx_closed_loc', None),
        # fixed / closed ----------------------------------------------------
        ('principal_fixed_closed_res', None),
        ('carry_fixed_closed_res', None),
        ('overheads_fixed_closed_res', None),
        ('total_fixed_closed_res', None),

        ('principal_fixed_closed_loc', None),
        ('carry_fixed_closed_loc', None),
        ('overheads_fixed_closed_loc', None),
        ('total_fixed_closed_loc', None),
    ]
    pl_opened_fields = [
        # full / opened ----------------------------------------------------
        ('principal_opened_res', None),
        ('carry_opened_res', None),
        ('overheads_opened_res', None),
        ('total_opened_res', None),

        ('principal_opened_loc', None),
        ('carry_opened_loc', None),
        ('overheads_opened_loc', None),
        ('total_opened_loc', None),

        # fx / opened ----------------------------------------------------
        ('principal_fx_opened_res', None),
        ('carry_fx_opened_res', None),
        ('overheads_fx_opened_res', None),
        ('total_fx_opened_res', None),

        ('principal_fx_opened_loc', None),
        ('carry_fx_opened_loc', None),
        ('overheads_fx_opened_loc', None),
        ('total_fx_opened_loc', None),

        # fixed / opened ----------------------------------------------------
        ('principal_fixed_opened_res', None),
        ('carry_fixed_opened_res', None),
        ('overheads_fixed_opened_res', None),
        ('total_fixed_opened_res', None),

        ('principal_fixed_opened_loc', None),
        ('carry_fixed_opened_loc', None),
        ('overheads_fixed_opened_loc', None),
        ('total_fixed_opened_loc', None),
    ]

    dump_columns = [
        # 'is_cloned',
        'type_code',
        'subtype_code',
        # 'trn',
        'instr',
        'ccy',
        'trn_ccy',
        'notes',
        'prtfl',
        'acc',
        'str1',
        'str2',
        'str3',
        # 'custom_fields',
        # 'is_empty',
        'pricing_ccy',
        'last_notes',
        'mismatch',
        'mismatch_prtfl',
        'mismatch_acc',
        'alloc',
        'alloc_bl',
        'alloc_pl',
        'report_ccy_cur',
        'report_ccy_cur_fx',
        'instr_price_cur',
        'instr_price_cur_principal_price',
        'instr_price_cur_accrued_price',
        'instr_pricing_ccy_cur',
        'instr_pricing_ccy_cur_fx',
        'instr_accrued_ccy_cur',
        'instr_accrued_ccy_cur_fx',
        'ccy_cur',
        'ccy_cur_fx',
        'pricing_ccy_cur',
        'pricing_ccy_cur_fx',
        'instr_principal_res',
        'instr_accrued_res',
        'exposure_res',
        'exposure_loc',
        'instr_accrual',
        'instr_accrual_accrued_price',
        'pos_size',
        'market_value_res',
        'market_value_loc',
        'cost_res',
        'ytm',
        'modified_duration',
        'ytm_at_cost',
        'time_invested_days',
        'time_invested',
        'gross_cost_res',
        'gross_cost_loc',
        'net_cost_res',
        'net_cost_loc',
        'principal_invested_res',
        'principal_invested_loc',
        'amount_invested_res',
        'amount_invested_loc',
        'pos_return_res',
        'pos_return_loc',
        'net_pos_return_res',
        'net_pos_return_loc',
        'daily_price_change',
        'mtd_price_change',
        'principal_res',
        'carry_res',
        'overheads_res',
        'total_res',
        'principal_loc',
        'carry_loc',
        'overheads_loc',
        'total_loc',
        'principal_closed_res',
        'carry_closed_res',
        'overheads_closed_res',
        'total_closed_res',
        'principal_closed_loc',
        'carry_closed_loc',
        'overheads_closed_loc',
        'total_closed_loc',
        'principal_opened_res',
        'carry_opened_res',
        'overheads_opened_res',
        'total_opened_res',
        'principal_opened_loc',
        'carry_opened_loc',
        'overheads_opened_loc',
        'total_opened_loc',
        'principal_fx_res',
        'carry_fx_res',
        'overheads_fx_res',
        'total_fx_res',
        'principal_fx_loc',
        'carry_fx_loc',
        'overheads_fx_loc',
        'total_fx_loc',
        'principal_fx_closed_res',
        'carry_fx_closed_res',
        'overheads_fx_closed_res',
        'total_fx_closed_res',
        'principal_fx_closed_loc',
        'carry_fx_closed_loc',
        'overheads_fx_closed_loc',
        'total_fx_closed_loc',
        'principal_fx_opened_res',
        'carry_fx_opened_res',
        'overheads_fx_opened_res',
        'total_fx_opened_res',
        'principal_fx_opened_loc',
        'carry_fx_opened_loc',
        'overheads_fx_opened_loc',
        'total_fx_opened_loc',
        'principal_fixed_res',
        'carry_fixed_res',
        'overheads_fixed_res',
        'total_fixed_res',
        'principal_fixed_loc',
        'carry_fixed_loc',
        'overheads_fixed_loc',
        'total_fixed_loc',
        'principal_fixed_closed_res',
        'carry_fixed_closed_res',
        'overheads_fixed_closed_res',
        'total_fixed_closed_res',
        'principal_fixed_closed_loc',
        'carry_fixed_closed_loc',
        'overheads_fixed_closed_loc',
        'total_fixed_closed_loc',
        'principal_fixed_opened_res',
        'carry_fixed_opened_res',
        'overheads_fixed_opened_res',
        'total_fixed_opened_res',
        'principal_fixed_opened_loc',
        'carry_fixed_opened_loc',
        'overheads_fixed_opened_loc',
        'total_fixed_opened_loc',
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

        if report.report_type == Report.TYPE_BALANCE:
            item.alloc = trn.alloc_bl
            item.alloc_bl = trn.alloc_bl
        elif report.report_type == Report.TYPE_PL:
            item.alloc = trn.alloc_pl
            item.alloc_pl = trn.alloc_pl
        else:
            raise RuntimeError('Bad report type: %s' % (report.report_type,))

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

            if val is None:
                item.pos_size = trn.pos_size * (1.0 - trn.multiplier)
            else:
                item.pos_size = val
            item.cost_res = trn.principal_res * (1.0 - trn.multiplier)

            if trn.instr:
                item.pricing_ccy = trn.instr.pricing_currency
            else:
                item.pricing_ccy = trn.report.master_user.system_currency

            item.gross_cost_res = trn.gross_cost_res
            item.net_cost_res = trn.net_cost_res
            item.principal_invested_res = trn.principal_invested_res
            item.amount_invested_res = trn.amount_invested_res

            if trn.trn_cls.id in [TransactionClass.BUY, TransactionClass.SELL]:
                item.last_notes = trn.notes

            if not trn.is_cloned:
                item.ytm_at_cost = trn.weighted_ytm
                item.time_invested_days = trn.weighted_time_invested_days
                item.time_invested += trn.weighted_time_invested

        elif item.type == ReportItem.TYPE_CURRENCY:
            item.acc = acc or trn.acc_cash
            item.str1 = str1 or trn.str1_cash
            item.str2 = str2 or trn.str2_cash
            item.str3 = str3 or trn.str3_cash
            item.ccy = ccy or trn.stl_ccy

            if val is None:
                item.pos_size = 0.0
            else:
                item.pos_size = val

            item.pricing_ccy = trn.report.master_user.system_currency

        elif item.type == ReportItem.TYPE_FX_TRADE:
            item.acc = acc or trn.acc_cash
            item.str1 = str1 or trn.str1_cash
            item.str2 = str2 or trn.str2_cash
            item.str3 = str3 or trn.str3_cash
            # item.ccy = ccy
            # item.trn_ccy = trn_ccy
            item.notes = trn.notes
            # item.pricing_ccy = trn.report.master_user.system_currency

        elif item.type == ReportItem.TYPE_CASH_IN_OUT:
            item.acc = acc or trn.acc_cash
            item.str1 = str1 or trn.str1_cash
            item.str2 = str2 or trn.str2_cash
            item.str3 = str3 or trn.str3_cash
            # item.ccy = ccy
            item.notes = trn.notes
            # item.pricing_ccy = trn.report.master_user.system_currency

        elif item.type == ReportItem.TYPE_TRANSACTION_PL:
            item.acc = acc or trn.acc_cash
            item.str1 = str1 or trn.str1_cash
            item.str2 = str2 or trn.str2_cash
            item.str3 = str3 or trn.str3_cash
            item.ccy = None
            item.notes = trn.notes
            # item.pricing_ccy = None

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
        # item.trn_ccy = src.trn_ccy  # -> Currency
        item.prtfl = src.prtfl  # -> Portfolio if use_portfolio
        # item.instr = src.instr
        item.acc = src.acc  # -> Account if use_account
        item.str1 = src.str1  # -> Strategy1 if use_strategy1
        item.str2 = src.str2  # -> Strategy2 if use_strategy2
        item.str3 = src.str3  # -> Strategy3 if use_strategy3
        item.notes = src.notes
        item.pricing_ccy = src.pricing_ccy

        # if item.type in [ReportItem.TYPE_TRANSACTION_PL, ReportItem.TYPE_FX_TRADE]:
        #     item.trn = src.trn
        if src.detail_trn:
            item.trn = src.trn

        item.alloc = src.alloc
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
        except ArithmeticError:
            report_ccy_cur_fx = 0.0

        if self.instr:
            self.instr_price_cur = self.pricing_provider[self.instr]
            self.instr_price_cur_principal_price = self.instr_price_cur.principal_price
            self.instr_price_cur_accrued_price = self.instr_price_cur.accrued_price
            self.instr_pricing_ccy_cur = self.fx_rate_provider[self.instr.pricing_currency]
            self.instr_pricing_ccy_cur_fx = self.instr_pricing_ccy_cur.fx_rate * report_ccy_cur_fx
            self.instr_accrued_ccy_cur = self.fx_rate_provider[self.instr.accrued_currency]
            self.instr_accrued_ccy_cur_fx = self.instr_accrued_ccy_cur.fx_rate * report_ccy_cur_fx

            self.pricing_ccy_cur = self.instr_pricing_ccy_cur
            self.pricing_ccy_cur_fx = self.instr_pricing_ccy_cur_fx

        if self.ccy:
            self.ccy_cur = self.fx_rate_provider[self.ccy]
            self.ccy_cur_fx = self.ccy_cur.fx_rate * report_ccy_cur_fx

            if self.pricing_ccy:
                self.pricing_ccy_cur = self.fx_rate_provider[self.pricing_ccy]
                self.pricing_ccy_cur_fx = self.pricing_ccy_cur.fx_rate * report_ccy_cur_fx

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

            # self.ytm_at_cost += o.ytm_at_cost
            # self.time_invested_days += o.time_invested_days
            # self.time_invested += o.time_invested

            self.gross_cost_res += o.gross_cost_res
            self.net_cost_res += o.net_cost_res
            self.principal_invested_res += o.principal_invested_res
            self.amount_invested_res += o.amount_invested_res

            if o.last_notes is not None:
                self.last_notes = o.last_notes

        # elif self.type == ReportItem.TYPE_SUMMARY or self.type == ReportItem.TYPE_INVESTED_SUMMARY:
        elif self.type == ReportItem.TYPE_SUMMARY:
            self.market_value_res += o.market_value_res
            # self.total_real_res += o.total_real_res
            # self.total_unreal_res += o.total_unreal_res

        elif self.type == ReportItem.TYPE_MISMATCH:
            self.mismatch += o.mismatch

    def add_pass2(self, trn):
        if not trn.is_cloned and self.type == ReportItem.TYPE_INSTRUMENT:
            self.ytm_at_cost += trn.weighted_ytm
            self.time_invested_days += trn.weighted_time_invested_days
            # self.time_invested += trn.weighted_time_invested

    # def add_pos(self, o):
    #     if self.type == ReportItem.TYPE_CURRENCY:
    #         self.pos_size += o.pos_size
    #
    #     elif self.type == ReportItem.TYPE_INSTRUMENT:
    #         self.pos_size += o.pos_size

    def close(self):
        # if self.type == ReportItem.TYPE_CURRENCY or self.type == ReportItem.TYPE_INVESTED_CURRENCY:
        if self.type == ReportItem.TYPE_CURRENCY:
            self.market_value_res = self.pos_size * self.ccy_cur_fx

        elif self.type == ReportItem.TYPE_INSTRUMENT:
            if self.instr:
                self.instr_principal_res = self.pos_size * self.instr.price_multiplier * self.instr_price_cur_principal_price * self.instr_pricing_ccy_cur_fx
                self.instr_accrued_res = self.pos_size * self.instr.accrued_multiplier * self.instr_price_cur_accrued_price * self.instr_pricing_ccy_cur_fx

                # _l.debug('> instr_accrual: instr=%s', self.instr.id)
                self.instr_accrual = self.instr.find_accrual(self.report.report_date)
                # _l.debug('< instr_accrual: %s', self.instr_accrual)
                if self.instr_accrual:
                    # _l.debug('> instr_accrual_accrued_price: instr=%s', self.instr.id)
                    self.instr_accrual_accrued_price = self.instr.get_accrued_price(self.report.report_date,
                                                                                    accrual=self.instr_accrual)
                    # _l.debug('< instr_accrual_accrued_price: %s', self.instr_accrual_accrued_price)
            else:
                self.instr_principal_res = 0.0
                self.instr_accrued_res = 0.0

                self.instr_accrual = None
                self.instr_accrual_accrued_price = 0.0

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

            try:
                self.pos_return_res = (self.principal_opened_res + self.carry_opened_res) / \
                                      self.principal_invested_res / self.instr_pricing_ccy_cur_fx
            except ArithmeticError:
                self.pos_return_res = 0
            try:
                self.net_pos_return_res = (
                                              self.principal_opened_res + self.carry_opened_res + self.overheads_opened_res) / self.principal_invested_res
            except ArithmeticError:
                self.net_pos_return_res = 0.0

            if self.instr:
                # YTM/Duration - берем price из price history на дату репорта.
                # Для записка итеративного алгоритма, для x0 из accrued schedule
                # берем на текущую дату - (accrued_size * accrued_multiplier)/(price * price_multiplier).
                try:
                    future_accrual_payments = self.instr.get_future_accrual_payments(
                        d0=self.report.report_date,
                        v0=self.instr_price_cur_principal_price,
                        principal_ccy_fx=self.instr_pricing_ccy_cur_fx,
                        accrual_ccy_fx=self.instr_accrued_ccy_cur_fx
                    )
                except (ValueError, TypeError):
                    future_accrual_payments = False

                self.ytm = f_xirr(future_accrual_payments)

                self.modified_duration = f_duration(future_accrual_payments, ytm=self.ytm)

                # self.time_invested = self.time_invested_days / 365.0
                #
                # if self.time_invested_days < 1.0 or isclose(self.time_invested_days, 1.0):
                #     # T - report date
                #     #  = (Current Price - Gross Cost Price) / Gross Cost Price, if Time Invested in days= 1 day
                #     # self.pricing()
                #     try:
                #         self.daily_price_change = (
                #                                   self.instr_price_cur_principal_price - self.gross_cost_loc) / self.gross_cost_loc
                #     except ArithmeticError:
                #         self.daily_price_change = 0.0
                # else:
                #     #  = (Current Price at T -  Price from Price History at T-1) / (Price from Price History at T-1) , if Time Invested > 1 day
                #     price_yest = self.pricing_provider[self.instr, self.report.report_date - timedelta(days=1)]
                #     try:
                #         self.daily_price_change = (
                #                                   self.instr_price_cur_principal_price - price_yest.principal_price) / price_yest.principal_price
                #     except ArithmeticError:
                #         self.daily_price_change = 0.0
                #
                # if self.time_invested_days <= self.report.report_date.day or isclose(self.time_invested_days,
                #                                                                      self.report.report_date.day):
                #     # T - report date
                #     #  = (Current Price - Gross Cost Price) / Gross Cost Price, if Time Invested in days <= Day(Report Date)
                #     try:
                #         self.mtd_price_change = (
                #                                 self.instr_price_cur_principal_price - self.gross_cost_loc) / self.gross_cost_loc
                #     except ArithmeticError:
                #         self.mtd_price_change = 0.0
                # else:
                #     #  = (Current Price -  Price from Price History at end_of_previous_month (Report Date)) / (Price from Price History at end_of_previous_month (Report Date)) , if Time Invested > Day(Report Date)
                #     price_eom = self.pricing_provider[
                #         self.instr, self.report.report_date - timedelta(days=self.report.report_date.day)]
                #     try:
                #         self.mtd_price_change = (
                #                                 self.instr_price_cur_principal_price - price_eom.principal_price) / price_eom.principal_price
                #     except ArithmeticError:
                #         self.mtd_price_change = 0.0

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

        # values in pricing ccy ---

        try:
            res_to_loc_fx = 1.0 / self.pricing_ccy_cur_fx
        except ArithmeticError:
            res_to_loc_fx = 0.0

        self.market_value_loc = self.market_value_res * res_to_loc_fx
        self.exposure_loc = self.exposure_res * res_to_loc_fx
        self.gross_cost_res = -self.gross_cost_res
        self.gross_cost_loc = self.gross_cost_res * res_to_loc_fx
        self.net_cost_res = -self.net_cost_res
        self.net_cost_loc = self.net_cost_res * res_to_loc_fx
        self.principal_invested_loc = self.principal_invested_res * res_to_loc_fx
        self.amount_invested_loc = self.amount_invested_res * res_to_loc_fx
        self.pos_return_loc = self.pos_return_res * res_to_loc_fx
        self.net_pos_return_loc = self.net_pos_return_res * res_to_loc_fx

        # p & l

        self.principal_loc = self.principal_res * res_to_loc_fx
        self.carry_loc = self.carry_res * res_to_loc_fx
        self.overheads_loc = self.overheads_res * res_to_loc_fx
        self.total_loc = self.total_res * res_to_loc_fx

        self.principal_closed_loc = self.principal_closed_res * res_to_loc_fx
        self.carry_closed_loc = self.carry_closed_res * res_to_loc_fx
        self.overheads_closed_loc = self.overheads_closed_res * res_to_loc_fx
        self.total_closed_loc = self.total_closed_res * res_to_loc_fx

        self.principal_opened_loc = self.principal_opened_res * res_to_loc_fx
        self.carry_opened_loc = self.carry_opened_res * res_to_loc_fx
        self.overheads_opened_loc = self.overheads_opened_res * res_to_loc_fx
        self.total_opened_loc = self.total_opened_res * res_to_loc_fx

        self.principal_fx_loc = self.principal_fx_res * res_to_loc_fx
        self.carry_fx_loc = self.carry_fx_res * res_to_loc_fx
        self.overheads_fx_loc = self.overheads_fx_res * res_to_loc_fx
        self.total_fx_loc = self.total_fx_res * res_to_loc_fx

        self.principal_fx_closed_loc = self.principal_fx_closed_res * res_to_loc_fx
        self.carry_fx_closed_loc = self.carry_fx_closed_res * res_to_loc_fx
        self.overheads_fx_closed_loc = self.overheads_fx_closed_res * res_to_loc_fx
        self.total_fx_closed_loc = self.total_fx_closed_res * res_to_loc_fx

        self.principal_fx_opened_loc = self.principal_fx_opened_res * res_to_loc_fx
        self.carry_fx_opened_loc = self.carry_fx_opened_res * res_to_loc_fx
        self.overheads_fx_opened_loc = self.overheads_fx_opened_res * res_to_loc_fx
        self.total_fx_opened_loc = self.total_fx_opened_res * res_to_loc_fx

        self.principal_fixed_loc = self.principal_fixed_res * res_to_loc_fx
        self.carry_fixed_loc = self.carry_fixed_res * res_to_loc_fx
        self.overheads_fixed_loc = self.overheads_fixed_res * res_to_loc_fx
        self.total_fixed_loc = self.total_fixed_res * res_to_loc_fx

        self.principal_fixed_closed_loc = self.principal_fixed_closed_res * res_to_loc_fx
        self.carry_fixed_closed_loc = self.carry_fixed_closed_res * res_to_loc_fx
        self.overheads_fixed_closed_loc = self.overheads_fixed_closed_res * res_to_loc_fx
        self.total_fixed_closed_loc = self.total_fixed_closed_res * res_to_loc_fx

        self.principal_fixed_opened_loc = self.principal_fixed_opened_res * res_to_loc_fx
        self.carry_fixed_opened_loc = self.carry_fixed_opened_res * res_to_loc_fx
        self.overheads_fixed_opened_loc = self.overheads_fixed_opened_res * res_to_loc_fx
        self.total_fixed_opened_loc = self.total_fixed_opened_res * res_to_loc_fx

        # ----

        if self.type == ReportItem.TYPE_CURRENCY:
            self.is_empty = isclose(self.pos_size, 0.0)

        elif self.type == ReportItem.TYPE_INSTRUMENT:
            self.is_empty = isclose(self.pos_size, 0.0) and \
                            isclose(self.total_res, 0.0) and \
                            isclose(self.total_closed_res, 0.0) and \
                            isclose(self.total_opened_res, 0.0)

    def close_pass2(self):
        if self.type == ReportItem.TYPE_INSTRUMENT:
            self.time_invested = self.time_invested_days / 365.0

            if self.time_invested_days < 1.0 or isclose(self.time_invested_days, 1.0):
                # T - report date
                #  = (Current Price - Gross Cost Price) / Gross Cost Price, if Time Invested in days= 1 day
                # self.pricing()
                try:
                    self.daily_price_change = (
                                                  self.instr_price_cur_principal_price - self.gross_cost_loc) / self.gross_cost_loc
                except ArithmeticError:
                    self.daily_price_change = 0.0
            else:
                #  = (Current Price at T -  Price from Price History at T-1) / (Price from Price History at T-1) , if Time Invested > 1 day
                price_yest = self.pricing_provider[self.instr, self.report.report_date - timedelta(days=1)]
                try:
                    self.daily_price_change = (
                                                  self.instr_price_cur_principal_price - price_yest.principal_price) / price_yest.principal_price
                except ArithmeticError:
                    self.daily_price_change = 0.0

            if self.time_invested_days <= self.report.report_date.day or isclose(self.time_invested_days,
                                                                                 self.report.report_date.day):
                # T - report date
                #  = (Current Price - Gross Cost Price) / Gross Cost Price, if Time Invested in days <= Day(Report Date)
                try:
                    self.mtd_price_change = (
                                                self.instr_price_cur_principal_price - self.gross_cost_loc) / self.gross_cost_loc
                except ArithmeticError:
                    self.mtd_price_change = 0.0
            else:
                #  = (Current Price -  Price from Price History at end_of_previous_month (Report Date)) / (Price from Price History at end_of_previous_month (Report Date)) , if Time Invested > Day(Report Date)
                price_eom = self.pricing_provider[
                    self.instr, self.report.report_date - timedelta(days=self.report.report_date.day)]
                try:
                    self.mtd_price_change = (
                                                self.instr_price_cur_principal_price - price_eom.principal_price) / price_eom.principal_price
                except ArithmeticError:
                    self.mtd_price_change = 0.0

    def pl_sub_item(self, o):
        self.principal_res -= o.principal_res
        self.carry_res -= o.carry_res
        self.overheads_res -= o.overheads_res
        self.total_res -= o.total_res

        self.principal_closed_res -= o.principal_closed_res
        self.carry_closed_res -= o.carry_closed_res
        self.overheads_closed_res -= o.overheads_closed_res
        self.total_closed_res -= o.total_closed_res

        self.principal_opened_res -= o.principal_opened_res
        self.carry_opened_res -= o.carry_opened_res
        self.overheads_opened_res -= o.overheads_opened_res
        self.total_opened_res -= o.total_opened_res

        self.principal_fx_res -= o.principal_fx_res
        self.carry_fx_res -= o.carry_fx_res
        self.overheads_fx_res -= o.overheads_fx_res
        self.total_fx_res -= o.total_fx_res

        self.principal_fx_closed_res -= o.principal_fx_closed_res
        self.carry_fx_closed_res -= o.carry_fx_closed_res
        self.overheads_fx_closed_res -= o.overheads_fx_closed_res
        self.total_fx_closed_res -= o.total_fx_closed_res

        self.principal_fx_opened_res -= o.principal_fx_opened_res
        self.carry_fx_opened_res -= o.carry_fx_opened_res
        self.overheads_fx_opened_res -= o.overheads_fx_opened_res
        self.total_fx_opened_res -= o.total_fx_opened_res

        self.principal_fixed_res -= o.principal_fixed_res
        self.carry_fixed_res -= o.carry_fixed_res
        self.overheads_fixed_res -= o.overheads_fixed_res
        self.total_fixed_res -= o.total_fixed_res

        self.principal_fixed_closed_res -= o.principal_fixed_closed_res
        self.carry_fixed_closed_res -= o.carry_fixed_closed_res
        self.overheads_fixed_closed_res -= o.overheads_fixed_closed_res
        self.total_fixed_closed_res -= o.total_fixed_closed_res

        self.principal_fixed_opened_res -= o.principal_fixed_opened_res
        self.carry_fixed_opened_res -= o.carry_fixed_opened_res
        self.overheads_fixed_opened_res -= o.overheads_fixed_opened_res
        self.total_fixed_opened_res -= o.total_fixed_opened_res

    # ----------------------------------------------------
    @property
    def pk(self):
        return (
            self.type,
            getattr(self.prtfl, 'id', -1),
            getattr(self.acc, 'id', -1),
            getattr(self.instr, 'id', -1),
            getattr(self.ccy, 'id', -1),
            getattr(self.mismatch_prtfl, 'id', -1),
            getattr(self.mismatch_acc, 'id', -1),
        )

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
    def subtype_name(self):
        for i, n in ReportItem.SUBTYPE_CHOICES:
            if i == self.subtype:
                return n
        return 'ERR'

    @property
    def subtype_code(self):
        if self.subtype == ReportItem.SUBTYPE_UNKNOWN:
            return 'UNKNOWN'

        elif self.subtype == ReportItem.SUBTYPE_TOTAL:
            return 'TOTAL'

        elif self.subtype == ReportItem.SUBTYPE_CLOSED:
            return 'CLOSED'

        elif self.subtype == ReportItem.SUBTYPE_OPENED:
            return 'OPENED'

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
            # return 'TRANSACTION_PL'
            return self.notes

        elif self.type == ReportItem.TYPE_FX_TRADE:
            # return 'FX_TRADE'
            # return '%s/%s' % (getattr(self.trn_ccy, 'user_code', None), getattr(self.ccy, 'user_code', None),)
            return self.notes

        elif self.type == ReportItem.TYPE_CASH_IN_OUT:
            # return 'CASH_IN_OUT'
            # return getattr(self.ccy, 'user_code', None)
            return self.notes

        elif self.type == ReportItem.TYPE_MISMATCH:
            return getattr(self.instr, 'user_code', None)

        elif self.type == ReportItem.TYPE_SUMMARY:
            return 'SUMMARY'

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
            # return ugettext('Transaction PL')
            return self.notes

        elif self.type == ReportItem.TYPE_FX_TRADE:
            # return ugettext('FX-Trade')
            # return ugettext('FX-Trades: %s/%s') % (getattr(self.trn_ccy, 'short_name', None),
            #                                        getattr(self.ccy, 'short_name', None),)
            return self.notes

        elif self.type == ReportItem.TYPE_CASH_IN_OUT:
            # return ugettext('Cash In/Out: %s/%s')
            # return ugettext('Cash In/Out: %s') % getattr(self.ccy, 'short_name', None)
            return self.notes

        elif self.type == ReportItem.TYPE_MISMATCH:
            return getattr(self.instr, 'short_name', None)

        elif self.type == ReportItem.TYPE_SUMMARY:
            return ugettext('Summary')

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
            # return ugettext('Transaction PL')
            return self.notes

        elif self.type == ReportItem.TYPE_FX_TRADE:
            # return ugettext('FX-Trade')
            # return ugettext('FX-Trades: %s/%s') % (
            #     getattr(self.trn_ccy, 'name', None), getattr(self.ccy, 'name', None),)
            return self.notes

        elif self.type == ReportItem.TYPE_CASH_IN_OUT:
            # return ugettext('Cash In/Out: %s/%s')
            # return ugettext('Cash In/Out: %s') % getattr(self.ccy, 'name', None)
            return self.notes

        elif self.type == ReportItem.TYPE_MISMATCH:
            return getattr(self.instr, 'name', None)

        elif self.type == ReportItem.TYPE_SUMMARY:
            return ugettext('Summary')

        return '<ERROR>'

    @property
    def trn_cls(self):
        return getattr(self.trn, 'trn_cls', None)

    @property
    def detail_trn(self):
        if self.trn and self.acc and self.trn.is_show_details(self.acc):
            return self.trn
        return None

    def eval_custom_fields(self):
        res = []
        for cf in self.report.custom_fields:
            if cf.expr and self.report.member:
                try:
                    names = {
                        'item': self
                    }
                    value = formula.safe_eval(cf.expr, names=names, context=self.report.context)
                except formula.InvalidExpression:
                    value = ugettext('Invalid expression')
            else:
                value = None
            res.append({
                'custom_field': cf,
                'value': value
            })
        self.custom_fields = res

    def overwrite_pl_fields_by_subtype(self):
        if self.subtype == ReportItem.SUBTYPE_TOTAL:
            pass

        elif self.subtype == ReportItem.SUBTYPE_CLOSED:
            for sitem, ditem in self.pl_closed_fields:
                if ditem is None:
                    ditem = str(sitem).replace('closed_', '')
                val = getattr(self, sitem)
                setattr(self, ditem, val)

        elif self.subtype == ReportItem.SUBTYPE_OPENED:
            for sitem, ditem in self.pl_opened_fields:
                if ditem is None:
                    ditem = str(sitem).replace('opene_', '')
                val = getattr(self, sitem)
                setattr(self, ditem, val)

        for sitem, ditem in self.pl_closed_fields:
            setattr(self, sitem, float('nan'))

        for sitem, ditem in self.pl_opened_fields:
            setattr(self, sitem, float('nan'))


class Report(object):
    TYPE_BALANCE = 1
    TYPE_PL = 2
    TYPE_CHOICES = (
        (TYPE_BALANCE, 'Balance'),
        (TYPE_PL, 'P&L'),
    )

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
                 pl_first_date=None,
                 report_type=TYPE_BALANCE,
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
                 allocation_detailing=True,
                 instruments=None,
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
        self.context = {
            'master_user': self.master_user,
            'member': self.member,
        }
        self.pricing_policy = pricing_policy
        self.pl_first_date = pl_first_date
        self.report_type = report_type if report_type is not None else Report.TYPE_BALANCE
        self.report_date = report_date or (date_now() - timedelta(days=1))
        self.report_currency = report_currency or master_user.system_currency
        self.cost_method = cost_method or CostMethod.objects.get(pk=CostMethod.AVCO)

        self.portfolio_mode = portfolio_mode
        self.account_mode = account_mode
        self.strategy1_mode = strategy1_mode
        self.strategy2_mode = strategy2_mode
        self.strategy3_mode = strategy3_mode
        # self.alloc_mode = alloc_mode
        self.show_transaction_details = show_transaction_details
        self.approach_multiplier = approach_multiplier
        self.allocation_detailing = allocation_detailing

        self.instruments = instruments or []
        self.portfolios = portfolios or []
        self.accounts = accounts or []
        self.strategies1 = strategies1 or []
        self.strategies2 = strategies2 or []
        self.strategies3 = strategies3 or []
        self.transaction_classes = transaction_classes or []
        # self.date_field = date_field or 'transaction_date'
        if date_field:
            self.date_field = date_field
        else:
            if self.report_type == Report.TYPE_BALANCE:
                self.date_field = 'transaction_date'
            elif self.report_type == Report.TYPE_PL:
                self.date_field = 'accounting_date'
            else:
                self.date_field = 'transaction_date'

        self.custom_fields = custom_fields or []

        self.items = items or []
        self.transactions = []

        self.item_instruments = []
        self.item_currencies = []
        self.item_portfolios = []
        self.item_accounts = []
        self.item_strategies1 = []
        self.item_strategies2 = []
        self.item_strategies3 = []
        self.item_currency_fx_rates = []
        self.item_instrument_pricings = []
        self.item_instrument_accruals = []

    def __str__(self):
        return "%s for %s/%s @ %s" % (self.__class__.__name__, self.master_user, self.member, self.report_date)

    def close(self):
        for item in self.items:
            item.eval_custom_fields()

        item_instruments = {}
        item_currencies = {}
        item_portfolios = {}
        item_accounts = {}
        item_strategies1 = {}
        item_strategies2 = {}
        item_strategies3 = {}
        item_currency_fx_rates = {}
        item_instrument_pricings = {}
        item_instrument_accruals = {}

        for item in self.items:
            if item.instr:
                item_instruments[item.instr.id] = item.instr
            if item.ccy:
                item_currencies[item.ccy.id] = item.ccy
            if item.prtfl:
                item_portfolios[item.prtfl.id] = item.prtfl
            if item.acc:
                item_accounts[item.acc.id] = item.acc
            if item.str1:
                item_strategies1[item.str1.id] = item.str1
            if item.str2:
                item_strategies2[item.str2.id] = item.str2
            if item.str3:
                item_strategies3[item.str3.id] = item.str3
            if item.mismatch_prtfl:
                item_portfolios[item.mismatch_prtfl.id] = item.mismatch_prtfl
            if item.mismatch_acc:
                item_accounts[item.mismatch_acc.id] = item.mismatch_acc
            if item.alloc:
                item_instruments[item.alloc.id] = item.alloc
            if item.report_ccy_cur:
                item_currency_fx_rates[item.report_ccy_cur.id] = item.report_ccy_cur
            if item.instr_price_cur:
                item_instrument_pricings[item.instr_price_cur.id] = item.instr_price_cur
            if item.instr_pricing_ccy_cur:
                item_currency_fx_rates[item.instr_pricing_ccy_cur.id] = item.instr_pricing_ccy_cur
            if item.instr_accrued_ccy_cur:
                item_currency_fx_rates[item.instr_accrued_ccy_cur.id] = item.instr_accrued_ccy_cur
            if item.ccy_cur:
                item_currency_fx_rates[item.ccy_cur.id] = item.ccy_cur
            if item.pricing_ccy_cur:
                item_currency_fx_rates[item.pricing_ccy_cur.id] = item.pricing_ccy_cur
            if item.instr_accrual:
                item_instrument_accruals[item.instr_accrual.id] = item.instr_accrual

        self.item_instruments = list(item_instruments.values())
        self.item_currencies = list(item_currencies.values())
        self.item_portfolios = list(item_portfolios.values())
        self.item_accounts = list(item_accounts.values())
        self.item_strategies1 = list(item_strategies1.values())
        self.item_strategies2 = list(item_strategies2.values())
        self.item_strategies3 = list(item_strategies3.values())
        self.item_currency_fx_rates = list(item_currency_fx_rates.values())
        self.item_instrument_pricings = list(item_instrument_pricings.values())
        self.item_instrument_accruals = list(item_instrument_accruals.values())

    @property
    def report_type_str(self):
        if self.report_type == Report.TYPE_BALANCE:
            return "BALANCE"
        elif self.report_type == Report.TYPE_PL:
            return "P&L"
        return "<UNKNOWN>"

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
