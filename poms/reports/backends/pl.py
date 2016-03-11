# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division

from poms.reports.backends.balance import BalanceReportBuilder
from poms.reports.models import PLReportInstrument
from poms.transactions.models import TransactionClass


class PLReportBuilder(BalanceReportBuilder):
    def build(self):
        super(PLReportBuilder, self).build()

        summary = self.instance.summary
        items_index = {}
        items = []

        for i in self.instance.items:
            if i.instrument:
                pli = PLReportInstrument(i.instrument)
                items.append(pli)
                items_index['%s' % pli.pk] = pli

                summary.principal_with_sign_system_ccy += i.principal_value_instrument_system_ccy
                summary.carry_with_sign_system_ccy += i.accrued_value_instrument_system_ccy

                pli.principal_with_sign_system_ccy += i.principal_value_instrument_system_ccy
                pli.carry_with_sign_system_ccy += i.accrued_value_instrument_system_ccy

        for i in items:
            i.total_system_ccy = i.principal_with_sign_system_ccy + \
                                 i.carry_with_sign_system_ccy + \
                                 i.overheads_with_sign_system_ccy

        self.annotate_fx_rates()

        for t in self.transactions:
            t.transaction_class_code = t.transaction_class.code
            # if t.transaction_currency:
            #     t.transaction_currency_name = t.transaction_currency.name
            # if t.instrument:
            #     t.instrument_name = t.instrument.name
            # if t.settlement_currency:
            #     t.settlement_currency_name = t.settlement_currency.name

            if t.transaction_class.code == TransactionClass.CASH_INFLOW:
                t.principal_with_sign_system_ccy = t.principal_with_sign * t.transaction_currency_fx_rate
                t.carry_with_sign_system_ccy = t.carry_with_sign * t.transaction_currency_fx_rate
                t.overheads_with_sign_system_ccy = t.overheads_with_sign * t.transaction_currency_fx_rate
            elif t.transaction_class.code in [TransactionClass.BUY, TransactionClass.SELL]:
                t.principal_with_sign_system_ccy = t.principal_with_sign * t.settlement_currency_fx_rate
                t.carry_with_sign_system_ccy = t.carry_with_sign * t.settlement_currency_fx_rate
                t.overheads_with_sign_system_ccy = t.overheads_with_sign * t.settlement_currency_fx_rate
            elif t.transaction_class.code == TransactionClass.INSTRUMENT_PL:
                t.principal_with_sign_system_ccy = t.principal_with_sign * t.settlement_currency_fx_rate
                t.carry_with_sign_system_ccy = t.carry_with_sign * t.settlement_currency_fx_rate
                t.overheads_with_sign_system_ccy = t.overheads_with_sign * t.settlement_currency_fx_rate

            summary.principal_with_sign_system_ccy += getattr(t, 'principal_with_sign_system_ccy', 0.)
            summary.carry_with_sign_system_ccy += getattr(t, 'carry_with_sign_system_ccy', 0.)
            summary.overheads_with_sign_system_ccy += getattr(t, 'overheads_with_sign_system_ccy', 0.)

        summary.total_system_ccy = summary.principal_with_sign_system_ccy + \
                                   summary.carry_with_sign_system_ccy + \
                                   summary.overheads_with_sign_system_ccy

        self.instance.items = items
        self.instance.transactions = self.transactions

        return self.instance
