# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division

from functools import reduce

import six

from poms.reports.backends.balance import BalanceReportBuilder
from poms.reports.models import PLReportInstrument
from poms.transactions.models import TransactionClass


class PLReportBuilder(BalanceReportBuilder):
    def build(self):
        # super(PLReportBuilder, self).build()
        # balance_items = self.instance.items
        balance_items = super(PLReportBuilder, self).get_items()

        items = {}

        for bi in balance_items:
            if bi.instrument:
                pli = PLReportInstrument(bi.instrument)
                items['%s' % pli.pk] = pli

                # summary.principal_with_sign_system_ccy += bi.principal_value_system_ccy
                # summary.carry_with_sign_system_ccy += bi.accrued_value_system_ccy

                pli.principal_with_sign_system_ccy += bi.principal_value_system_ccy
                pli.carry_with_sign_system_ccy += bi.accrued_value_system_ccy

        items = [i for i in six.itervalues(items)]
        items = sorted(items, key=lambda x: x.pk)

        for i in items:
            i.total_system_ccy = i.principal_with_sign_system_ccy + \
                                 i.carry_with_sign_system_ccy + \
                                 i.overheads_with_sign_system_ccy

        self.annotate_fx_rates()

        for t in self.transactions:
            t.transaction_class_code = t_class = t.transaction_class.code
            if t_class == TransactionClass.CASH_INFLOW:
                t.principal_with_sign_system_ccy = t.principal_with_sign * t.transaction_currency_fx_rate
                t.carry_with_sign_system_ccy = t.carry_with_sign * t.transaction_currency_fx_rate
                t.overheads_with_sign_system_ccy = t.overheads_with_sign * t.transaction_currency_fx_rate
            elif t_class in [TransactionClass.BUY, TransactionClass.SELL]:
                t.principal_with_sign_system_ccy = t.principal_with_sign * t.settlement_currency_fx_rate
                t.carry_with_sign_system_ccy = t.carry_with_sign * t.settlement_currency_fx_rate
                t.overheads_with_sign_system_ccy = t.overheads_with_sign * t.settlement_currency_fx_rate
            elif t_class == TransactionClass.INSTRUMENT_PL:
                t.principal_with_sign_system_ccy = t.principal_with_sign * t.settlement_currency_fx_rate
                t.carry_with_sign_system_ccy = t.carry_with_sign * t.settlement_currency_fx_rate
                t.overheads_with_sign_system_ccy = t.overheads_with_sign * t.settlement_currency_fx_rate

                # summary.principal_with_sign_system_ccy += getattr(t, 'principal_with_sign_system_ccy', 0.)
                # summary.carry_with_sign_system_ccy += getattr(t, 'carry_with_sign_system_ccy', 0.)
                # summary.overheads_with_sign_system_ccy += getattr(t, 'overheads_with_sign_system_ccy', 0.)

        summary = self.instance.summary

        summary.principal_with_sign_system_ccy = \
            reduce(lambda x, y: x + y.principal_with_sign_system_ccy, items, 0.) + \
            reduce(lambda x, y: x + getattr(y, 'principal_with_sign_system_ccy', 0.), self.transactions, 0.)

        summary.carry_with_sign_system_ccy = \
            reduce(lambda x, y: x + y.carry_with_sign_system_ccy, items, 0.) + \
            reduce(lambda x, y: x + getattr(y, 'carry_with_sign_system_ccy', 0.), self.transactions, 0.)

        summary.overheads_with_sign_system_ccy = \
            reduce(lambda x, y: x + getattr(y, 'overheads_with_sign_system_ccy', 0.), self.transactions, 0.)

        summary.total_system_ccy = summary.principal_with_sign_system_ccy + \
                                   summary.carry_with_sign_system_ccy + \
                                   summary.overheads_with_sign_system_ccy

        self.instance.items = items
        self.instance.transactions = self.transactions

        return self.instance
