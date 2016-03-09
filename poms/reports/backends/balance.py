from __future__ import unicode_literals

import logging

from poms.reports.backends.base import BaseReportBuilder
from poms.reports.models import BalanceReportItem, BalanceReportSummary
from poms.transactions.models import TransactionClass

_l = logging.getLogger('poms.reports')


class BalanceReportBuilder(BaseReportBuilder):
    def _get_currency_item(self, items_index, items, currency):
        key = 'currency:%s' % currency.id
        i = items_index.get(key, None)
        if i is None:
            i = BalanceReportItem(currency=currency)
            i.key = key
            items_index[key] = i
            items.append(i)
        return i

    def _get_instrument_item(self, items_index, items, instrument):
        key = 'instrument:%s' % instrument.id
        i = items_index.get(key, None)
        if i is None:
            i = BalanceReportItem(instrument=instrument)
            i.key = key
            items_index[key] = i
            items.append(i)
        return i

    def build(self):
        items_index = {}
        items = []
        for t in self.transactions:
            if t.transaction_class.code == TransactionClass.CASH_INFLOW:
                cash_item = self._get_currency_item(items_index, items, t.transaction_currency)
                cash_item.position_size_with_sign += t.position_size_with_sign
            elif t.transaction_class.code in [TransactionClass.BUY, TransactionClass.SELL]:
                instrument_item = self._get_instrument_item(items_index, items, t.instrument)
                instrument_item.position_size_with_sign += t.position_size_with_sign

                cash_item = self._get_currency_item(items_index, items, t.settlement_currency)
                cash_item.position_size_with_sign += t.cash_consideration
            elif t.transaction_class.code == TransactionClass.INSTRUMENT_PL:
                cash_item = self._get_currency_item(items_index, items, t.settlement_currency)
                cash_item.position_size_with_sign += t.cash_consideration

        items = sorted(items, key=lambda x: x.key)
        self.instance.results = items

        if self.instance.currency:
            summary = BalanceReportSummary()
            ccy = self.instance.currency
            for t in self.transactions:
                if t.transaction_class.code == TransactionClass.CASH_INFLOW:
                    value = self.currency_fx(t.transaction_currency,
                                             t.position_size_with_sign,
                                             ccy)
                    summary.invested_value += value
            for i in items:
                if i.instrument:
                    value = i.position_size_with_sign * self.instrument_price(i.instrument)
                    value = self.currency_fx(i.instrument.currency,
                                             value,
                                             ccy)
                    print('%s -> %s' % (i.instrument, value))
                    summary.current_value += value
                if i.currency:
                    value = self.currency_fx(i.currency,
                                             i.position_size_with_sign,
                                             ccy)
                    print('%s -> %s' % (i.currency, value))
                    summary.current_value += value
            summary.p_and_l = summary.current_value - summary.invested_value
            self.instance.summary = summary

        return self.instance
