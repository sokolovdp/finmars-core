import uuid
from collections import OrderedDict
from datetime import timedelta, date
from itertools import groupby

from poms.common.utils import date_now, isclose
from poms.reports.builders.base_item import BaseReport


class PerformancePeriod:
    def __init__(self, report, period_begin=None, period_end=None, period_name=None, period_key=None):
        self.report = report
        self.period_begin = period_begin
        self.period_end = period_end
        self.period_name = period_name
        self.period_key = period_key

        self.local_trns = []
        self.trns = []

        # self.items = []
        # self.items_nav0 = []
        # self.items_nav1 = []
        # self.items_pls = []

        self._items = OrderedDict()

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return 'Period({}/{},local_trns={},trns={},items={})'.format(
            self.period_begin, self.period_end, len(self.local_trns), len(self.trns), len(self._items))

    @property
    def items(self):
        return self._items.values()

    def get(self, portfolio=None, account=None, strategy1=None, strategy2=None, strategy3=None):
        key = PerformanceReportItem.make_group_key(
            self.report,
            period_key=self.period_key,
            portfolio=portfolio,
            account=account,
            strategy1=strategy1,
            strategy2=strategy2,
            strategy3=strategy3
        )
        try:
            return self._items[key]
        except KeyError:
            item = PerformanceReportItem(
                self.report,
                id=str(uuid.uuid4()),
                period_begin=self.period_begin,
                period_end=self.period_end,
                period_name=self.period_name,
                period_key=self.period_key,
                portfolio=portfolio,
                account=account,
                strategy1=strategy1,
                strategy2=strategy2,
                strategy3=strategy3
            )
            self._items[key] = item
            return item

    def get_by_trn_pos(self, trn):
        return self.get(
            portfolio=trn.prtfl,
            account=trn.acc_pos,
            strategy1=trn.str1_pos,
            strategy2=trn.str2_pos,
            strategy3=trn.str3_pos
        )

    def get_by_trn_cash(self, trn, interim=False):
        return self.get(
            portfolio=trn.prtfl,
            account=trn.acc_cash if not interim else trn.acc_interim,
            strategy1=trn.str1_cash,
            strategy2=trn.str2_cash,
            strategy3=trn.str3_cash
        )

    def nav_add(self, trn):
        is_nav_period_start = trn.period_key < self.period_key

        if trn.case == 0:
            if not isclose(trn.instr_mkt_val_res, 0):
                item = self.get_by_trn_pos(trn)
                if is_nav_period_start:
                    item.nav_period_start += trn.instr_mkt_val_res
                item.nav_period_end += trn.instr_mkt_val_res

            if not isclose(trn.cash_mkt_val_res, 0):
                item = self.get_by_trn_cash(trn, interim=False)
                if is_nav_period_start:
                    item.nav_period_start += trn.cash_mkt_val_res
                item.nav_period_end += trn.cash_mkt_val_res

        elif trn.case == 1:
            if not isclose(trn.instr_mkt_val_res, 0):
                item = self.get_by_trn_pos(trn)
                if is_nav_period_start:
                    item.nav_period_start += trn.instr_mkt_val_res
                item.nav_period_end += trn.instr_mkt_val_res

            if not isclose(trn.cash_mkt_val_res, 0):
                item = self.get_by_trn_cash(trn, interim=True)
                if is_nav_period_start:
                    item.nav_period_start += trn.cash_mkt_val_res
                item.nav_period_end += trn.cash_mkt_val_res

        elif trn.case == 2:
            if not isclose(trn.instr_mkt_val_res, 0):
                pass

            if not isclose(trn.cash_mkt_val_res, 0):
                item = self.get_by_trn_cash(trn, interim=False)
                if is_nav_period_start:
                    item.nav_period_start += trn.cash_mkt_val_res
                item.nav_period_end += trn.cash_mkt_val_res

                item = self.get_by_trn_cash(trn, interim=True)
                if is_nav_period_start:
                    item.nav_period_start += -trn.cash_mkt_val_res
                item.nav_period_end += -trn.cash_mkt_val_res

    # def pl_add(self, trn):
    #     if trn.case == 0 or trn.case == 1:
    #         item = self.get_by_trn_pos(trn)
    #
    #         item.cash_res += trn.cash_res
    #         item.principal_res += trn.principal_res
    #         item.carry_res += trn.carry_res
    #         item.overheads_res += trn.overheads_res
    #         item.total_res += trn.total_res
    #
    #     elif trn.case == 2:
    #         pass
    #
    #     else:
    #         raise RuntimeError('Invalid transaction case: %s' % trn.case)

    def cash_in_out_add(self, trn):
        cash_item = self.get_by_trn_cash(trn, interim=False)
        pos_item = self.get_by_trn_pos(trn)

        cash_proceed = trn.total_res

        cash_item.cash_inflows += cash_proceed
        cash_item.time_weighted_cash_inflows += cash_proceed * trn.period_time_weight

        cash_item.cash_outflows += cash_proceed
        cash_item.time_weighted_cash_outflows += cash_proceed * trn.period_time_weight

        pos_item.cash_inflows += -cash_proceed
        pos_item.time_weighted_cash_inflows += -cash_proceed * trn.period_time_weight

        pos_item.cash_outflows += -cash_proceed
        pos_item.time_weighted_cash_outflows += -cash_proceed * trn.period_time_weight

    def close(self, prev_period):
        for item in self._items.values():
            item.close()


