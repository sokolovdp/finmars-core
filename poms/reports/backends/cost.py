# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division

import six

from poms.reports.backends.base import BaseReportBuilder
from poms.reports.models import CostReportInstrument
from poms.transactions.models import TransactionClass


class CostReportBuilder(BaseReportBuilder):
    def __init__(self, *args, **kwargs):
        super(CostReportBuilder, self).__init__(*args, **kwargs)

    def _get_transaction_qs(self):
        queryset = super(CostReportBuilder, self)._get_transaction_qs()
        queryset = queryset.filter(transaction_class__code__in=[TransactionClass.BUY, TransactionClass.SELL])
        return queryset

    def _get_cost_item(self, items, instrument):
        key = 'instrument:%s' % instrument.id
        i = items.get(key, None)
        if i is None:
            i = CostReportInstrument(instrument=instrument)
            i.pk = instrument.id
            items[key] = i
        return i

    def build(self):
        multiplier_attr = self.annotate_multiplier(self.instance.multiplier_class)

        self.annotate_fx_rates()

        items = {}
        for t in self.transactions:
            if t.transaction_class.code in [TransactionClass.BUY, TransactionClass.SELL]:
                multiplier = getattr(t, multiplier_attr, 0.)

                t.remaining_position = abs(t.position_size_with_sign * (1 - multiplier))
                t.remaining_position_cost_settlement_ccy = t.principal_with_sign * (1 - multiplier)
                t.remaining_position_cost_system_ccy = t.remaining_position_cost_settlement_ccy * t.settlement_currency_fx_rate

                item = self._get_cost_item(items, t.instrument)
                item.position += t.remaining_position
                item.cost_system_ccy += t.remaining_position_cost_system_ccy

        items = [i for i in six.itervalues(items)]
        items = sorted(items, key=lambda x: x.pk)

        for item in items:
            self.annotate_fx_rate(item.instrument, 'pricing_currency')
            item.cost_instrument_ccy = item.cost_system_ccy / item.instrument.pricing_currency_fx_rate
            item.cost_price = abs(item.cost_instrument_ccy / item.position)
            item.cost_price_adjusted = item.cost_price / item.instrument.price_multiplier

        self.instance.transactions = self.transactions
        self.instance.items = items
        return self.instance
