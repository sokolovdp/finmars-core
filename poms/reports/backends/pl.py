from poms.reports.backends.balance import BalanceReportBuilder


class PLReportBuilder(BalanceReportBuilder):
    def build(self):
        return self.instance
