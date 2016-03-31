# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division

import six

from poms.reports.backends.base import BaseReportBuilder, BaseReport2Builder
from poms.reports.models import CostReportItem
from poms.transactions.models import TransactionClass


class CostReportBuilder(BaseReportBuilder):
    def __init__(self, *args, **kwargs):
        super(CostReportBuilder, self).__init__(*args, **kwargs)
        self._filter_date_attr = 'accounting_date'

    def _get_transaction_qs(self):
        queryset = super(CostReportBuilder, self)._get_transaction_qs()
        # queryset = queryset.filter(transaction_class__code__in=[TransactionClass.BUY, TransactionClass.SELL])
        return queryset

    def _get_cost_item(self, items, transaction):
        key = '%s' % transaction.instrument.id
        i = items.get(key, None)
        if i is None:
            i = CostReportItem(pk='%s' % transaction.instrument.id, instrument=transaction.instrument)
            items[key] = i
        return i

    def build(self):
        multiplier_attr = self.annotate_multiplier(self.instance.multiplier_class)

        self.annotate_fx_rates()

        items = {}
        for t in self.transactions:
            t_class = t.transaction_class_id
            if t_class in [TransactionClass.BUY, TransactionClass.SELL]:
                multiplier = getattr(t, multiplier_attr, 0.)

                t.remaining_position = abs(t.position_size_with_sign * (1 - multiplier))
                t.remaining_position_cost_settlement_ccy = t.principal_with_sign * (1 - multiplier)
                t.remaining_position_cost_system_ccy = t.remaining_position_cost_settlement_ccy * t.settlement_currency_fx_rate

                item = self._get_cost_item(items, t)
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


class CostReport2Builder(BaseReport2Builder):
    def __init__(self, *args, **kwargs):
        super(CostReport2Builder, self).__init__(*args, **kwargs)
        self._filter_date_attr = 'accounting_date'
        self._items = {}

    def _get_item(self, trn, ext=None):
        t_key = self.make_key(portfolio=trn.portfolio, instrument=trn.instrument, account=trn.account_position, ext=ext)
        try:
            return self._items[t_key]
        except KeyError:
            portfolio = trn.portfolio if self._use_portfolio else None
            account = trn.account_position if self._use_account else None
            instrument = trn.instrument
            item = CostReportItem(pk=t_key, portfolio=portfolio, account=account, instrument=instrument)
            self._items[t_key] = item
            return item

    def build(self):
        multiplier_attr = self.set_multipliers(self.instance.multiplier_class)

        for t in self.transactions:
            self.set_currency_fx_rate(t, 'settlement_currency')

            t_class = t.transaction_class_id
            if t_class in [TransactionClass.BUY, TransactionClass.SELL]:
                multiplier = getattr(t, multiplier_attr, 0.)

                t.remaining_position = abs(t.position_size_with_sign * (1 - multiplier))
                t.remaining_position_cost_settlement_ccy = t.principal_with_sign * (1 - multiplier)
                t.remaining_position_cost_system_ccy = t.remaining_position_cost_settlement_ccy * t.settlement_currency_fx_rate

                item = self._get_item(t)
                item.position += t.remaining_position
                item.cost_system_ccy += t.remaining_position_cost_system_ccy

        items = [i for i in six.itervalues(self._items)]
        items = sorted(items, key=lambda x: x.pk)

        for item in items:
            self.set_currency_fx_rate(item.instrument, 'pricing_currency')
            item.cost_instrument_ccy = item.cost_system_ccy / item.instrument.pricing_currency_fx_rate
            item.cost_price = abs(item.cost_instrument_ccy / item.position)
            item.cost_price_adjusted = item.cost_price / item.instrument.price_multiplier

        self.instance.transactions = self.transactions
        self.instance.items = items
        return self.instance