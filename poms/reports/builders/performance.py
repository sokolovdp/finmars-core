import time
import logging

from django.db import transaction

from poms.reports.builders.base_builder import BaseReportBuilder
from poms.reports.builders.performance_item import PerformanceReportItem

_l = logging.getLogger('poms.reports')


class PerformanceReportBuilder(BaseReportBuilder):
    def __init__(self, instance):
        self.instance = instance

    def build(self):
        st = time.perf_counter()
        _l.debug('build transaction')

        with transaction.atomic():
            try:
                self.instance.items = [
                    PerformanceReportItem(
                        self.instance,
                        portfolio=self.instance.master_user.portfolio,
                        account=self.instance.master_user.account,
                        strategy1=self.instance.master_user.strategy1,
                        strategy2=self.instance.master_user.strategy2,
                        strategy3=self.instance.master_user.strategy3,
                    )
                ]
                self.instance.item_portfolios = [self.instance.master_user.portfolio, ]
                self.instance.item_accounts = [self.instance.master_user.account, ]
                self.instance.item_strategies1 = [self.instance.master_user.strategy1, ]
                self.instance.item_strategies2 = [self.instance.master_user.strategy2, ]
                self.instance.item_strategies3 = [self.instance.master_user.strategy3, ]
            finally:
                transaction.set_rollback(True)

        _l.debug('done: %s', (time.perf_counter() - st))
        return self.instance
