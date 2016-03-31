# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division

import logging
from datetime import date
from functools import reduce

import six

from poms.reports.backends.base import BaseReportBuilder, BaseReport2Builder
from poms.reports.models import BalanceReportItem
from poms.transactions.models import TransactionClass

_l = logging.getLogger('poms.reports')


# случаи 1 и 2 возможны для всех транзакций кроме Cash-Inflow/Outflow
# в т.ч. для Трансфер (чуть позже я поясню, что на самом деле Transfer = Sell + Buy)

class BalanceReportBuilder(BaseReportBuilder):
    def __init__(self, *args, **kwargs):
        super(BalanceReportBuilder, self).__init__(*args, **kwargs)
        self._filter_date_attr = 'transaction_date'

    def _get_transaction_qs(self):
        queryset = super(BalanceReportBuilder, self)._get_transaction_qs()
        return queryset

    def _get_currency_item(self, items, currency, account, transaction=None):
        key = 'currency:%s;account:%s;transaction:%s' % \
              (currency.id, getattr(account, 'pk', None), getattr(transaction, 'pk', None))
        i = items.get(key, None)
        if i is None:
            i = BalanceReportItem(currency=currency, account=account)
            i.pk = key
            items[key] = i
            i.transaction = transaction
        return i

    def _get_instrument_item(self, items, instrument, account):
        key = 'instrument:%s;account:%s' % (instrument.id, getattr(account, 'pk', None))
        i = items.get(key, None)
        if i is None:
            i = BalanceReportItem(instrument=instrument, account=account)
            i.pk = key
            items[key] = i
        return i

    def get_accounts(self, transaction):
        now = self.end_date
        accounting_date = transaction.accounting_date
        cash_date = transaction.cash_date
        if cash_date is None:
            cash_date = date.max
        if accounting_date == cash_date or (accounting_date < now and cash_date < now):  # default
            return 0, transaction.account_position, transaction.account_cash
        else:
            if cash_date > accounting_date:  # case 1
                return 1, transaction.account_position, transaction.account_interim
            else:  # case 2
                return 2, None, transaction.account_interim

    def is_show_details(self, case, account):
        if case == 0 or not getattr(self.instance, 'show_transaction_details', False):
            return False
        acc_type = getattr(account, 'type', None)
        return getattr(acc_type, 'show_transaction_details', False)

    def get_transaction_details(self, case, account, transaction):
        if self.is_show_details(case, account):
            return transaction
        return None

    def get_items(self):
        invested_items = {}
        items = {}

        for t in self.transactions:
            t_class = t.transaction_class_id
            case, account_position, account_cash = self.get_accounts(t)

            if t_class in [TransactionClass.CASH_INFLOW, TransactionClass.CASH_OUTFLOW]:
                cash_item = self._get_currency_item(items, t.transaction_currency, account_position)
                cash_item.balance_position += t.position_size_with_sign

                invested_item = self._get_currency_item(invested_items, t.transaction_currency, account_position)
                invested_item.balance_position += t.position_size_with_sign

            elif t_class in [TransactionClass.FX_TRADE]:
                # TODO: use transaction_currency
                pass
            elif t_class in [TransactionClass.BUY, TransactionClass.SELL]:
                if case == 0 or case == 1:
                    if account_position:
                        instrument_item = self._get_instrument_item(items, t.instrument, account_position)
                        instrument_item.balance_position += t.position_size_with_sign
                    cash_item = self._get_currency_item(items, t.settlement_currency, account_cash,
                                                        self.get_transaction_details(case, account_cash, t))
                    cash_item.balance_position += t.cash_consideration
                elif case == 2:
                    cash_item = self._get_currency_item(items, t.settlement_currency, account_cash,
                                                        self.get_transaction_details(case, account_cash, t))
                    cash_item.balance_position += -t.cash_consideration

            elif t_class in [TransactionClass.INSTRUMENT_PL, TransactionClass.TRANSACTION_PL]:
                if case == 0 or case == 1:
                    cash_item = self._get_currency_item(items, t.settlement_currency, account_cash,
                                                        self.get_transaction_details(case, account_cash, t))
                    cash_item.balance_position += t.cash_consideration
                elif case == 2:
                    cash_item = self._get_currency_item(items, t.settlement_currency, account_cash,
                                                        self.get_transaction_details(case, account_cash, t))
                    cash_item.balance_position += -t.cash_consideration

        for i in six.itervalues(invested_items):
            i.currency_history = self.find_currency_history(i.currency)
            i.currency_fx_rate = getattr(i.currency_history, 'fx_rate', 0.)
            i.market_value_system_ccy = i.balance_position * i.currency_fx_rate

        for i in six.itervalues(items):
            if i.instrument:
                i.price_history = self.find_price_history(i.instrument, self.instance.end_date)
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
            elif i.currency:
                # i.currency_name = i.currency.name
                i.currency_history = self.find_currency_history(i.currency)
                i.currency_fx_rate = getattr(i.currency_history, 'fx_rate', 0.)
                i.principal_value_system_ccy = i.balance_position * i.currency_fx_rate
                i.market_value_system_ccy = i.principal_value_system_ccy

        invested_items = [i for i in six.itervalues(invested_items)]
        invested_items = sorted(invested_items, key=lambda x: x.pk)

        items = [i for i in six.itervalues(items)]
        items = sorted(items, key=lambda x: x.pk)

        return items, invested_items

    def build(self):
        items, invested_items = self.get_items()

        self.instance.invested_items = invested_items
        self.instance.items = items

        summary = self.instance.summary
        summary.invested_value_system_ccy = reduce(lambda x, y: x + y.market_value_system_ccy, invested_items, 0.)
        summary.current_value_system_ccy = reduce(lambda x, y: x + y.market_value_system_ccy, items, 0.)
        summary.p_l_system_ccy = summary.current_value_system_ccy - summary.invested_value_system_ccy

        self.instance.transactions = self.transactions

        return self.instance


