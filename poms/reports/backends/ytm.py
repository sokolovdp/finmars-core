# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division

import six

from poms.reports.backends.base import BaseReportBuilder
from poms.reports.models import YTMReportInstrument
from poms.transactions.models import TransactionClass


class YTMReportBuilder(BaseReportBuilder):
    def __init__(self, *args, **kwargs):
        super(YTMReportBuilder, self).__init__(*args, **kwargs)
        self._filter_date_attr = 'accounting_date'

    def _get_transaction_qs(self):
        queryset = super(YTMReportBuilder, self)._get_transaction_qs()
        # queryset = queryset.filter(transaction_class__code__in=[TransactionClass.BUY, TransactionClass.SELL])
        return queryset

    def _get_ytm_item(self, items, transaction):
        key = '%s' % transaction.instrument.id
        i = items.get(key, None)
        if i is None:
            i = YTMReportInstrument(instrument=transaction.instrument)
            # i.pk = transaction.instrument.id
            items[key] = i
        return i

    def build(self):
        multiplier_attr = self.annotate_multiplier(self.instance.multiplier_class)

        items = {}
        end_date = self.end_date

        # calculate total position for instrument
        for t in self.transactions:
            t_class = t.transaction_class.code
            if t_class in [TransactionClass.BUY, TransactionClass.SELL, TransactionClass.FX_TRADE]:
                item = self._get_ytm_item(items, t)
                item.position += t.position_size_with_sign

        for t in self.transactions:
            t_class = t.transaction_class.code
            if t_class in [TransactionClass.BUY, TransactionClass.SELL, TransactionClass.FX_TRADE]:
                multiplier = getattr(t, multiplier_attr, 0.)
                item = self._get_ytm_item(items, t)

                t.ytm = 0.
                t.time_invested = (end_date - t.transaction_date).days
                t.remaining_position = abs(t.position_size_with_sign * (1 - multiplier))
                t.remaining_position_percent = t.remaining_position / item.position
                t.weighted_ytm = t.ytm * t.remaining_position_percent
                t.weighted_time_invested = t.time_invested * t.remaining_position_percent

                item.ytm += t.weighted_ytm
                item.time_invested += t.weighted_time_invested

        items = [i for i in six.itervalues(items)]
        items = sorted(items, key=lambda x: x.pk)

        self.instance.transactions = self.transactions
        self.instance.items = items
        return self.instance
