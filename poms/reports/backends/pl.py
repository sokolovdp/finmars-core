# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division

import six

from poms.reports.backends.balance import BalanceReportBuilder
from poms.reports.backends.base import BaseReport2Builder
from poms.reports.models import PLReportInstrument, BalanceReportItem
from poms.transactions.models import TransactionClass


class PLReportBuilder(BalanceReportBuilder):
    def __init__(self, *args, **kwargs):
        super(PLReportBuilder, self).__init__(*args, **kwargs)
        self._filter_date_attr = 'accounting_date'

    def build(self):
        balance_items, balance_invested_items = super(PLReportBuilder, self).get_items()

        items = {}
        for bi in balance_items:
            if bi.instrument:
                pli = PLReportInstrument(bi.instrument)
                pli.pk = '%s' % bi.instrument.id
                items['%s' % bi.instrument.id] = pli

                # summary.principal_with_sign_system_ccy += bi.principal_value_system_ccy
                # summary.carry_with_sign_system_ccy += bi.accrued_value_system_ccy

                pli.principal_with_sign_system_ccy += bi.principal_value_system_ccy
                pli.carry_with_sign_system_ccy += bi.accrued_value_system_ccy

        self.annotate_fx_rates()

        summary = self.instance.summary
        for t in self.transactions:
            t_class = t.transaction_class.code
            if t_class in [TransactionClass.CASH_INFLOW, TransactionClass.CASH_OUTFLOW]:
                t.principal_with_sign_system_ccy = t.principal_with_sign * t.transaction_currency_fx_rate
                t.carry_with_sign_system_ccy = t.carry_with_sign * t.transaction_currency_fx_rate
                t.overheads_with_sign_system_ccy = t.overheads_with_sign * t.transaction_currency_fx_rate

            elif t_class in [TransactionClass.BUY, TransactionClass.SELL, TransactionClass.FX_TRADE]:
                t.principal_with_sign_system_ccy = t.principal_with_sign * t.settlement_currency_fx_rate
                t.carry_with_sign_system_ccy = t.carry_with_sign * t.settlement_currency_fx_rate
                t.overheads_with_sign_system_ccy = t.overheads_with_sign * t.settlement_currency_fx_rate

                pli = items['%s' % t.instrument.id]
                pli.principal_with_sign_system_ccy += t.principal_with_sign_system_ccy
                pli.carry_with_sign_system_ccy += t.carry_with_sign_system_ccy
                pli.overheads_with_sign_system_ccy += t.overheads_with_sign_system_ccy

            elif t_class in [TransactionClass.INSTRUMENT_PL]:
                t.principal_with_sign_system_ccy = t.principal_with_sign * t.settlement_currency_fx_rate
                t.carry_with_sign_system_ccy = t.carry_with_sign * t.settlement_currency_fx_rate
                t.overheads_with_sign_system_ccy = t.overheads_with_sign * t.settlement_currency_fx_rate

                pli = items['%s' % t.instrument.id]
                pli.principal_with_sign_system_ccy += t.principal_with_sign_system_ccy
                pli.carry_with_sign_system_ccy += t.carry_with_sign_system_ccy
                pli.overheads_with_sign_system_ccy += t.overheads_with_sign_system_ccy

            elif t_class in [TransactionClass.TRANSACTION_PL]:
                t.principal_with_sign_system_ccy = t.principal_with_sign * t.settlement_currency_fx_rate
                t.carry_with_sign_system_ccy = t.carry_with_sign * t.settlement_currency_fx_rate
                t.overheads_with_sign_system_ccy = t.overheads_with_sign * t.settlement_currency_fx_rate

                try:
                    pli = items[t_class]
                except KeyError:
                    pli = items[t_class] = PLReportInstrument()
                    pli.pk = t_class
                pli.principal_with_sign_system_ccy += t.principal_with_sign_system_ccy
                pli.carry_with_sign_system_ccy += t.carry_with_sign_system_ccy
                pli.overheads_with_sign_system_ccy += t.overheads_with_sign_system_ccy

            # summary.principal_with_sign_system_ccy += getattr(t, 'principal_with_sign_system_ccy', 0.)
            # summary.carry_with_sign_system_ccy += getattr(t, 'carry_with_sign_system_ccy', 0.)
            # summary.overheads_with_sign_system_ccy += getattr(t, 'overheads_with_sign_system_ccy', 0.)
            pass

        # summary.principal_with_sign_system_ccy = \
        #     reduce(lambda x, y: x + y.principal_with_sign_system_ccy, items, 0.) + \
        #     reduce(lambda x, y: x + getattr(y, 'principal_with_sign_system_ccy', 0.), self.transactions, 0.)
        #
        # summary.carry_with_sign_system_ccy = \
        #     reduce(lambda x, y: x + y.carry_with_sign_system_ccy, items, 0.) + \
        #     reduce(lambda x, y: x + getattr(y, 'carry_with_sign_system_ccy', 0.), self.transactions, 0.)
        #
        # summary.overheads_with_sign_system_ccy = \
        #     reduce(lambda x, y: x + getattr(y, 'overheads_with_sign_system_ccy', 0.), self.transactions, 0.)

        # summary.total_system_ccy = summary.principal_with_sign_system_ccy + \
        #                            summary.carry_with_sign_system_ccy + \
        #                            summary.overheads_with_sign_system_ccy

        items = [i for i in six.itervalues(items)]
        items = sorted(items, key=lambda x: x.pk)
        for i in items:
            i.total_system_ccy = i.principal_with_sign_system_ccy + \
                                 i.carry_with_sign_system_ccy + \
                                 i.overheads_with_sign_system_ccy

            summary.principal_with_sign_system_ccy += i.principal_with_sign_system_ccy
            summary.carry_with_sign_system_ccy += i.carry_with_sign_system_ccy
            summary.overheads_with_sign_system_ccy += i.overheads_with_sign_system_ccy
            summary.total_system_ccy += i.total_system_ccy

        self.instance.items = items
        self.instance.transactions = self.transactions

        return self.instance


