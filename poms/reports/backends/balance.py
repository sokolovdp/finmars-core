# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division

import logging
from functools import reduce

from poms.reports.backends.base import BaseReportBuilder
from poms.reports.models import BalanceReportItem
from poms.transactions.models import TransactionClass

_l = logging.getLogger('poms.reports')


class BalanceReportBuilder(BaseReportBuilder):
    def _get_currency_item(self, items_index, items, currency):
        key = 'currency:%s' % currency.id
        i = items_index.get(key, None)
        if i is None:
            i = BalanceReportItem(currency=currency)
            i.pk = key
            items_index[key] = i
            items.append(i)
        return i

    def _get_instrument_item(self, items_index, items, instrument):
        key = 'instrument:%s' % instrument.id
        i = items_index.get(key, None)
        if i is None:
            i = BalanceReportItem(instrument=instrument)
            i.pk = key
            items_index[key] = i
            items.append(i)
        return i

    def build(self):
        items_index = {}
        items = []
        invested_items_index = {}
        invested_items = []
        for t in self.transactions:
            if t.transaction_class.code == TransactionClass.CASH_INFLOW:
                cash_item = self._get_currency_item(items_index, items, t.transaction_currency)
                cash_item.balance_position += t.position_size_with_sign

                invested_item = self._get_currency_item(invested_items_index, invested_items, t.transaction_currency)
                invested_item.balance_position += t.position_size_with_sign
            elif t.transaction_class.code in [TransactionClass.BUY, TransactionClass.SELL]:
                instrument_item = self._get_instrument_item(items_index, items, t.instrument)
                instrument_item.balance_position += t.position_size_with_sign

                cash_item = self._get_currency_item(items_index, items, t.settlement_currency)
                cash_item.balance_position += t.cash_consideration
            elif t.transaction_class.code == TransactionClass.INSTRUMENT_PL:
                cash_item = self._get_currency_item(items_index, items, t.settlement_currency)
                cash_item.balance_position += t.cash_consideration

        items = sorted(items, key=lambda x: x.pk)
        self.instance.items = items

        invested_items = sorted(invested_items, key=lambda x: x.pk)
        self.instance.invested_items = invested_items

        for i in invested_items:
            i.currency_history = self.find_currency_history(i.currency)
            i.currency_fx_rate = getattr(i.currency_history, 'fx_rate', 0.)
            i.market_value_system_ccy = i.balance_position * i.currency_fx_rate

        for i in items:
            if i.instrument:
                i.price_history = self.find_price_history(i.instrument, self.instance.end_date)
                i.instrument_principal_currency_history = self.find_currency_history(i.instrument.pricing_currency)
                i.instrument_accrued_currency_history = self.find_currency_history(i.instrument.accrued_currency)

                # i.instrument_name = i.instrument.name
                # i.instrument_principal_pricing_ccy = getattr(i.instrument.pricing_currency, 'name', None)
                i.instrument_price_multiplier = i.instrument.price_multiplier if i.instrument.price_multiplier is not None else 1.
                # i.instrument_accrued_pricing_ccy = getattr(i.instrument.accrued_currency, 'name', None)
                i.instrument_accrued_multiplier = i.instrument.accrued_multiplier if i.instrument.accrued_multiplier is not None else 1.

                i.instrument_principal_price = getattr(i.price_history, 'principal_price', 0.) or 0.
                i.instrument_accrued_price = getattr(i.price_history, 'accrued_price', 0.) or 0.

                i.principal_value_instrument_principal_ccy = i.instrument_price_multiplier * i.balance_position * i.instrument_principal_price
                i.accrued_value_instrument_principal_ccy = i.instrument_accrued_multiplier * i.balance_position * i.instrument_accrued_price

                i.instrument_principal_fx_rate = getattr(i.instrument_principal_currency_history, 'fx_rate', 0.) or 0.
                i.instrument_accrued_fx_rate = getattr(i.instrument_accrued_currency_history, 'fx_rate', 0.) or 0.

                i.principal_value_instrument_system_ccy = i.principal_value_instrument_principal_ccy * i.instrument_principal_fx_rate
                i.accrued_value_instrument_system_ccy = i.accrued_value_instrument_principal_ccy * i.instrument_accrued_fx_rate

                i.market_value_system_ccy = i.principal_value_instrument_system_ccy + \
                                            i.accrued_value_instrument_system_ccy
            elif i.currency:
                # i.currency_name = i.currency.name
                i.currency_history = self.find_currency_history(i.currency)
                i.currency_fx_rate = getattr(i.currency_history, 'fx_rate', 0.)
                i.principal_value_instrument_system_ccy = i.balance_position * i.currency_fx_rate
                i.market_value_system_ccy = i.principal_value_instrument_system_ccy

        summary = self.instance.summary
        summary.invested_value_system_ccy = reduce(lambda x, y: x + y.market_value_system_ccy, invested_items, 0.)
        summary.current_value_system_ccy = reduce(lambda x, y: x + y.market_value_system_ccy, items, 0.)
        summary.p_l_system_ccy = summary.current_value_system_ccy - summary.invested_value_system_ccy

        return self.instance
