from django.utils import timezone

from poms.reports.backends.base import BaseReportBuilder
from poms.reports.models import YTMReportInstrument
from poms.transactions.models import TransactionClass


class YTMReportBuilder(BaseReportBuilder):
    def _get_ytm_item(self, items, items_index, instrument):
        key = 'instrument:%s' % instrument.id
        i = items_index.get(key, None)
        if i is None:
            i = YTMReportInstrument(instrument=instrument)
            i.pk = instrument.id
            items_index[key] = i
            items.append(i)
        return i

    def build(self):
        multiplier_attr = None
        if self.instance.multiplier_class == 'avco':
            self.annotate_avco_multiplier()
            multiplier_attr = 'avco_multiplier'
        elif self.instance.multiplier_class == 'fifo':
            self.annotate_fifo_multiplier()
            multiplier_attr = 'fifo_multiplier'

        items = []
        items_index = {}

        now = self.instance.end_date or timezone.now().date()

        for t in self.transactions:
            if t.transaction_class.code in [TransactionClass.BUY, TransactionClass.SELL]:
                item = self._get_ytm_item(items, items_index, t.instrument)
                item.position += t.position_size_with_sign

        for t in self.transactions:
            if t.transaction_class.code in [TransactionClass.BUY, TransactionClass.SELL]:
                multiplier = getattr(t, multiplier_attr, 0.)
                item = self._get_ytm_item(items, items_index, t.instrument)

                t.ytm = 0.
                t.time_invested = (now - t.transaction_date).days
                t.remaining_position = abs(t.position_size_with_sign * (1 - multiplier))
                t.remaining_position_percent = t.remaining_position / item.position
                t.weighted_ytm = t.ytm * t.remaining_position_percent
                t.weighted_time_invested = t.time_invested * t.remaining_position_percent

                item.ytm += t.weighted_ytm
                item.time_invested += t.weighted_time_invested

        self.instance.transactions = self.transactions
        self.instance.items = items
        return self.instance
