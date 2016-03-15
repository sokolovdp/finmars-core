# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division

import logging
from datetime import date
from functools import reduce

import six

from poms.reports.backends.base import BaseReportBuilder
from poms.reports.models import BalanceReportItem
from poms.transactions.models import TransactionClass

_l = logging.getLogger('poms.reports')


# случаи 1 и 2 возможны для всех транзакций кроме Cash-Inflow/Outflow
# в т.ч. для Трансфер (чуть позже я поясню, что на самом деле Transfer = Sell + Buy)

class BalanceReportBuilder(BaseReportBuilder):
    def __init__(self, *args, **kwargs):
        super(BalanceReportBuilder, self).__init__(*args, **kwargs)
        self._filter_date_attr = 'accounting_date'

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
            case, account_position, account_cash = self.get_accounts(t)

            if t.transaction_class.code == TransactionClass.CASH_INFLOW:
                cash_item = self._get_currency_item(items, t.transaction_currency, account_position)
                cash_item.balance_position += t.position_size_with_sign

                invested_item = self._get_currency_item(invested_items, t.transaction_currency, account_position)
                invested_item.balance_position += t.position_size_with_sign
            elif t.transaction_class.code in [TransactionClass.BUY, TransactionClass.SELL]:
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
            elif t.transaction_class.code == TransactionClass.INSTRUMENT_PL:
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

                # i.instrument_name = i.instrument.name
                # i.instrument_principal_pricing_ccy = getattr(i.instrument.pricing_currency, 'name', None)
                i.instrument_price_multiplier = i.instrument.price_multiplier if i.instrument.price_multiplier is not None else 1.
                # i.instrument_accrued_pricing_ccy = getattr(i.instrument.accrued_currency, 'name', None)
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

        # # create balance items
        # for t in self.transactions:
        #     if t.transaction_class.code == TransactionClass.CASH_INFLOW:
        #         cash_item = self._get_currency_item(items, t.transaction_currency)
        #         cash_item.balance_position += t.position_size_with_sign
        #
        #         invested_item = self._get_currency_item(invested_items, t.transaction_currency)
        #         invested_item.balance_position += t.position_size_with_sign
        #     elif t.transaction_class.code in [TransactionClass.BUY, TransactionClass.SELL]:
        #         instrument_item = self._get_instrument_item(items, t.instrument)
        #         instrument_item.balance_position += t.position_size_with_sign
        #
        #         cash_item = self._get_currency_item(items, t.settlement_currency)
        #         cash_item.balance_position += t.cash_consideration
        #     elif t.transaction_class.code == TransactionClass.INSTRUMENT_PL:
        #         cash_item = self._get_currency_item(items, t.settlement_currency)
        #         cash_item.balance_position += t.cash_consideration

        self.instance.items = items

        self.instance.invested_items = invested_items

        summary = self.instance.summary
        summary.invested_value_system_ccy = reduce(lambda x, y: x + y.market_value_system_ccy, invested_items, 0.)
        summary.current_value_system_ccy = reduce(lambda x, y: x + y.market_value_system_ccy, items, 0.)
        summary.p_l_system_ccy = summary.current_value_system_ccy - summary.invested_value_system_ccy

        self.instance.transactions = self.transactions

        return self.instance