class BalanceReport2Builder(BaseReport2Builder):
    def __init__(self, *args, **kwargs):
        super(BalanceReport2Builder, self).__init__(*args, **kwargs)
        self._filter_date_attr = 'transaction_date'
        self._invested_items = {}
        self._items = {}

    def _get_item0(self, items, trn, instr=None, ccy=None, acc=None, ext=None):
        t_key = self.make_key(portfolio=trn.portfolio, instrument=instr, currency=ccy, account=acc, ext=ext)
        try:
            return items[t_key]
        except KeyError:
            portfolio = trn.portfolio if self._use_portfolio else None
            account = acc if self._use_account else None
            instrument = instr
            currency = ccy
            item = BalanceReportItem(pk=t_key, portfolio=portfolio, account=account, instrument=instrument,
                                     currency=currency)
            items[t_key] = item
            return item

    def _get_item(self, trn, instr=None, ccy=None, acc=None, case=None):
        if self._is_show_details(trn, case, acc):
            ext = trn.id
        else:
            ext = None
        item = self._get_item0(self._items, trn, instr=instr, ccy=ccy, acc=acc, ext=ext)
        if ext:
            item.transaction = trn
        return item

    def _is_show_details(self, trn, case, acc):
        if (case == 1 or case == 2) and self.instance.show_transaction_details:
            return acc and acc.type and acc.type.show_transaction_details
        return False

    def _get_invested_items(self, trn, instr=None, ccy=None, acc=None):
        return self._get_item0(self._invested_items, trn, instr=instr, ccy=ccy, acc=acc)

    def _get_trn_case(self, trn):
        accounting_date, cash_date = trn.accounting_date, trn.cash_date
        if cash_date is None:
            cash_date = date.max

        if accounting_date <= self._end_date < cash_date:  # default
            return 1
        elif cash_date <= self._end_date < accounting_date:
            return 2
        else:
            return 0

    def _add_cash(self, item, value, fx_rate=None, fx_rate_date=None):
        if fx_rate is None:
            fx_rate_date = fx_rate_date or self._end_date
            h = self.find_currency_history(item.currency, date=fx_rate_date)
            fx_rate = getattr(h, 'fx_rate', 0.)
        item.balance_position += value
        item.principal_value_system_ccy += value * fx_rate
        item.market_value_system_ccy = item.principal_value_system_ccy

    def _process_instrument(self, t, case):
        if case == 0:
            instrument_item = self._get_item(t, instr=t.instrument, acc=t.account_position)
            instrument_item.balance_position += t.position_size_with_sign

        elif case == 1:
            instrument_item = self._get_item(t, instr=t.instrument, acc=t.account_position)
            instrument_item.balance_position += t.position_size_with_sign

        elif case == 2:
            pass

    def _process_cash(self, t, ccy, ccy_val, acc, acc_interim=None, case=None, fx_rate=None,
                      fx_rate_date=None):
        if case == 0:
            cash_item = self._get_item(t, ccy=ccy, acc=acc)
            self._add_cash(cash_item, ccy_val, fx_rate=fx_rate, fx_rate_date=fx_rate_date)

        elif case == 1:
            cash_item = self._get_item(t, ccy=ccy, acc=acc_interim, case=case)
            self._add_cash(cash_item, ccy_val, fx_rate=fx_rate, fx_rate_date=fx_rate_date)

        elif case == 2:
            cash_item = self._get_item(t, ccy=ccy, acc=acc)
            self._add_cash(cash_item, ccy_val, fx_rate=fx_rate, fx_rate_date=fx_rate_date)

            cash_item = self._get_item(t, ccy=ccy, acc=acc_interim, case=case)
            self._add_cash(cash_item, -ccy_val, fx_rate=fx_rate, fx_rate_date=fx_rate_date)

    def get_items(self):
        for t in self.transactions:
            t_class = t.transaction_class_id
            case = self._get_trn_case(t)

            if t_class == TransactionClass.CASH_INFLOW or t_class == TransactionClass.CASH_OUTFLOW:
                # Cash-Inflow/Cash-Outflow use transaction.reference_fx_rate

                cash_item = self._get_item(t, ccy=t.transaction_currency, acc=t.account_position)
                self._add_cash(cash_item, t.position_size_with_sign, fx_rate=t.reference_fx_rate)

                invested_item = self._get_invested_items(t, ccy=t.transaction_currency, acc=t.account_cash)
                self._add_cash(invested_item, t.position_size_with_sign, fx_rate=t.reference_fx_rate)

            elif t_class == TransactionClass.BUY or t_class == TransactionClass.SELL:
                if case == 0:
                    instrument_item = self._get_item(t, instr=t.instrument, acc=t.account_position)
                    instrument_item.balance_position += t.position_size_with_sign

                    cash_item = self._get_item(t, ccy=t.settlement_currency, acc=t.account_cash)
                    self._add_cash(cash_item, t.cash_consideration)

                elif case == 1:
                    instrument_item = self._get_item(t, instr=t.instrument, acc=t.account_position)
                    instrument_item.balance_position += t.position_size_with_sign

                    cash_item = self._get_item(t, ccy=t.settlement_currency, acc=t.account_interim, case=case)
                    self._add_cash(cash_item, t.cash_consideration)

                elif case == 2:
                    cash_item = self._get_item(t, ccy=t.settlement_currency, acc=t.account_cash)
                    self._add_cash(cash_item, t.cash_consideration)

                    cash_item = self._get_item(t, ccy=t.settlement_currency, acc=t.account_interim, case=case)
                    self._add_cash(cash_item, -t.cash_consideration)

            elif t_class == TransactionClass.INSTRUMENT_PL:
                # cash_item = self._get_item(t, ccy=t.settlement_currency, acc=t.account_cash)
                # self.add_cash(cash_item, t.cash_consideration)

                if case == 0:
                    cash_item = self._get_item(t, ccy=t.settlement_currency, acc=t.account_cash)
                    self._add_cash(cash_item, t.cash_consideration)

                elif case == 1:
                    cash_item = self._get_item(t, ccy=t.settlement_currency, acc=t.account_interim, case=case)
                    self._add_cash(cash_item, t.cash_consideration)

                elif case == 2:
                    cash_item = self._get_item(t, ccy=t.settlement_currency, acc=t.account_cash)
                    self._add_cash(cash_item, t.cash_consideration)

                    cash_item = self._get_item(t, ccy=t.settlement_currency, acc=t.account_interim, case=case)
                    self._add_cash(cash_item, -t.cash_consideration)

            elif t_class == TransactionClass.TRANSACTION_PL:
                # cash_item = self._get_item(t, ccy=t.settlement_currency, acc=t.account_cash, add_details=True)
                # self.add_cash(cash_item, t.cash_consideration)

                if case == 0:
                    cash_item = self._get_item(t, ccy=t.settlement_currency, acc=t.account_cash)
                    self._add_cash(cash_item, t.cash_consideration)

                elif case == 1:
                    cash_item = self._get_item(t, ccy=t.settlement_currency, acc=t.account_interim, case=case)
                    self._add_cash(cash_item, t.cash_consideration)

                elif case == 2:
                    cash_item = self._get_item(t, ccy=t.settlement_currency, acc=t.account_cash)
                    self._add_cash(cash_item, t.cash_consideration)

                    cash_item = self._get_item(t, ccy=t.settlement_currency, acc=t.account_interim, case=case)
                    self._add_cash(cash_item, -t.cash_consideration)

            elif t_class == TransactionClass.FX_TRADE:
                # Fx-Trade use fx-rate on transaction date
                # продублировать логику работу как с кэшь частью BUY/SELL, а не то как делали

                if case == 0:
                    cash_item = self._get_item(t, ccy=t.transaction_currency, acc=t.account_position)
                    self._add_cash(cash_item, t.position_size_with_sign, fx_rate_date=t.accounting_date)

                    cash_item = self._get_item(t, ccy=t.settlement_currency, acc=t.account_cash)
                    self._add_cash(cash_item, t.cash_consideration, fx_rate_date=t.accounting_date)

                elif case == 1:
                    cash_item = self._get_item(t, ccy=t.transaction_currency, acc=t.account_interim, case=case)
                    self._add_cash(cash_item, t.position_size_with_sign, fx_rate_date=t.accounting_date)

                    cash_item = self._get_item(t, ccy=t.settlement_currency, acc=t.account_interim, case=case)
                    self._add_cash(cash_item, t.cash_consideration, fx_rate_date=t.accounting_date)

                elif case == 2:
                    cash_item = self._get_item(t, ccy=t.transaction_currency, acc=t.account_position)
                    self._add_cash(cash_item, t.position_size_with_sign, fx_rate_date=t.accounting_date)

                    cash_item = self._get_item(t, ccy=t.transaction_currency, acc=t.account_interim, case=case)
                    self._add_cash(cash_item, -t.position_size_with_sign, fx_rate_date=t.accounting_date)

                    cash_item = self._get_item(t, ccy=t.settlement_currency, acc=t.account_cash)
                    self._add_cash(cash_item, t.cash_consideration, fx_rate_date=t.accounting_date)

                    cash_item = self._get_item(t, ccy=t.settlement_currency, acc=t.account_interim, case=case)
                    self._add_cash(cash_item, -t.cash_consideration, fx_rate_date=t.accounting_date)

        for i in six.itervalues(self._invested_items):
            if i.instrument:
                self.calc_balance_instrument(i)
                # elif i.currency:
                #     self.calc_balance_ccy(i)

        for i in six.itervalues(self._items):
            if i.instrument:
                self.calc_balance_instrument(i)
                # elif i.currency:
                #     self.calc_balance_ccy(i)

        invested_items = [i for i in six.itervalues(self._invested_items)]
        invested_items = sorted(invested_items, key=lambda x: x.pk)

        items = [i for i in six.itervalues(self._items)]
        items = sorted(items, key=lambda x: x.pk)

        return items, invested_items

    def build(self):
        items, invested_items = self.get_items()

        self.instance.invested_items = invested_items
        self.instance.items = items

        summary = self.instance.summary
        summary.invested_value_system_ccy = reduce(lambda x, y: x + y.market_value_system_ccy, invested_items, 0.)
        summary.current_value_system_ccy = reduce(lambda x, y: x + y.market_value_system_ccy, items, 0.)
        summary.p_l_system_ccy = summary.current_value_system_ccy - summary.invested_value_system_ccy

        self.instance.transactions = self.transactions

        return self.instance
