from datetime import timedelta, date

from poms.common.utils import date_now


class PerformanceReportItem:
    def __init__(self,
                 report,
                 ):
        self.report = report
        self.id = None

        self.custom_fields = []

    def __str__(self):
        return 'PerformanceReportItem:%s' % self.id

    def eval_custom_fields(self):
        # use optimization inside serialization
        res = []
        self.custom_fields = res


class PerformanceReport:
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
                 portfolios=None,
                 accounts=None,
                 accounts_position=None,
                 accounts_cash=None,
                 strategies1=None,
                 strategies2=None,
                 strategies3=None,
                 custom_fields=None,
                 items=None):
        self.has_errors = False
        self.id = id
        self.task_id = task_id
        self.task_status = task_status
        self.master_user = master_user
        self.member = member
        self.begin_date = begin_date or date.min
        self.end_date = end_date or (date_now() - timedelta(days=1))
        self.report_currency = report_currency or master_user.system_currency
        self.pricing_policy = pricing_policy
        self.periods = periods
        self.portfolios = portfolios or []
        self.accounts = accounts or []
        self.accounts_position = accounts_position or []
        self.accounts_cash = accounts_cash or []
        self.strategies1 = strategies1 or []
        self.strategies2 = strategies2 or []
        self.strategies3 = strategies3 or []
        self.custom_fields = custom_fields or []

        self.context = {
            'master_user': self.master_user,
            'member': self.member,
        }

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

