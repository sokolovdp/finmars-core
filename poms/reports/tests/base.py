from __future__ import unicode_literals, division

from datetime import date

import pandas as pd
from django.contrib.auth.models import User
from django.test import TestCase

from poms.accounts.models import Account
from poms.currencies.models import Currency, CurrencyHistory
from poms.instruments.models import Instrument, PriceHistory
from poms.portfolios.models import Portfolio
from poms.transactions.models import Transaction, TransactionClass
from poms.users.models import MasterUser


def n(v):
    return "%.6f" % v


class BaseReportTestCase(TestCase):
    def setUp(self):
        pd.set_option('display.width', 1000)

        u = User.objects.create_user('a')
        self.m = m = MasterUser.objects.create(user=u)

        cash_inflow = TransactionClass.objects.create(code=TransactionClass.CASH_INFLOW,
                                                      name=TransactionClass.CASH_INFLOW)
        cash_outflow = TransactionClass.objects.create(code=TransactionClass.CASH_OUTFLOW,
                                                       name=TransactionClass.CASH_OUTFLOW)
        buy = TransactionClass.objects.create(code=TransactionClass.BUY,
                                              name=TransactionClass.BUY)
        sell = TransactionClass.objects.create(code=TransactionClass.SELL,
                                               name=TransactionClass.SELL)
        instrument_pl = TransactionClass.objects.create(code=TransactionClass.INSTRUMENT_PL,
                                                        name=TransactionClass.INSTRUMENT_PL)
        transaction_pl = TransactionClass.objects.create(code=TransactionClass.TRANSACTION_PL,
                                                         name=TransactionClass.TRANSACTION_PL)
        fx_tade = TransactionClass.objects.create(code=TransactionClass.FX_TRADE,
                                                  name=TransactionClass.FX_TRADE)

        ccy_ = Currency.objects.create(user_code='-', master_user=None)
        self.usd = Currency.objects.create(user_code='USD', name='USD', master_user=None)
        self.eur = Currency.objects.create(user_code='EUR', name='EUR', master_user=None)
        self.chf = Currency.objects.create(user_code='CHF', name='CHF', master_user=None)
        self.cad = Currency.objects.create(user_code='CAD', name='CAD', master_user=None)
        self.mex = Currency.objects.create(user_code='MEX', name='MEX', master_user=None)
        self.rub = Currency.objects.create(user_code='RUB', name='RUB', master_user=None)
        self.gbp = Currency.objects.create(user_code='GBP', name='GBP', master_user=None)

        d = date(2016, 3, 1)
        CurrencyHistory.objects.create(currency=self.eur, date=d, fx_rate=1.3)
        CurrencyHistory.objects.create(currency=self.chf, date=d, fx_rate=0.9)
        CurrencyHistory.objects.create(currency=self.cad, date=d, fx_rate=1.2)
        CurrencyHistory.objects.create(currency=self.mex, date=d, fx_rate=0.15)
        CurrencyHistory.objects.create(currency=self.rub, date=d, fx_rate=1. / 75.)
        CurrencyHistory.objects.create(currency=self.gbp, date=d, fx_rate=1.6)

        self.instr1_bond_chf = Instrument.objects.create(master_user=m, name="instr1-bond, CHF",
                                                         pricing_currency=self.chf, price_multiplier=0.01,
                                                         accrued_currency=self.chf, accrued_multiplier=0.01)
        self.instr2_stock = Instrument.objects.create(master_user=m, name="instr2-stock",
                                                      pricing_currency=self.gbp, price_multiplier=1.,
                                                      accrued_currency=self.rub, accrued_multiplier=1.)

        PriceHistory.objects.create(instrument=self.instr1_bond_chf, date=d,
                                    principal_price=20., accrued_price=0.5)

        PriceHistory.objects.create(instrument=self.instr2_stock, date=d,
                                    principal_price=1.5, accrued_price=2)

        self.acc1 = Account.objects.create(master_user=m, name='Acc1')
        self.acc2 = Account.objects.create(master_user=m, name='Acc2')
        self.prov_acc1 = Account.objects.create(master_user=m, name='Prov Acc1')
        self.prov_acc2 = Account.objects.create(master_user=m, name='Prov Acc2')

        self.p1 = Portfolio.objects.create(master_user=m, name='p1')
        self.p2 = Portfolio.objects.create(master_user=m, name='p2')

        t1 = Transaction.objects.create(
            master_user=m,
            transaction_class=cash_inflow,
            portfolio=self.p1,
            instrument=None,
            transaction_currency=self.eur,
            position_size_with_sign=1000,
            settlement_currency=self.eur,  # TODO: must be None
            cash_consideration=0.,
            principal_with_sign=0.,
            carry_with_sign=0.,
            overheads_with_sign=0.,
            transaction_date=date(2016, 3, 1),
            accounting_date=date(2016, 3, 1),
            cash_date=date(2016, 3, 1),
            account_position=self.acc1,
            account_cash=self.acc1,
            account_interim=self.prov_acc1,
            reference_fx_rate=1.3
        )

        t2 = Transaction.objects.create(
            master_user=m,
            transaction_class=buy,
            portfolio=self.p1,
            instrument=self.instr1_bond_chf,
            transaction_currency=None,
            position_size_with_sign=100,
            settlement_currency=self.usd,
            cash_consideration=-200.,
            principal_with_sign=-180.,
            carry_with_sign=-5.,
            overheads_with_sign=-15.,
            transaction_date=date(2016, 3, 4),
            accounting_date=date(2016, 3, 4),
            cash_date=date(2016, 3, 6),
            account_position=self.acc1,
            account_cash=self.acc1,
            account_interim=self.prov_acc1,
            reference_fx_rate=None
        )

        t3 = Transaction.objects.create(
            master_user=m,
            transaction_class=sell,
            portfolio=self.p1,
            instrument=self.instr2_stock,
            transaction_currency=None,
            position_size_with_sign=-200,
            settlement_currency=self.rub,
            cash_consideration=1000.,
            principal_with_sign=1100.,
            carry_with_sign=0.,
            overheads_with_sign=-100.,
            transaction_date=date(2016, 3, 4),
            accounting_date=date(2016, 3, 6),
            cash_date=date(2016, 3, 4),
            account_position=self.acc1,
            account_cash=self.acc1,
            account_interim=self.prov_acc1,
            reference_fx_rate=None
        )

        t4 = Transaction.objects.create(
            master_user=m,
            transaction_class=cash_outflow,
            portfolio=self.p1,
            instrument=None,
            transaction_currency=self.rub,
            position_size_with_sign=-1000,
            settlement_currency=self.rub,  # TODO: must be None
            cash_consideration=0.,
            principal_with_sign=0,
            carry_with_sign=0.,
            overheads_with_sign=0.,
            transaction_date=date(2016, 3, 7),
            accounting_date=date(2016, 3, 7),
            cash_date=date(2016, 3, 7),
            account_position=self.acc1,
            account_cash=self.acc1,
            account_interim=self.prov_acc1,
            reference_fx_rate=1 / 75.
        )

        t5 = Transaction.objects.create(
            master_user=m,
            transaction_class=instrument_pl,
            portfolio=self.p1,
            instrument=self.instr2_stock,
            transaction_currency=None,
            position_size_with_sign=0.,
            settlement_currency=self.chf,
            cash_consideration=10.,
            principal_with_sign=0,
            carry_with_sign=11.,
            overheads_with_sign=-1.,
            transaction_date=date(2016, 3, 8),
            accounting_date=date(2016, 3, 8),
            cash_date=date(2016, 3, 8),
            account_position=self.acc1,
            account_cash=self.acc1,
            account_interim=self.prov_acc1,
            reference_fx_rate=None
        )

        t6 = Transaction.objects.create(
            master_user=m,
            transaction_class=instrument_pl,
            portfolio=self.p1,
            instrument=self.instr1_bond_chf,
            transaction_currency=None,
            position_size_with_sign=0.,
            settlement_currency=self.chf,
            cash_consideration=20.,
            principal_with_sign=0,
            carry_with_sign=20.,
            overheads_with_sign=0.,
            transaction_date=date(2016, 3, 9),
            accounting_date=date(2016, 3, 9),
            cash_date=date(2016, 3, 9),
            account_position=self.acc1,
            account_cash=self.acc1,
            account_interim=self.prov_acc1,
            reference_fx_rate=None
        )

        t7 = Transaction.objects.create(
            master_user=m,
            transaction_class=transaction_pl,
            portfolio=self.p1,
            instrument=None,
            transaction_currency=None,
            position_size_with_sign=0.,
            settlement_currency=self.rub,
            cash_consideration=-1000.,
            principal_with_sign=0,
            carry_with_sign=-900.,
            overheads_with_sign=-100.,
            transaction_date=date(2016, 3, 9),
            accounting_date=date(2016, 3, 9),
            cash_date=date(2016, 3, 9),
            account_position=self.acc1,
            account_cash=self.acc1,
            account_interim=self.prov_acc1,
            reference_fx_rate=None
        )

        t8 = Transaction.objects.create(
            master_user=m,
            transaction_class=fx_tade,
            portfolio=self.p1,
            instrument=None,
            transaction_currency=self.cad,
            position_size_with_sign=80.,
            settlement_currency=self.mex,
            cash_consideration=-150.,
            principal_with_sign=-140,
            carry_with_sign=0.,
            overheads_with_sign=-10.,
            transaction_date=date(2016, 3, 9),
            accounting_date=date(2016, 3, 9),
            cash_date=date(2016, 3, 9),
            account_position=self.acc1,
            account_cash=self.acc1,
            account_interim=self.prov_acc1,
            reference_fx_rate=None
        )

        self.trn_1 = [t1.pk, t2.pk, t3.pk, t4.pk]  # [inflow, buy, sell, outflow]
        self.trn_2 = [t1.pk, t2.pk, t3.pk, t4.pk, t5.pk, t6.pk, t7.pk]  # + [instr_pl, instr_pl, trn_pk]
        self.trn_3 = [t1.pk, t2.pk, t3.pk, t4.pk, t5.pk, t6.pk, t7.pk, t8.pk]  # + [fx trade]

    def _print_transactions(self, transactions, *columns):
        print('-' * 79)
        print('Transactions')
        data = []
        for t in transactions:
            data.append([getattr(t, c, None) for c in columns])
        print(pd.DataFrame(data=data, columns=columns))
