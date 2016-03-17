from __future__ import unicode_literals, division

from datetime import date

import pandas as pd
from django.contrib.auth.models import User
from django.test import TestCase

from poms.accounts.models import Account
from poms.currencies.models import Currency, CurrencyHistory
from poms.instruments.models import Instrument, PriceHistory
from poms.portfolios.models import Portfolio
from poms.reports.backends.balance import BalanceReport2Builder
from poms.reports.backends.pl import PLReport2Builder
from poms.reports.models import BalanceReport, PLReport
from poms.transactions.models import Transaction, TransactionClass
from poms.users.models import MasterUser


class BalanceTestCase(TestCase):
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
        usd = Currency.objects.create(user_code='USD', name='USD', master_user=None)
        eur = Currency.objects.create(user_code='EUR', name='EUR', master_user=None)
        chf = Currency.objects.create(user_code='CHF', name='CHF', master_user=None)
        cad = Currency.objects.create(user_code='CAD', name='CAD', master_user=None)
        mex = Currency.objects.create(user_code='MEX', name='MEX', master_user=None)
        rub = Currency.objects.create(user_code='RUB', name='RUB', master_user=None)
        gbp = Currency.objects.create(user_code='GBP', name='GBP', master_user=None)

        d = date(2016, 3, 1)
        CurrencyHistory.objects.create(currency=eur, date=d, fx_rate=1.3)
        CurrencyHistory.objects.create(currency=chf, date=d, fx_rate=0.9)
        CurrencyHistory.objects.create(currency=cad, date=d, fx_rate=1.2)
        CurrencyHistory.objects.create(currency=mex, date=d, fx_rate=0.15)
        CurrencyHistory.objects.create(currency=rub, date=d, fx_rate=1. / 75.)
        CurrencyHistory.objects.create(currency=gbp, date=d, fx_rate=1.6)

        instr1_bond_chf = Instrument.objects.create(master_user=m, name="instr1-bond, CHF",
                                                    pricing_currency=chf, price_multiplier=0.01,
                                                    accrued_currency=chf, accrued_multiplier=0.01)
        instr2_stock = Instrument.objects.create(master_user=m, name="instr2-stock",
                                                 pricing_currency=gbp, price_multiplier=1.,
                                                 accrued_currency=rub, accrued_multiplier=1.)

        PriceHistory.objects.create(instrument=instr1_bond_chf, date=d,
                                    principal_price=20., accrued_price=0.5)

        PriceHistory.objects.create(instrument=instr2_stock, date=d,
                                    principal_price=1.5, accrued_price=2)

        acc1 = Account.objects.create(master_user=m, name='Acc1')
        acc2 = Account.objects.create(master_user=m, name='Acc2')
        prov_acc1 = Account.objects.create(master_user=m, name='Prov Acc1')
        prov_acc2 = Account.objects.create(master_user=m, name='Prov Acc2')

        p1 = Portfolio.objects.create(master_user=m, name='p1')
        p2 = Portfolio.objects.create(master_user=m, name='p2')

        t1 = Transaction.objects.create(
            master_user=m,
            transaction_class=cash_inflow,
            portfolio=p1,
            instrument=None,
            transaction_currency=eur,
            position_size_with_sign=1000,
            settlement_currency=eur,  # TODO: must be None
            cash_consideration=0.,
            principal_with_sign=0.,
            carry_with_sign=0.,
            overheads_with_sign=0.,
            transaction_date=date(2016, 3, 1),
            accounting_date=date(2016, 3, 1),
            cash_date=date(2016, 3, 1),
            account_position=acc1,
            account_cash=acc1,
            account_interim=prov_acc1,
            reference_fx_rate=1.3
        )

        t2 = Transaction.objects.create(
            master_user=m,
            transaction_class=buy,
            portfolio=p1,
            instrument=instr1_bond_chf,
            transaction_currency=None,
            position_size_with_sign=100,
            settlement_currency=usd,
            cash_consideration=-200.,
            principal_with_sign=-180.,
            carry_with_sign=-5.,
            overheads_with_sign=-15.,
            transaction_date=date(2016, 3, 4),
            accounting_date=date(2016, 3, 4),
            cash_date=date(2016, 3, 6),
            account_position=acc1,
            account_cash=acc1,
            account_interim=prov_acc1,
            reference_fx_rate=None
        )

        t3 = Transaction.objects.create(
            master_user=m,
            transaction_class=sell,
            portfolio=p1,
            instrument=instr2_stock,
            transaction_currency=None,
            position_size_with_sign=-200,
            settlement_currency=rub,
            cash_consideration=1000.,
            principal_with_sign=1100.,
            carry_with_sign=0.,
            overheads_with_sign=-100.,
            transaction_date=date(2016, 3, 4),
            accounting_date=date(2016, 3, 6),
            cash_date=date(2016, 3, 4),
            account_position=acc1,
            account_cash=acc1,
            account_interim=prov_acc1,
            reference_fx_rate=None
        )

        t4 = Transaction.objects.create(
            master_user=m,
            transaction_class=cash_outflow,
            portfolio=p1,
            instrument=None,
            transaction_currency=rub,
            position_size_with_sign=-1000,
            settlement_currency=rub,  # TODO: must be None
            cash_consideration=0.,
            principal_with_sign=0,
            carry_with_sign=0.,
            overheads_with_sign=0.,
            transaction_date=date(2016, 3, 7),
            accounting_date=date(2016, 3, 7),
            cash_date=date(2016, 3, 7),
            account_position=acc1,
            account_cash=acc1,
            account_interim=prov_acc1,
            reference_fx_rate=1 / 75.
        )

        t5 = Transaction.objects.create(
            master_user=m,
            transaction_class=instrument_pl,
            portfolio=p1,
            instrument=instr2_stock,
            transaction_currency=None,
            position_size_with_sign=0.,
            settlement_currency=chf,
            cash_consideration=10.,
            principal_with_sign=0,
            carry_with_sign=11.,
            overheads_with_sign=-1.,
            transaction_date=date(2016, 3, 8),
            accounting_date=date(2016, 3, 8),
            cash_date=date(2016, 3, 8),
            account_position=acc1,
            account_cash=acc1,
            account_interim=prov_acc1,
            reference_fx_rate=None
        )

        t6 = Transaction.objects.create(
            master_user=m,
            transaction_class=instrument_pl,
            portfolio=p1,
            instrument=instr1_bond_chf,
            transaction_currency=None,
            position_size_with_sign=0.,
            settlement_currency=chf,
            cash_consideration=20.,
            principal_with_sign=0,
            carry_with_sign=20.,
            overheads_with_sign=0.,
            transaction_date=date(2016, 3, 9),
            accounting_date=date(2016, 3, 9),
            cash_date=date(2016, 3, 9),
            account_position=acc1,
            account_cash=acc1,
            account_interim=prov_acc1,
            reference_fx_rate=None
        )

        t7 = Transaction.objects.create(
            master_user=m,
            transaction_class=transaction_pl,
            portfolio=p1,
            instrument=None,
            transaction_currency=None,
            position_size_with_sign=0.,
            settlement_currency=rub,
            cash_consideration=-1000.,
            principal_with_sign=0,
            carry_with_sign=-900.,
            overheads_with_sign=-100.,
            transaction_date=date(2016, 3, 9),
            accounting_date=date(2016, 3, 9),
            cash_date=date(2016, 3, 9),
            account_position=acc1,
            account_cash=acc1,
            account_interim=prov_acc1,
            reference_fx_rate=None
        )

        t8 = Transaction.objects.create(
            master_user=m,
            transaction_class=fx_tade,
            portfolio=p1,
            instrument=None,
            transaction_currency=cad,
            position_size_with_sign=80.,
            settlement_currency=mex,
            cash_consideration=-150.,
            principal_with_sign=-140,
            carry_with_sign=0.,
            overheads_with_sign=-10.,
            transaction_date=date(2016, 3, 9),
            accounting_date=date(2016, 3, 9),
            cash_date=date(2016, 3, 9),
            account_position=acc1,
            account_cash=acc1,
            account_interim=prov_acc1,
            reference_fx_rate=None
        )

        self.trn_1 = [t1.pk, t2.pk, t3.pk, t4.pk]  # [inflow, buy, sell, outflow]
        self.trn_2 = [t1.pk, t2.pk, t3.pk, t4.pk, t5.pk, t6.pk, t7.pk]  # + [instr_pl, instr_pl, trn_pk]
        self.trn_3 = [t1.pk, t2.pk, t3.pk, t4.pk, t5.pk, t6.pk, t7.pk, t8.pk]  # + [fx trade]

    def _validate_balance(self, instance, instr_res, ccy_res, total_res):
        instr = {}
        ccy = {}
        for i in instance.items:
            portfolio = getattr(i.portfolio, 'name', None)
            account = getattr(i.account, 'name', None)

            v = "%.6f" % i.balance_position, "%.6f" % i.market_value_system_ccy
            if i.instrument:
                instr[portfolio, account, i.instrument.name] = v
            if i.currency:
                ccy[portfolio, account, i.currency.name] = v

        self.assertDictEqual(instr, instr_res, 'Instruments failed')

        self.assertDictEqual(ccy, ccy_res, 'Currencies failed')

        self.assertDictEqual({
            'invested_value_system_ccy': "%.6f" % instance.summary.invested_value_system_ccy,
            'current_value_system_ccy': "%.6f" % instance.summary.current_value_system_ccy,
            'p_l_system_ccy': "%.6f" % instance.summary.p_l_system_ccy,
        }, total_res, 'Summary failed')

    def _validate_pl(self, instance, instr_res, ext_res, total_res):
        instr = {}
        ext = {}
        for i in instance.items:
            portfolio = getattr(i.portfolio, 'name', None)
            account = getattr(i.account, 'name', None)
            v = "%.6f" % i.principal_with_sign_system_ccy, "%.6f" % i.carry_with_sign_system_ccy, \
                "%.6f" % i.overheads_with_sign_system_ccy, "%.6f" % i.total_system_ccy,
            if i.instrument:
                instr[portfolio, account, i.instrument.name] = v
            else:
                ext[portfolio, account, i.pk] = v

        self.assertDictEqual(instr, instr_res, 'Instruments failed')

        self.assertDictEqual(ext, ext_res, 'Ext rows failed')

        self.assertDictEqual({
            'principal_with_sign_system_ccy': "%.6f" % instance.summary.principal_with_sign_system_ccy,
            'carry_with_sign_system_ccy': "%.6f" % instance.summary.carry_with_sign_system_ccy,
            'overheads_with_sign_system_ccy': "%.6f" % instance.summary.overheads_with_sign_system_ccy,
            'total_system_ccy': "%.6f" % instance.summary.total_system_ccy,
        }, total_res, 'Summary failed')

    def _print_transactions(self, transactions, *columns):
        print('-' * 79)
        print('Transactions')
        data = []
        for t in transactions:
            data.append([getattr(t, c, None) for c in columns])
        print(pd.DataFrame(data=data, columns=columns))

    def _print_balance(self, instance):
        columns = ['portfolio', 'account', 'instrument', 'currency', 'position', 'market_value']
        data = []
        for i in instance.items:
            portfolio = i.portfolio
            acc = i.account
            instr = i.instrument
            ccy = i.currency
            data.append([
                getattr(portfolio, 'name', None),
                getattr(acc, 'name', None),
                getattr(instr, 'name', None),
                getattr(ccy, 'name', None),
                i.balance_position,
                i.market_value_system_ccy,
            ])
        print('-' * 79)
        print('Positions')
        print(pd.DataFrame(data=data, columns=columns))

        print('-' * 79)
        print('Summary')
        print(pd.DataFrame(
            data=[[instance.summary.invested_value_system_ccy, instance.summary.current_value_system_ccy,
                   instance.summary.p_l_system_ccy], ],
            columns=['invested_value_system_ccy', 'current_value_system_ccy', 'p_l_system_ccy']))

    def _print_pl(self, instance):
        columns = ['pk',
                   'portfolio', 'account', 'instrument',
                   'principal_with_sign_system_ccy', 'carry_with_sign_system_ccy', 'overheads_with_sign_system_ccy',
                   'total_system_ccy']
        data = []

        self.principal_with_sign_system_ccy = 0.
        self.carry_with_sign_system_ccy = 0.
        self.overheads_with_sign_system_ccy = 0.
        self.total_system_ccy = 0.

        for i in instance.items:
            portfolio = i.portfolio
            acc = i.account
            instr = i.instrument
            data.append([
                i.pk,
                getattr(portfolio, 'name', None),
                getattr(acc, 'name', None),
                getattr(instr, 'name', None),
                i.principal_with_sign_system_ccy,
                i.carry_with_sign_system_ccy,
                i.overheads_with_sign_system_ccy,
                i.total_system_ccy,
            ])
        print('-' * 79)
        print('Positions')
        print(pd.DataFrame(data=data, columns=columns))

        print('-' * 79)
        print('Summary')
        print(pd.DataFrame(
            data=[[instance.summary.principal_with_sign_system_ccy, instance.summary.carry_with_sign_system_ccy,
                   instance.summary.overheads_with_sign_system_ccy, instance.summary.total_system_ccy]],
            columns=['principal_with_sign_system_ccy', 'carry_with_sign_system_ccy', 'overheads_with_sign_system_ccy',
                     'total_system_ccy']))

    def test_balance1(self):
        queryset = Transaction.objects.filter(pk__in=self.trn_1)

        instance = BalanceReport(master_user=self.m,
                                 begin_date=None, end_date=None,
                                 use_portfolio=False, use_account=False,
                                 show_transaction_details=False)
        b = BalanceReport2Builder(instance=instance, queryset=queryset)
        b.build()
        self._print_balance(instance)
        self._validate_balance(instance,
                               instr_res={
                                   # name: position, market value
                                   (None, None, 'instr1-bond, CHF'): ("100.000000", "18.450000"),
                                   (None, None, 'instr2-stock'): ("-200.000000", "-485.333333"),
                               },
                               ccy_res={
                                   (None, None, 'USD'): ("-200.000000", "-200.000000"),
                                   (None, None, 'RUB'): ("0.000000", "0.000000"),
                                   (None, None, 'EUR'): ("1000.000000", "1300.000000"),
                               },
                               total_res={
                                   'invested_value_system_ccy': "1286.666667",
                                   'current_value_system_ccy': "633.116667",
                                   'p_l_system_ccy': "-653.550000",
                               })

        instance = BalanceReport(master_user=self.m,
                                 begin_date=None, end_date=date(2016, 3, 15),
                                 use_portfolio=False, use_account=True,
                                 show_transaction_details=False)
        b = BalanceReport2Builder(instance=instance, queryset=queryset)
        b.build()
        self._print_balance(instance)
        self._validate_balance(instance,
                               instr_res={
                                   # name: position, market value
                                   (None, 'Acc1', 'instr1-bond, CHF'): ("100.000000", "18.450000"),
                                   (None, 'Acc1', 'instr2-stock'): ("-200.000000", "-485.333333"),
                               },
                               ccy_res={
                                   (None, 'Acc1', 'USD'): ("-200.000000", "-200.000000"),
                                   (None, 'Acc1', 'RUB'): ("0.000000", "0.000000"),
                                   (None, 'Acc1', 'EUR'): ("1000.000000", "1300.000000"),
                               },
                               total_res={
                                   'invested_value_system_ccy': "1286.666667",
                                   'current_value_system_ccy': "633.116667",
                                   'p_l_system_ccy': "-653.550000",
                               })

        instance = BalanceReport(master_user=self.m,
                                 begin_date=None, end_date=date(2016, 3, 15),
                                 use_portfolio=True, use_account=True,
                                 show_transaction_details=False)
        b = BalanceReport2Builder(instance=instance, queryset=queryset)
        b.build()
        self._print_balance(instance)
        self._validate_balance(instance,
                               instr_res={
                                   # name: position, market value
                                   ('p1', 'Acc1', 'instr1-bond, CHF'): ("100.000000", "18.450000"),
                                   ('p1', 'Acc1', 'instr2-stock'): ("-200.000000", "-485.333333"),
                               },
                               ccy_res={
                                   ('p1', 'Acc1', 'USD'): ("-200.000000", "-200.000000"),
                                   ('p1', 'Acc1', 'RUB'): ("0.000000", "0.000000"),
                                   ('p1', 'Acc1', 'EUR'): ("1000.000000", "1300.000000"),
                               },
                               total_res={
                                   'invested_value_system_ccy': "1286.666667",
                                   'current_value_system_ccy': "633.116667",
                                   'p_l_system_ccy': "-653.550000",
                               })

    def test_balance2(self):
        queryset = Transaction.objects.filter(pk__in=self.trn_2)

        instance = BalanceReport(master_user=self.m,
                                 begin_date=None, end_date=date(2016, 3, 15),
                                 use_portfolio=False, use_account=False,
                                 show_transaction_details=False)
        b = BalanceReport2Builder(instance=instance, queryset=queryset)
        b.build()
        self._print_balance(instance)
        self._validate_balance(instance,
                               instr_res={
                                   # name: position, market value
                                   (None, None, 'instr1-bond, CHF'): ("100.000000", "18.450000"),
                                   (None, None, 'instr2-stock'): ("-200.000000", "-485.333333"),
                               },
                               ccy_res={
                                   (None, None, 'USD'): ("-200.000000", "-200.000000"),
                                   (None, None, 'EUR'): ("1000.000000", "1300.000000"),
                                   (None, None, 'CHF'): ("30.000000", "27.000000"),
                                   (None, None, 'RUB'): ("-1000.000000", "-13.333333"),
                               },
                               total_res={
                                   'invested_value_system_ccy': "1286.666667",
                                   'current_value_system_ccy': "646.783333",
                                   'p_l_system_ccy': "-639.883333",
                               })

        instance = BalanceReport(master_user=self.m,
                                 begin_date=None, end_date=date(2016, 3, 15),
                                 use_portfolio=False, use_account=True,
                                 show_transaction_details=False)
        b = BalanceReport2Builder(instance=instance, queryset=queryset)
        b.build()
        self._print_balance(instance)
        self._validate_balance(instance,
                               instr_res={
                                   # name: position, market value
                                   (None, 'Acc1', 'instr1-bond, CHF'): ("100.000000", "18.450000"),
                                   (None, 'Acc1', 'instr2-stock'): ("-200.000000", "-485.333333"),
                               },
                               ccy_res={
                                   (None, 'Acc1', 'USD'): ("-200.000000", "-200.000000"),
                                   (None, 'Acc1', 'EUR'): ("1000.000000", "1300.000000"),
                                   (None, 'Acc1', 'CHF'): ("30.000000", "27.000000"),
                                   (None, 'Acc1', 'RUB'): ("-1000.000000", "-13.333333"),
                               },
                               total_res={
                                   'invested_value_system_ccy': "1286.666667",
                                   'current_value_system_ccy': "646.783333",
                                   'p_l_system_ccy': "-639.883333",
                               })

        instance = BalanceReport(master_user=self.m,
                                 begin_date=None, end_date=date(2016, 3, 15),
                                 use_portfolio=True, use_account=True,
                                 show_transaction_details=False)
        b = BalanceReport2Builder(instance=instance, queryset=queryset)
        b.build()
        self._print_balance(instance)
        self._validate_balance(instance,
                               instr_res={
                                   # name: position, market value
                                   ('p1', 'Acc1', 'instr1-bond, CHF'): ("100.000000", "18.450000"),
                                   ('p1', 'Acc1', 'instr2-stock'): ("-200.000000", "-485.333333"),
                               },
                               ccy_res={
                                   ('p1', 'Acc1', 'USD'): ("-200.000000", "-200.000000"),
                                   ('p1', 'Acc1', 'EUR'): ("1000.000000", "1300.000000"),
                                   ('p1', 'Acc1', 'CHF'): ("30.000000", "27.000000"),
                                   ('p1', 'Acc1', 'RUB'): ("-1000.000000", "-13.333333"),
                               },
                               total_res={
                                   'invested_value_system_ccy': "1286.666667",
                                   'current_value_system_ccy': "646.783333",
                                   'p_l_system_ccy': "-639.883333",
                               })

    def test_balance3(self):
        queryset = Transaction.objects.filter(pk__in=self.trn_3)

        instance = BalanceReport(master_user=self.m,
                                 begin_date=None, end_date=date(2016, 3, 15),
                                 use_portfolio=False, use_account=False,
                                 show_transaction_details=False)
        b = BalanceReport2Builder(instance=instance, queryset=queryset)
        b.build()
        self._print_balance(instance)
        self._validate_balance(instance,
                               instr_res={
                                   # name: position, market value
                                   (None, None, 'instr1-bond, CHF'): ("100.000000", "18.450000"),
                                   (None, None, 'instr2-stock'): ("-200.000000", "-485.333333"),
                               },
                               ccy_res={
                                   (None, None, 'USD'): ("-200.000000", "-200.000000"),
                                   (None, None, 'EUR'): ("1000.000000", "1300.000000"),
                                   (None, None, 'CHF'): ("30.000000", "27.000000"),
                                   (None, None, 'RUB'): ("-1000.000000", "-13.333333"),
                                   (None, None, 'CAD'): ("80.000000", "96.000000"),
                                   (None, None, 'MEX'): ("-150.000000", "-22.500000"),
                               },
                               total_res={
                                   'invested_value_system_ccy': "1286.666667",
                                   'current_value_system_ccy': "720.283333",
                                   'p_l_system_ccy': "-566.383333",
                               })

        instance = BalanceReport(master_user=self.m,
                                 begin_date=None, end_date=date(2016, 3, 15),
                                 use_portfolio=False, use_account=True,
                                 show_transaction_details=False)
        b = BalanceReport2Builder(instance=instance, queryset=queryset)
        b.build()
        self._print_balance(instance)
        self._validate_balance(instance,
                               instr_res={
                                   # name: position, market value
                                   (None, 'Acc1', 'instr1-bond, CHF'): ("100.000000", "18.450000"),
                                   (None, 'Acc1', 'instr2-stock'): ("-200.000000", "-485.333333"),
                               },
                               ccy_res={
                                   (None, 'Acc1', 'USD'): ("-200.000000", "-200.000000"),
                                   (None, 'Acc1', 'EUR'): ("1000.000000", "1300.000000"),
                                   (None, 'Acc1', 'CHF'): ("30.000000", "27.000000"),
                                   (None, 'Acc1', 'RUB'): ("-1000.000000", "-13.333333"),
                                   (None, 'Acc1', 'CAD'): ("80.000000", "96.000000"),
                                   (None, 'Acc1', 'MEX'): ("-150.000000", "-22.500000"),
                               },
                               total_res={
                                   'invested_value_system_ccy': "1286.666667",
                                   'current_value_system_ccy': "720.283333",
                                   'p_l_system_ccy': "-566.383333",
                               })

        instance = BalanceReport(master_user=self.m,
                                 begin_date=None, end_date=date(2016, 3, 15),
                                 use_portfolio=True, use_account=True,
                                 show_transaction_details=False)
        b = BalanceReport2Builder(instance=instance, queryset=queryset)
        b.build()
        self._print_balance(instance)
        self._validate_balance(instance,
                               instr_res={
                                   # name: position, market value
                                   ('p1', 'Acc1', 'instr1-bond, CHF'): ("100.000000", "18.450000"),
                                   ('p1', 'Acc1', 'instr2-stock'): ("-200.000000", "-485.333333"),
                               },
                               ccy_res={
                                   ('p1', 'Acc1', 'USD'): ("-200.000000", "-200.000000"),
                                   ('p1', 'Acc1', 'EUR'): ("1000.000000", "1300.000000"),
                                   ('p1', 'Acc1', 'CHF'): ("30.000000", "27.000000"),
                                   ('p1', 'Acc1', 'RUB'): ("-1000.000000", "-13.333333"),
                                   ('p1', 'Acc1', 'CAD'): ("80.000000", "96.000000"),
                                   ('p1', 'Acc1', 'MEX'): ("-150.000000", "-22.500000"),
                               },
                               total_res={
                                   'invested_value_system_ccy': "1286.666667",
                                   'current_value_system_ccy': "720.283333",
                                   'p_l_system_ccy': "-566.383333",
                               })

    def test_balance1_w_dates(self):
        queryset = Transaction.objects.filter(pk__in=self.trn_1)
        instance = BalanceReport(master_user=self.m,
                                 begin_date=None, end_date=date(2016, 3, 5),
                                 use_portfolio=False, use_account=True,
                                 show_transaction_details=False)
        b = BalanceReport2Builder(instance=instance, queryset=queryset)
        b.build()

        self._print_transactions(b.transactions,
                                 'transaction_class',
                                 'portfolio',
                                 'instrument', 'transaction_currency',
                                 'position_size_with_sign',
                                 'settlement_currency',
                                 'cash_consideration',
                                 'accounting_date', 'cash_date')
        print('*' * 79)
        self._print_balance(instance)
        self._validate_balance(instance,
                               instr_res={
                                   # name: position, market value
                                   (None, 'Acc1', 'instr1-bond, CHF'): ("100.000000", "18.450000"),
                                   # (None, 'Acc1', 'instr2-stock'): ("-200.000000", "-485.333333"),
                               },
                               ccy_res={
                                   (None, 'Acc1', 'EUR'): ("1000.000000", "1300.000000"),
                                   (None, 'Prov Acc1', 'USD'): ("-200.000000", "-200.000000"),
                                   (None, 'Prov Acc1', 'RUB'): ("-1000.000000", "-13.333333"),
                               },
                               total_res={
                                   'invested_value_system_ccy': "1300.000000",
                                   'current_value_system_ccy': "1105.116667",
                                   'p_l_system_ccy': "-194.883333",
                               })

        queryset = Transaction.objects.filter(pk__in=self.trn_1)
        instance = BalanceReport(master_user=self.m,
                                 begin_date=None, end_date=date(2016, 3, 6),
                                 use_portfolio=False, use_account=True,
                                 show_transaction_details=False)
        b = BalanceReport2Builder(instance=instance, queryset=queryset)
        b.build()

        self._print_balance(instance)
        self._validate_balance(instance,
                               instr_res={
                                   # name: position, market value
                                   (None, 'Acc1', 'instr1-bond, CHF'): ("100.000000", "18.450000"),
                                   (None, 'Acc1', 'instr2-stock'): ("-200.000000", "-485.333333"),
                               },
                               ccy_res={
                                   (None, 'Acc1', 'EUR'): ("1000.000000", "1300.000000"),
                                   (None, 'Acc1', 'USD'): ("-200.000000", "-200.000000"),
                                   (None, 'Acc1', 'RUB'): ("1000.000000", "13.333333"),
                               },
                               total_res={
                                   'invested_value_system_ccy': "1300.000000",
                                   'current_value_system_ccy': "646.450000",
                                   'p_l_system_ccy': "-653.550000",
                               })

    def test_pl1(self):
        queryset = Transaction.objects.filter(pk__in=self.trn_2)

        instance = PLReport(master_user=self.m,
                            begin_date=None, end_date=None,
                            use_portfolio=False, use_account=False)
        b = PLReport2Builder(instance=instance, queryset=queryset)
        b.build()
        self._print_transactions(instance.transactions,
                                 'transaction_class',
                                 'portfolio',
                                 'instrument', 'transaction_currency',
                                 'position_size_with_sign',
                                 'settlement_currency',
                                 'cash_consideration',
                                 'principal_with_sign', 'carry_with_sign', 'overheads_with_sign',
                                 'principal_with_sign_system_ccy', 'carry_with_sign_system_ccy',
                                 'overheads_with_sign_system_ccy'
                                 )
        self._print_pl(instance)
        self._validate_pl(instance,
                          instr_res={
                              (None, None, 'instr1-bond, CHF'): (
                                  "-162.000000", "13.450000", '-15.000000', '-163.550000'),
                              (None, None, 'instr2-stock'): ("-465.333333", "4.566667", '-2.233333', '-463.000000'),
                          },
                          ext_res={
                              (None, None, 'Transaction PL'): ("0.000000", "-12.000000", '-1.333333', '-13.333333'),
                          },
                          total_res={
                              'principal_with_sign_system_ccy': "-627.333333",
                              'carry_with_sign_system_ccy': "6.016667",
                              'overheads_with_sign_system_ccy': "-18.566667",
                              'total_system_ccy': "-639.883333",
                          })


        instance = PLReport(master_user=self.m,
                            begin_date=None, end_date=None,
                            use_portfolio=False, use_account=True)
        b = PLReport2Builder(instance=instance, queryset=queryset)
        b.build()
        self._print_pl(instance)
        self._validate_pl(instance,
                          instr_res={
                              (None, 'Acc1', 'instr1-bond, CHF'): (
                                  "-162.000000", "13.450000", '-15.000000', '-163.550000'),
                              (None, 'Acc1', 'instr2-stock'): ("-465.333333", "4.566667", '-2.233333', '-463.000000'),
                          },
                          ext_res={
                              (None, 'Acc1', 'Transaction PL'): ("0.000000", "-12.000000", '-1.333333', '-13.333333'),
                          },
                          total_res={
                              'principal_with_sign_system_ccy': "-627.333333",
                              'carry_with_sign_system_ccy': "6.016667",
                              'overheads_with_sign_system_ccy': "-18.566667",
                              'total_system_ccy': "-639.883333",
                          })

        instance = PLReport(master_user=self.m,
                            begin_date=None, end_date=None,
                            use_portfolio=True, use_account=True)
        b = PLReport2Builder(instance=instance, queryset=queryset)
        b.build()
        self._print_pl(instance)
        self._validate_pl(instance,
                          instr_res={
                              ('p1', 'Acc1', 'instr1-bond, CHF'): (
                                  "-162.000000", "13.450000", '-15.000000', '-163.550000'),
                              ('p1', 'Acc1', 'instr2-stock'): ("-465.333333", "4.566667", '-2.233333', '-463.000000'),
                          },
                          ext_res={
                              ('p1', 'Acc1', 'Transaction PL'): ("0.000000", "-12.000000", '-1.333333', '-13.333333'),
                          },
                          total_res={
                              'principal_with_sign_system_ccy': "-627.333333",
                              'carry_with_sign_system_ccy': "6.016667",
                              'overheads_with_sign_system_ccy': "-18.566667",
                              'total_system_ccy': "-639.883333",
                          })

    def test_pl2(self):
        queryset = Transaction.objects.filter(pk__in=self.trn_3)

        instance = PLReport(master_user=self.m,
                            begin_date=None, end_date=None,
                            use_portfolio=False, use_account=False)
        b = PLReport2Builder(instance=instance, queryset=queryset)
        b.build()
        self._print_transactions(instance.transactions,
                                 'transaction_class',
                                 'portfolio',
                                 'instrument', 'transaction_currency',
                                 'position_size_with_sign',
                                 'settlement_currency',
                                 'cash_consideration',
                                 'principal_with_sign', 'carry_with_sign', 'overheads_with_sign',
                                 'principal_with_sign_system_ccy', 'carry_with_sign_system_ccy',
                                 'overheads_with_sign_system_ccy'
                                 )
        self._print_pl(instance)
        self._validate_pl(instance,
                          instr_res={
                              (None, None, 'instr1-bond, CHF'): (
                                  "-162.000000", "13.450000", '-15.000000', '-163.550000'),
                              (None, None, 'instr2-stock'): ("-465.333333", "4.566667", '-2.233333', '-463.000000'),
                          },
                          ext_res={
                              (None, None, 'FX Trade'): ("75.000000", "0.000000", '-1.500000', '73.500000'),
                              (None, None, 'Transaction PL'): ("0.000000", "-12.000000", '-1.333333', '-13.333333'),
                          },
                          total_res={
                              'principal_with_sign_system_ccy': "-552.333333",
                              'carry_with_sign_system_ccy': "6.016667",
                              'overheads_with_sign_system_ccy': "-20.066667",
                              'total_system_ccy': "-566.383333",
                          })