class PerformanceReportItem:
    # TYPE_DEFAULT = 0
    # TYPE_MKT_VAL = 1
    # TYPE_PL = 2

    def __init__(self, report, id=None,
                 period_begin=None, period_end=None, period_name=None, period_key=None,
                 portfolio=None, account=None, strategy1=None, strategy2=None, strategy3=None):
        self.report = report
        self.id = str(id) if id is not None else ''

        # self.item_type = item_type if item_type is not None else PerformanceReportItem.TYPE_DEFAULT

        self.period_begin = period_begin
        self.period_end = period_end
        self.period_name = period_name
        self.period_key = period_key
        self.portfolio = portfolio
        self.account = account
        self.strategy1 = strategy1
        self.strategy2 = strategy2
        self.strategy3 = strategy3

        # temporal fields
        self.acc_date = date.min
        self.processing_date = date.min
        self.instr_principal_res = 0
        self.instr_accrued_res = 0
        self.cash_res = 0
        self.principal_res = 0
        self.carry_res = 0
        self.overheads_res = 0
        self.total_res = 0
        self.mkt_val_res = 0
        self.global_time_weight = 0
        self.period_time_weight = 0

        # final fields
        self.return_pl = 0
        self.return_nav = 0
        self.pl_in_period = 0
        self.nav_change = 0
        self.nav_period_start = 0
        self.nav_period_end = 0
        self.cash_inflows = 0
        self.cash_outflows = 0
        self.time_weighted_cash_inflows = 0
        self.time_weighted_cash_outflows = 0
        self.avg_nav_in_period = 0
        self.cumulative_return_pl = 0
        self.cumulative_return_nav = 0

        self.custom_fields = []

    @classmethod
    def from_trn(cls, trn, item_type=None, portfolio=None, account=None, strategy1=None, strategy2=None,
                 strategy3=None):
        ret = cls(
            trn.report,
            id=-1,
            item_type=item_type,
            period_begin=trn.period_begin,
            period_end=trn.period_end,
            period_name=trn.period_name,
            period_key=trn.period_key,
            portfolio=portfolio,
            account=account,
            strategy1=strategy1,
            strategy2=strategy2,
            strategy3=strategy3
        )
        ret.acc_date = trn.acc_date
        ret.processing_date = trn.processing_date
        ret.instr_principal_res = trn.instr_principal_res
        ret.instr_accrued_res = trn.instr_accrued_res
        ret.cash_res = trn.cash_res
        ret.principal_res = trn.principal_res
        ret.carry_res = trn.carry_res
        ret.overheads_res = trn.overheads_res
        ret.total_res = trn.total_res
        ret.global_time_weight = trn.global_time_weight
        ret.period_time_weight = trn.period_time_weight
        return ret

    @classmethod
    def from_item(cls, item, id=None, item_type=None):
        ret = cls(
            item.report,
            id=id if id is not None else item.id,
            item_type=item_type if item_type is not None else item.item_type,
            period_begin=item.period_begin,
            period_end=item.period_end,
            period_name=item.period_name,
            period_key=item.period_key,
            portfolio=item.portfolio,
            account=item.account,
            strategy1=item.strategy1,
            strategy2=item.strategy2,
            strategy3=item.strategy3
        )
        return ret

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return 'Item({}/{},prtfl={},acc={},str1={},str2={},str3={})'.format(
            self.period_begin, self.period_end, getattr(self.portfolio, 'id', -1), getattr(self.account, 'id', -1),
            getattr(self.strategy1, 'id', -1), getattr(self.strategy2, 'id', -1), getattr(self.strategy3, 'id', -1), )

    @staticmethod
    def make_group_key(report, period_key=None, portfolio=None, account=None,
                       strategy1=None, strategy2=None, strategy3=None):
        # return (
        #     self.period_key,
        #     self.portfolio.id,
        #     self.account.id,
        #     self.strategy1.id,
        #     self.strategy2.id,
        #     self.strategy3.id
        # )
        if report.portfolio_mode == PerformanceReport.MODE_INDEPENDENT:
            pass
        else:
            portfolio = None

        if report.account_mode == PerformanceReport.MODE_INDEPENDENT:
            pass
        else:
            account = None

        if report.strategy1_mode == PerformanceReport.MODE_INDEPENDENT:
            pass
        else:
            strategy1 = None

        if report.strategy2_mode == PerformanceReport.MODE_INDEPENDENT:
            pass
        else:
            strategy2 = None

        if report.strategy3_mode == PerformanceReport.MODE_INDEPENDENT:
            pass
        else:
            strategy3 = None

        return (
            period_key,
            getattr(portfolio, 'id', -1),
            getattr(account, 'id', -1),
            getattr(strategy1, 'id', -1),
            getattr(strategy2, 'id', -1),
            getattr(strategy3, 'id', -1),
        )

    @property
    def group_key(self):
        # return (
        #     self.period_key,
        #     self.portfolio.id,
        #     self.account.id,
        #     self.strategy1.id,
        #     self.strategy2.id,
        #     self.strategy3.id
        # )
        # if self.report.portfolio_mode == PerformanceReport.MODE_INDEPENDENT:
        #     portfolio = self.portfolio
        # else:
        #     portfolio = None
        #
        # if self.report.account_mode == PerformanceReport.MODE_INDEPENDENT:
        #     account = self.account
        # else:
        #     account = None
        #
        # if self.report.strategy1_mode == PerformanceReport.MODE_INDEPENDENT:
        #     strategy1 = self.strategy1
        # else:
        #     strategy1 = None
        #
        # if self.report.strategy2_mode == PerformanceReport.MODE_INDEPENDENT:
        #     strategy2 = self.strategy2
        # else:
        #     strategy2 = None
        #
        # if self.report.strategy3_mode == PerformanceReport.MODE_INDEPENDENT:
        #     strategy3 = self.strategy3
        # else:
        #     strategy3 = None
        #
        # return (
        #     self.period_key,
        #     getattr(portfolio, 'id', -1),
        #     getattr(account, 'id', -1),
        #     getattr(strategy1, 'id', -1),
        #     getattr(strategy2, 'id', -1),
        #     getattr(strategy3, 'id', -1),
        # )
        return PerformanceReportItem.make_group_key(
            self.report,
            period_key=self.period_key,
            portfolio=self.portfolio,
            account=self.account,
            strategy1=self.strategy1,
            strategy2=self.strategy2,
            strategy3=self.strategy3
        )

    # def add(self, item):
    #     if self.item_type == self.TYPE_DEFAULT:
    #         pass
    #
    #     elif self.item_type == self.TYPE_MKT_VAL:
    #         self.mkt_val_res += item.mkt_val_res
    #
    #         self.instr_principal_res += item.instr_principal_res
    #         self.instr_accrued_res += item.instr_accrued_res
    #
    #     elif self.item_type == self.TYPE_PL:
    #         self.cash_res += item.cash_res
    #         self.principal_res += item.principal_res
    #         self.carry_res += item.carry_res
    #         self.overheads_res += item.overheads_res
    #         self.total_res += item.total_res

    def calc(self):
        # try:
        #     self.global_time_weight = (self.report.end_date - self.acc_date).days / \
        #                               (self.report.end_date - self.report.begin_date).days
        # except ArithmeticError:
        #     self.global_time_weight = 0
        #
        # try:
        #     self.period_time_weight = (self.period_end - self.acc_date).days / \
        #                               (self.period_end - self.period_begin).days
        # except ArithmeticError:
        #     self.period_time_weight = 0
        pass

    def set_as_cash(self, trn):
        self.cash_inflows = trn.total_res

    def set_as_pos(self, trn):
        self.cash_inflows = -trn.total_res

    def close(self):
        # self.return_pl = 0

        try:
            self.return_nav = self.nav_change / self.avg_nav_in_period
        except ArithmeticError:
            self.return_nav = 0

        # self.pl_in_period = 0

        self.nav_change = (self.nav_period_end - self.nav_period_start) + \
                          (self.cash_outflows - self.cash_inflows)

        # self.nav_period_start = 0

        # self.nav_period_end = 0

        # self.cash_inflows = 0

        # self.cash_outflows = 0

        # self.time_weighted_cash_inflows = 0

        # self.time_weighted_cash_outflows = 0

        self.avg_nav_in_period = self.nav_period_start + \
                                 (self.time_weighted_cash_inflows - self.time_weighted_cash_outflows)

        # self.cumulative_return_pl = 0

        # self.cumulative_return_nav = 0
        pass

    def random(self):
        from random import random

        self.return_pl = random()
        self.return_nav = random()
        self.pl_in_period = random()
        self.nav_change = random()
        self.nav_period_start = random()
        self.nav_period_end = random()
        self.cash_inflows = random()
        self.cash_outflows = random()
        self.time_weighted_cash_inflows = random()
        self.time_weighted_cash_outflows = random()
        self.avg_nav_in_period = random()
        self.cumulative_return_pl = random()
        self.cumulative_return_nav = random()

    def eval_custom_fields(self):
        # use optimization inside serialization
        res = []
        self.custom_fields = res


