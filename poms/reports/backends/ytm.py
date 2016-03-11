from poms.reports.backends.base import BaseReportBuilder


class YTMReportBuilder(BaseReportBuilder):
    def build(self):
        multiplier = None
        if self.instance.multiplier_class == 'avco':
            self.annotate_avco_multiplier()
            multiplier = 'avco_multiplier'
        elif self.instance.multiplier_class == 'fifo':
            self.annotate_fifo_multiplier()
            multiplier = 'fifo_multiplier'

        items = []
        items_index = {}

        self.instance.transactions = self.transactions
        self.instance.items = items
        return self.instance
