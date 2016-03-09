from __future__ import unicode_literals

import logging
import random

from poms.reports.backends.base import BaseReportBuilder
from poms.reports.models import BalanceReportItem
from poms.transactions.models import TransactionClass

_l = logging.getLogger('poms.reports')


class BalanceReportBuilder(BaseReportBuilder):

    def _get_currency_item(self, items_index, items, transaction):
        key = 'currency:%s' % transaction.settlement_currency_id
        i = items_index.get(key, None)
        if i is None:
            i = BalanceReportItem(currency=transaction.settlement_currency)
            i.key = key
            items_index[key] = i
            items.append(i)
        return i

    def _get_instrument_item(self, items_index, items, transaction):
        key = 'instrument:%s' % transaction.instrument_id
        i = items_index.get(key, None)
        if i is None:
            i = BalanceReportItem(instrument=transaction.instrument)
            i.key = key
            items_index[key] = i
            items.append(i)
        return i

    def build(self):
        items_index = {}
        items = []
        for t in self.transactions:
            if t.transaction_class.code == TransactionClass.CASH_INFLOW:
                # c_cash[t['instrument']] += t['position_with_sign']
                cash_item = self._get_currency_item(items_index, items, t)
                cash_item.position_size_with_sign += t.position_size_with_sign
            elif t.transaction_class.code in [TransactionClass.BUY, TransactionClass.SELL]:
                instrument_item = self._get_instrument_item(items_index, items, t)
                instrument_item.position_size_with_sign += t.position_size_with_sign

                cash_item = self._get_currency_item(items_index, items, t)
                cash_item.position_size_with_sign += t.cash_consideration

                # c_cash[t['currency']] += t['cash_flow']
                # c_position[t['instrument']] += t['position_with_sign']
            elif t.transaction_class.code == TransactionClass.INSTRUMENT_PL:
                # c_cash[t['currency']] += t['cash_flow']
                cash_item = self._get_currency_item(items_index, items, t)
                cash_item.position_size_with_sign += t.cash_consideration

        self.instance.results = sorted(items, key=lambda x: x.key)
        return self.instance
