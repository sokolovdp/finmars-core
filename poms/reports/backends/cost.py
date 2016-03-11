from poms.reports.backends.base import BaseReportBuilder
from poms.reports.models import CostReportInstrument
from poms.transactions.models import TransactionClass


class CostReportBuilder(BaseReportBuilder):
    def _get_cost_item(self, items, items_index, instrument):
        key = 'instrument:%s' % instrument.id
        i = items_index.get(key, None)
        if i is None:
            i = CostReportInstrument(instrument=instrument)
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

        self.annotate_fx_rates()

        for t in self.transactions:
            if t.transaction_class.code in [TransactionClass.BUY, TransactionClass.SELL]:
                multiplier = getattr(t, multiplier_attr, 0.)
                t.remaining_position = abs(t.position_size_with_sign * (1 - multiplier))
                t.remaining_position_cost_settlement_ccy = t.principal_with_sign * (1 - multiplier)
                t.remaining_position_cost_system_ccy = t.remaining_position_cost_settlement_ccy * t.settlement_currency_fx_rate

                item = self._get_cost_item(items, items_index, t.instrument)
                item.position += t.remaining_position
                item.cost_system_ccy += t.remaining_position_cost_system_ccy

        for item in items:
            self.annotate_fx_rate(item.instrument, 'pricing_currency')
            item.cost_instrument_ccy = item.cost_system_ccy / item.instrument.pricing_currency_fx_rate
            item.cost_price = abs(item.cost_instrument_ccy / item.position)
            item.cost_price_adjusted = item.cost_price / item.instrument.price_multiplier

        self.instance.transactions = self.transactions
        self.instance.items = items
        return self.instance