class PerformanceReport(BaseReport):
    report_type = 0  # VirtualTransaction
    report_date = date.min  # VirtualTransaction

    def __init__(self,
                 id=None,
                 task_id=None,
                 task_status=None,
                 master_user=None,
                 member=None,
                 begin_date=None,
                 end_date=None,
                 report_currency=None,
                 pricing_policy=None,
                 periods=None,
                 portfolio_mode=BaseReport.MODE_INDEPENDENT,
                 account_mode=BaseReport.MODE_INDEPENDENT,
                 strategy1_mode=BaseReport.MODE_INDEPENDENT,
                 strategy2_mode=BaseReport.MODE_INDEPENDENT,
                 strategy3_mode=BaseReport.MODE_INDEPENDENT,
                 portfolios=None,
                 accounts=None,
                 accounts_position=None,
                 accounts_cash=None,
                 strategies1=None,
                 strategies2=None,
                 strategies3=None,
                 custom_fields=None,
                 items=None):
        super(PerformanceReport, self).__init__(id=id, master_user=master_user, member=member,
                                                task_id=task_id, task_status=task_status)

        self.has_errors = False

        d = date_now() - timedelta(days=1)
        self.begin_date = begin_date or date(d.year, 1, 1)
        # self.begin_date = date.min
        self.end_date = end_date or d
        self.report_currency = report_currency or master_user.system_currency
        self.pricing_policy = pricing_policy
        self.periods = periods
        self.portfolio_mode = portfolio_mode
        self.account_mode = account_mode
        self.strategy1_mode = strategy1_mode
        self.strategy2_mode = strategy2_mode
        self.strategy3_mode = strategy3_mode
        self.portfolios = portfolios or []
        self.accounts = accounts or []
        self.accounts_position = accounts_position or []
        self.accounts_cash = accounts_cash or []
        self.strategies1 = strategies1 or []
        self.strategies2 = strategies2 or []
        self.strategies3 = strategies3 or []
        self.custom_fields = custom_fields or []

        self.items = items
        self.item_portfolios = []
        self.item_accounts = []
        self.item_strategies1 = []
        self.item_strategies2 = []
        self.item_strategies3 = []

    def __str__(self):
        return 'PerformanceReport:%s' % self.id

    def close(self):
        for item in self.items:
            item.eval_custom_fields()
