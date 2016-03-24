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

    def _get_item0(self, items, trn, instr_attr=None, ccy_attr=None, acc_attr=None, ext=None):
        t_key = self._get_transaction_key(trn, instr_attr, ccy_attr, acc_attr, ext=ext)
        try:
            return items[t_key]
        except KeyError:
            portfolio = trn.portfolio if self._use_portfolio else None
            account = getattr(trn, acc_attr, None) if acc_attr and self._use_account else None
            instrument = getattr(trn, instr_attr, None) if instr_attr else None
            currency = getattr(trn, ccy_attr, None) if ccy_attr else None
            item = BalanceReportItem(pk=t_key, portfolio=portfolio, account=account, instrument=instrument,
                                     currency=currency)
            items[t_key] = item
            return item

    def _get_item(self, trn, instr_attr=None, ccy_attr=None, acc_attr=None, ext=None):
        return self._get_item0(self._items, trn, instr_attr=instr_attr, ccy_attr=ccy_attr, acc_attr=acc_attr, ext=ext)

    def _get_invested_items(self, trn, instr_attr=None, ccy_attr=None, acc_attr=None):
        return self._get_item0(self._invested_items, trn, instr_attr=instr_attr, ccy_attr=ccy_attr, acc_attr=acc_attr)

    def get_accounts(self, trn):
        accounting_date, cash_date = trn.accounting_date, trn.cash_date
        if cash_date is None:
            cash_date = date.max

        if accounting_date <= self._end_date < cash_date:  # default
            return 1, 'account_position', 'account_interim'
        elif cash_date <= self._end_date < accounting_date:
            return 2, None, 'account_interim'
        else:
            return 0, 'account_position', 'account_cash'

    def is_show_details(self, trn, acc_atr):
        if self.instance.show_transaction_details:
            acc = getattr(trn, acc_atr, None)
            return acc and acc.type and acc.type.show_transaction_details
        return False

    def add_cash(self, item, value, fx_rate=None, date=None):
        if fx_rate is None:
            date = date or self._end_date
            h = self.find_currency_history(item.currency, date=date)
            fx_rate = getattr(h, 'fx_rate', 0.)
        item.balance_position += value
        item.principal_value_system_ccy += value * fx_rate
        item.market_value_system_ccy = item.principal_value_system_ccy

    def get_items(self):
        for t in self.transactions:
            t_class = t.transaction_class_id
            case, acc_pos_attr, acc_cash_attr = self.get_accounts(t)

            if t_class in [TransactionClass.CASH_INFLOW, TransactionClass.CASH_OUTFLOW]:
                # TODO: Cash-Inflow/Cash-Outflow use transaction.reference_fx_rate

                cash_item = self._get_item(t, ccy_attr='transaction_currency', acc_attr=acc_pos_attr)
                # cash_item.balance_position += t.position_size_with_sign
                self.add_cash(cash_item, t.position_size_with_sign, fx_rate=t.reference_fx_rate)

                invested_item = self._get_invested_items(t, ccy_attr='transaction_currency', acc_attr=acc_pos_attr)
                # invested_item.balance_position += t.position_size_with_sign
                self.add_cash(invested_item, t.position_size_with_sign, fx_rate=t.reference_fx_rate)

            elif t_class in [TransactionClass.BUY, TransactionClass.SELL]:
                if case == 0 or case == 1:
                    instrument_item = self._get_item(t, instr_attr='instrument', acc_attr=acc_pos_attr)
                    instrument_item.balance_position += t.position_size_with_sign

                # cash_item = self._get_item(t, ccy_attr='settlement_currency', acc_attr=acc_cash_attr)
                if case in [1, 2] and self.is_show_details(t, acc_cash_attr):
                    cash_item = self._get_item(t, ccy_attr='settlement_currency', acc_attr=acc_cash_attr, ext=t.id)
                    cash_item.transaction = t
                else:
                    cash_item = self._get_item(t, ccy_attr='settlement_currency', acc_attr=acc_cash_attr)

                if case == 0 or case == 1:
                    # cash_item.balance_position += t.cash_consideration
                    self.add_cash(cash_item, t.cash_consideration)
                elif case == 2:
                    # cash_item.balance_position += -t.cash_consideration
                    self.add_cash(cash_item, -t.cash_consideration)

            elif t_class in [TransactionClass.INSTRUMENT_PL]:
                # cash_item = self._get_item(t, ccy_attr='settlement_currency', acc_attr=acc_cash_attr)
                if case in [1, 2] and self.is_show_details(t, acc_cash_attr):
                    cash_item = self._get_item(t, ccy_attr='settlement_currency', acc_attr=acc_cash_attr, ext=t.id)
                    cash_item.transaction = t
                else:
                    cash_item = self._get_item(t, ccy_attr='settlement_currency', acc_attr=acc_cash_attr)

                if case == 0 or case == 1:
                    # cash_item.balance_position += t.cash_consideration
                    self.add_cash(cash_item, t.cash_consideration)
                elif case == 2:
                    # cash_item.balance_position += -t.cash_consideration
                    self.add_cash(cash_item, -t.cash_consideration)

            elif t_class in [TransactionClass.TRANSACTION_PL]:
                # cash_item = self._get_item(t, ccy_attr='settlement_currency', acc_attr=acc_cash_attr)
                if case in [1, 2] and self.is_show_details(t, acc_cash_attr):
                    cash_item = self._get_item(t, ccy_attr='settlement_currency', acc_attr=acc_cash_attr, ext=t.id)
                    cash_item.transaction = t
                else:
                    cash_item = self._get_item(t, ccy_attr='settlement_currency', acc_attr=acc_cash_attr)

                if case == 0 or case == 1:
                    # cash_item.balance_position += t.cash_consideration
                    self.add_cash(cash_item, t.cash_consideration)
                elif case == 2:
                    # cash_item.balance_position += -t.cash_consideration
                    self.add_cash(cash_item, -t.cash_consideration)

            elif t_class in [TransactionClass.FX_TRADE]:
                # TODO: Fx-Trade use fx-rate on transaction date
                instrument_item = self._get_item(t, ccy_attr='transaction_currency', acc_attr=acc_pos_attr)
                # instrument_item.balance_position += t.position_size_with_sign
                self.add_cash(instrument_item, t.position_size_with_sign, date=t.accounting_date)

                cash_item = self._get_item(t, ccy_attr='settlement_currency', acc_attr=acc_cash_attr)
                # cash_item.balance_position += t.cash_consideration
                self.add_cash(cash_item, t.cash_consideration, date=t.accounting_date)

                # if case == 0 or case == 1:
                #     instrument_item = self._get_item(t, ccy_attr='transaction_currency', acc_attr=acc_pos_attr)
                #     instrument_item.balance_position += t.position_size_with_sign
                # if case == 0 or case == 1:
                #     cash_item.balance_position += t.cash_consideration
                # elif case == 2:
                #     cash_item.balance_position += -t.cash_consideration

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
