# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division

import six

from poms.reports.backends.balance import BalanceReportBuilder
from poms.reports.backends.base import BaseReport2Builder
from poms.reports.models import PLReportItem, BalanceReportItem
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
                pli = PLReportItem(bi.instrument)
                pli.pk = '%s' % bi.instrument.id
                items['%s' % bi.instrument.id] = pli

                # summary.principal_with_sign_system_ccy += bi.principal_value_system_ccy
                # summary.carry_with_sign_system_ccy += bi.accrued_value_system_ccy

                pli.principal_with_sign_system_ccy += bi.principal_value_system_ccy
                pli.carry_with_sign_system_ccy += bi.accrued_value_system_ccy

        self.annotate_fx_rates()

        summary = self.instance.summary
        for t in self.transactions:
            t_class = t.transaction_class_id
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
                    pli = items[t_class] = PLReportItem()
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

    def _get_item(self, trn, acc, ext=None):
        t_key = self.make_key(portfolio=trn.portfolio, account=acc, instrument=trn.instrument, ext=ext)
        try:
            return self._items[t_key]
        except KeyError:
            # portfolio = trn.portfolio if self._use_portfolio else None
            # account = acc if self._use_account else None
            # instrument = trn.instrument
            # item = PLReportItem(pk=t_key, portfolio=portfolio, account=account, instrument=instrument)
            item = self.make_item(PLReportItem, key=t_key, portfolio=trn.portfolio, account=acc,
                                  instrument=trn.instrument)
            self._items[t_key] = item
            return item

    def _get_balance_items(self, trn, acc, ext=None):
        t_key = self.make_key(portfolio=trn.portfolio, account=acc, instrument=trn.instrument, ext=ext)
        try:
            return self._balance_items[t_key]
        except KeyError:
            # portfolio = trn.portfolio if self._use_portfolio else None
            # account = acc if self._use_account else None
            # instrument = trn.instrument
            # item = BalanceReportItem(pk=t_key, portfolio=portfolio, account=account, instrument=instrument)
            item = self.make_item(BalanceReportItem, key=t_key, portfolio=trn.portfolio, account=acc,
                                  instrument=trn.instrument)
            self._balance_items[t_key] = item
            return item

    def _process_instrument(self, t, item, sign=1.):
        # default case
        # self.set_currency_fx_rate(t, 'transaction_currency')
        self.set_currency_fx_rate(t, 'settlement_currency')

        t.principal_with_sign_system_ccy = t.principal_with_sign * t.settlement_currency_fx_rate
        t.carry_with_sign_system_ccy = t.carry_with_sign * t.settlement_currency_fx_rate
        t.overheads_with_sign_system_ccy = t.overheads_with_sign * t.settlement_currency_fx_rate

        item.principal_with_sign_system_ccy += sign * t.principal_with_sign_system_ccy
        item.carry_with_sign_system_ccy += sign * t.carry_with_sign_system_ccy
        item.overheads_with_sign_system_ccy += sign * t.overheads_with_sign_system_ccy

    def _process_fx_trade(self, t, item, sign=1.):
        self.set_currency_fx_rate(t, 'transaction_currency')
        self.set_currency_fx_rate(t, 'settlement_currency')

        t.principal_with_sign_system_ccy = t.principal_with_sign * t.settlement_currency_fx_rate + \
                                           t.position_size_with_sign * t.transaction_currency_fx_rate
        t.carry_with_sign_system_ccy = t.carry_with_sign * t.settlement_currency_fx_rate
        t.overheads_with_sign_system_ccy = t.overheads_with_sign * t.settlement_currency_fx_rate

        item.principal_with_sign_system_ccy += sign * t.principal_with_sign_system_ccy
        item.carry_with_sign_system_ccy += sign * t.carry_with_sign_system_ccy
        item.overheads_with_sign_system_ccy += sign * t.overheads_with_sign_system_ccy

    def build(self):
        for t in self.transactions:
            t_class = t.transaction_class_id
            # item = None
            if t_class == TransactionClass.CASH_INFLOW or t_class == TransactionClass.CASH_OUTFLOW:
                pass
            elif t_class == TransactionClass.BUY or t_class == TransactionClass.SELL:
                item = self._get_item(t, acc=t.account_position)
                self._process_instrument(t, item)

                bitem = self._get_balance_items(t, acc=t.account_position)
                bitem.balance_position += t.position_size_with_sign

            elif t_class == TransactionClass.INSTRUMENT_PL:
                item = self._get_item(t, acc=t.account_position)
                self._process_instrument(t, item)

            elif t_class == TransactionClass.TRANSACTION_PL:
                item = self._get_item(t, acc=t.account_position, ext=TransactionClass.TRANSACTION_PL)
                item.name = TransactionClass.TRANSACTION_PL
                self._process_instrument(t, item)

            elif t_class == TransactionClass.FX_TRADE:
                spec = self._get_item(t, acc=t.account_position, ext=TransactionClass.FX_TRADE)
                spec.name = TransactionClass.FX_TRADE
                self._process_fx_trade(t, spec)

                # self.set_currency_fx_rate(t, 'transaction_currency')
                # self.set_currency_fx_rate(t, 'settlement_currency')
                #
                # t.principal_with_sign_system_ccy = t.principal_with_sign * t.settlement_currency_fx_rate + \
                #                                    t.position_size_with_sign * t.transaction_currency_fx_rate
                # t.carry_with_sign_system_ccy = t.carry_with_sign * t.settlement_currency_fx_rate
                # t.overheads_with_sign_system_ccy = t.overheads_with_sign * t.settlement_currency_fx_rate
                #
                # spec.principal_with_sign_system_ccy += t.principal_with_sign_system_ccy
                # spec.carry_with_sign_system_ccy += t.carry_with_sign_system_ccy
                # spec.overheads_with_sign_system_ccy += t.overheads_with_sign_system_ccy

            elif t_class == TransactionClass.TRANSFER:
                # item = self._get_item(t, acc=t.account_cash)
                # self._process_instrument(t, item)
                # bitem = self._get_balance_items(t, acc=t.account_cash)
                # bitem.balance_position += t.position_size_with_sign
                #
                # item = self._get_item(t, acc=t.account_position)
                # self._process_instrument(t, item, sign=-1.)
                # bitem = self._get_balance_items(t, acc=t.account_position)
                # bitem.balance_position += -t.position_size_with_sign

                # make 2 transactions for buy/sell
                pass

            elif t_class == TransactionClass.FX_TRANSFER:
                # spec = self._get_item(t, acc=t.account_cash, ext=TransactionClass.FX_TRADE)
                # spec.name = TransactionClass.FX_TRADE
                # self._process_fx_trade(t, spec)
                #
                # spec = self._get_item(t, acc=t.account_position, ext=TransactionClass.FX_TRADE)
                # spec.name = TransactionClass.FX_TRADE
                # self._process_fx_trade(t, spec, sign=-1.)

                # make 2 transactions for buy/sell
                pass

        for i in six.itervalues(self._balance_items):
            self.calc_balance_instrument(i)

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
