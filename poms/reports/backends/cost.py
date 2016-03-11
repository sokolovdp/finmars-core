from poms.reports.backends.base import BaseReportBuilder


class CostReportBuilder(BaseReportBuilder):
    def build(self):
        if self.instance.multiplier_class == 'avco':
            self.annotate_avco_multiplier()
        elif self.instance.multiplier_class == 'fifo':
            self.annotate_fifo_multiplier()
        self.instance.transactions = self.transactions
        return self.instance
