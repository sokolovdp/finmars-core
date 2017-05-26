from datetime import timedelta, date

from random import random

from poms.common.utils import date_now
from poms.reports.builders.base_item import BaseReport


class PerformanceReportItem:
    def __init__(self,
                 report,
                 portfolio=None,
                 account=None,
                 strategy1=None,
                 strategy2=None,
                 strategy3=None,
                 ):
        self.report = report
        self.id = None

        self.portfolio = portfolio
        self.account = account
        self.strategy1 = strategy1
        self.strategy2 = strategy2
        self.strategy3 = strategy3

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

        self.custom_fields = []

    def __str__(self):
        return 'PerformanceReportItem:%s' % self.id

    def eval_custom_fields(self):
        # use optimization inside serialization
        res = []
        self.custom_fields = res


class PerformanceReport(BaseReport):
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

        self.begin_date = begin_date or date.min
        self.end_date = end_date or (date_now() - timedelta(days=1))
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