class PLReport2Builder(BaseReport2Builder):
    def __init__(self, *args, **kwargs):
        super(PLReport2Builder, self).__init__(*args, **kwargs)
        self._filter_date_attr = 'accounting_date'
        self._items = {}
        self._balance_items = {}

    def _get_item(self, trn, trn_key=None):
        t_key = trn_key or self._get_transaction_key(trn, 'instrument', None, 'account_position')
        try:
            return self._items[t_key]
        except KeyError:
            portfolio = trn.portfolio if self._use_portfolio else None
            account = trn.account_position if self._use_account else None
            instrument = trn.instrument
            item = PLReportInstrument(pk=t_key, portfolio=portfolio, account=account, instrument=instrument)
            self._items[t_key] = item
            return item

    def _get_balance_items(self, trn):
        t_key = self._get_transaction_key(trn, 'instrument', None, 'account_position')
        try:
            return self._balance_items[t_key]
        except KeyError:
            portfolio = trn.portfolio if self._use_portfolio else None
            account = trn.account_position if self._use_account else None
            instrument = trn.instrument
            item = BalanceReportItem(pk=t_key, portfolio=portfolio, account=account, instrument=instrument)
            self._balance_items[t_key] = item
            return item

    def build(self):
        # items = {}
        # for bi in balance_items:
        #     if bi.instrument:
        #         pli = PLReportInstrument(bi.instrument)
        #         pli.pk = '%s' % bi.instrument.id
        #         items['%s' % bi.instrument.id] = pli
        #
        #         # summary.principal_with_sign_system_ccy += bi.principal_value_system_ccy
        #         # summary.carry_with_sign_system_ccy += bi.accrued_value_system_ccy
        #
        #         pli.principal_with_sign_system_ccy += bi.principal_value_system_ccy
        #         pli.carry_with_sign_system_ccy += bi.accrued_value_system_ccy

        for t in self.transactions:
            t_class = t.transaction_class.code
            item = None
            if t_class in [TransactionClass.CASH_INFLOW, TransactionClass.CASH_OUTFLOW]:
                pass
            elif t_class in [TransactionClass.BUY, TransactionClass.SELL]:
                # t.principal_with_sign_system_ccy = t.principal_with_sign * t.settlement_currency_fx_rate
                # t.carry_with_sign_system_ccy = t.carry_with_sign * t.settlement_currency_fx_rate
                # t.overheads_with_sign_system_ccy = t.overheads_with_sign * t.settlement_currency_fx_rate

                item = self._get_item(t)

                bitem = self._get_balance_items(t)
                bitem.balance_position += t.position_size_with_sign

            elif t_class in [TransactionClass.INSTRUMENT_PL]:
                # t.principal_with_sign_system_ccy = t.principal_with_sign * t.settlement_currency_fx_rate
                # t.carry_with_sign_system_ccy = t.carry_with_sign * t.settlement_currency_fx_rate
                # t.overheads_with_sign_system_ccy = t.overheads_with_sign * t.settlement_currency_fx_rate

                item = self._get_item(t)

            elif t_class in [TransactionClass.TRANSACTION_PL]:
                # t.principal_with_sign_system_ccy = t.principal_with_sign * t.settlement_currency_fx_rate
                # t.carry_with_sign_system_ccy = t.carry_with_sign * t.settlement_currency_fx_rate
                # t.overheads_with_sign_system_ccy = t.overheads_with_sign * t.settlement_currency_fx_rate

                item = self._get_item(t, trn_key=TransactionClass.TRANSACTION_PL)

            elif t_class in [TransactionClass.FX_TRADE]:
                spec = self._get_item(t, trn_key=TransactionClass.FX_TRADE)

                self.set_currency_fx_rate(t, 'transaction_currency', date=t.accounting_date)
                self.set_currency_fx_rate(t, 'settlement_currency')

                t.principal_with_sign_system_ccy = t.principal_with_sign * t.settlement_currency_fx_rate + \
                                                   t.position_size_with_sign * t.transaction_currency_fx_rate
                t.carry_with_sign_system_ccy = t.carry_with_sign * t.settlement_currency_fx_rate
                t.overheads_with_sign_system_ccy = t.overheads_with_sign * t.settlement_currency_fx_rate

                spec.principal_with_sign_system_ccy += t.principal_with_sign_system_ccy
                spec.carry_with_sign_system_ccy += t.carry_with_sign_system_ccy
                spec.overheads_with_sign_system_ccy += t.overheads_with_sign_system_ccy

            if item:
                self.set_fx_rate(t)
                t.principal_with_sign_system_ccy = t.principal_with_sign * t.settlement_currency_fx_rate
                t.carry_with_sign_system_ccy = t.carry_with_sign * t.settlement_currency_fx_rate
                t.overheads_with_sign_system_ccy = t.overheads_with_sign * t.settlement_currency_fx_rate

                item.principal_with_sign_system_ccy += t.principal_with_sign_system_ccy
                item.carry_with_sign_system_ccy += t.carry_with_sign_system_ccy
                item.overheads_with_sign_system_ccy += t.overheads_with_sign_system_ccy

        for i in six.itervalues(self._balance_items):
            # TODO: copy-pasted from balance :(
            i.price_history = self.find_price_history(i.instrument)
            i.instrument_principal_currency_history = self.find_currency_history(i.instrument.pricing_currency)
            i.instrument_accrued_currency_history = self.find_currency_history(i.instrument.accrued_currency)

            i.instrument_price_multiplier = i.instrument.price_multiplier if i.instrument.price_multiplier is not None else 1.
            i.instrument_accrued_multiplier = i.instrument.accrued_multiplier if i.instrument.accrued_multiplier is not None else 1.

            i.instrument_principal_price = getattr(i.price_history, 'principal_price', 0.) or 0.
            i.instrument_accrued_price = getattr(i.price_history, 'accrued_price', 0.) or 0.

            i.principal_value_instrument_principal_ccy = i.instrument_price_multiplier * i.balance_position * i.instrument_principal_price
            i.accrued_value_instrument_accrued_ccy = i.instrument_accrued_multiplier * i.balance_position * i.instrument_accrued_price

            i.instrument_principal_fx_rate = getattr(i.instrument_principal_currency_history, 'fx_rate', 0.) or 0.
            i.instrument_accrued_fx_rate = getattr(i.instrument_accrued_currency_history, 'fx_rate', 0.) or 0.

            i.principal_value_system_ccy = i.principal_value_instrument_principal_ccy * i.instrument_principal_fx_rate
            i.accrued_value_system_ccy = i.accrued_value_instrument_accrued_ccy * i.instrument_accrued_fx_rate

            i.market_value_system_ccy = i.principal_value_system_ccy + i.accrued_value_system_ccy

            pli = self._items[i.pk]
            pli.principal_with_sign_system_ccy += i.principal_value_system_ccy
            pli.carry_with_sign_system_ccy += i.accrued_value_system_ccy

        summary = self.instance.summary
        for i in six.itervalues(self._items):
            i.total_system_ccy = i.principal_with_sign_system_ccy + \
                                 i.carry_with_sign_system_ccy + \
                                 i.overheads_with_sign_system_ccy

            summary.principal_with_sign_system_ccy += i.principal_with_sign_system_ccy
            summary.carry_with_sign_system_ccy += i.carry_with_sign_system_ccy
            summary.overheads_with_sign_system_ccy += i.overheads_with_sign_system_ccy
            summary.total_system_ccy += i.total_system_ccy

        items = [i for i in six.itervalues(self._items)]
        items = sorted(items, key=lambda x: '%s' % (x.pk,))

        self.instance.items = items
        self.instance.transactions = self.transactions

        return self.instance
