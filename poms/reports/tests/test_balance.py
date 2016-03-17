from __future__ import unicode_literals, division

from datetime import date

import pandas as pd

from poms.reports.backends.balance import BalanceReport2Builder
from poms.reports.models import BalanceReport, BalanceReportItem, BalanceReportSummary
from poms.reports.tests.base import BaseReportTestCase, n
from poms.transactions.models import Transaction


class BalanceTestCase(BaseReportTestCase):
    def _print_balance_transactions(self, transactions):
        self._print_transactions(
            transactions,
            'transaction_class',
            'portfolio',
            'instrument', 'transaction_currency',
            'position_size_with_sign',
            'settlement_currency', 'cash_consideration',
            'accounting_date', 'cash_date')

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

    def _assertEqualBalance(self, result, expected):
        self.assertEqual(len(result.items), len(expected.items), 'len items')

        r_expected = {i.pk: i for i in expected.items}

        for ri in result.items:
            ei = r_expected.pop(ri.pk)

            self.assertEqual(ri.portfolio, ei.portfolio, '%s - portfolio' % ri.pk)
            self.assertEqual(ri.account, ei.account, '%s - account' % ri.pk)
            self.assertEqual(ri.instrument, ei.instrument, '%s - instrument' % ri.pk)
            self.assertEqual(ri.currency, ei.currency, '%s - currency' % ri.pk)

            self.assertEqual(n(ri.balance_position), n(ei.balance_position),
                             '%s - balance_position' % ri.pk)
            self.assertEqual(n(ri.market_value_system_ccy), n(ei.market_value_system_ccy),
                             '%s - market_value_system_ccy' % ri.pk)

        self.assertEqual(n(result.summary.invested_value_system_ccy), n(expected.summary.invested_value_system_ccy),
                         'invested_value_system_ccy')
        self.assertEqual(n(result.summary.current_value_system_ccy), n(expected.summary.current_value_system_ccy),
                         'current_value_system_ccy')
        self.assertEqual(n(result.summary.p_l_system_ccy), n(expected.summary.p_l_system_ccy),
                         'p_l_system_ccy')

    def test_balance1(self):
        queryset = Transaction.objects.filter(pk__in=self.trn_1)

        instance = BalanceReport(master_user=self.m,
                                 begin_date=None, end_date=None,
                                 use_portfolio=False, use_account=False,
                                 show_transaction_details=False)
        b = BalanceReport2Builder(instance=instance, queryset=queryset)
        b.build()
        self._print_balance(instance)

        self._assertEqualBalance(instance, BalanceReport(
            items=[
                BalanceReportItem(pk=b.make_key(None, None, self.instr1_bond_chf, None),
                                  portfolio=None, account=None, instrument=self.instr1_bond_chf, currency=None,
                                  balance_position=100.000000, market_value_system_ccy=18.450000),
                BalanceReportItem(pk=b.make_key(None, None, self.instr2_stock, None),
                                  portfolio=None, account=None, instrument=self.instr2_stock, currency=None,
                                  balance_position=-200.000000, market_value_system_ccy=-485.333333),

                BalanceReportItem(pk=b.make_key(None, None, None, self.usd),
                                  portfolio=None, account=None, instrument=None, currency=self.usd,
                                  balance_position=-200.000000, market_value_system_ccy=-200.000000),
                BalanceReportItem(pk=b.make_key(None, None, None, self.rub),
                                  portfolio=None, account=None, instrument=None, currency=self.rub,
                                  balance_position=0.000000, market_value_system_ccy=0.000000),
                BalanceReportItem(pk=b.make_key(None, None, None, self.eur),
                                  portfolio=None, account=None, instrument=None, currency=self.eur,
                                  balance_position=1000.000000, market_value_system_ccy=1300.000000),
            ],
            summary=BalanceReportSummary(invested_value_system_ccy=1286.666667,
                                         current_value_system_ccy=633.116667,
                                         p_l_system_ccy=-653.550000)
        ))

        instance = BalanceReport(master_user=self.m,
                                 begin_date=None, end_date=date(2016, 3, 15),
                                 use_portfolio=False, use_account=True,
                                 show_transaction_details=False)
        b = BalanceReport2Builder(instance=instance, queryset=queryset)
        b.build()
        self._print_balance(instance)
        self._assertEqualBalance(instance, BalanceReport(
            items=[
                BalanceReportItem(pk=b.make_key(None, self.acc1, self.instr1_bond_chf, None),
                                  portfolio=None, account=self.acc1, instrument=self.instr1_bond_chf, currency=None,
                                  balance_position=100.000000, market_value_system_ccy=18.450000),
                BalanceReportItem(pk=b.make_key(None, self.acc1, self.instr2_stock, None),
                                  portfolio=None, account=self.acc1, instrument=self.instr2_stock, currency=None,
                                  balance_position=-200.000000, market_value_system_ccy=-485.333333),

                BalanceReportItem(pk=b.make_key(None, self.acc1, None, self.usd),
                                  portfolio=None, account=self.acc1, instrument=None, currency=self.usd,
                                  balance_position=-200.000000, market_value_system_ccy=-200.000000),
                BalanceReportItem(pk=b.make_key(None, self.acc1, None, self.rub),
                                  portfolio=None, account=self.acc1, instrument=None, currency=self.rub,
                                  balance_position=0.000000, market_value_system_ccy=0.000000),
                BalanceReportItem(pk=b.make_key(None, self.acc1, None, self.eur),
                                  portfolio=None, account=self.acc1, instrument=None, currency=self.eur,
                                  balance_position=1000.000000, market_value_system_ccy=1300.000000),
            ],
            summary=BalanceReportSummary(invested_value_system_ccy=1286.666667,
                                         current_value_system_ccy=633.116667,
                                         p_l_system_ccy=-653.550000)
        ))

        instance = BalanceReport(master_user=self.m,
                                 begin_date=None, end_date=date(2016, 3, 15),
                                 use_portfolio=True, use_account=True,
                                 show_transaction_details=False)
        b = BalanceReport2Builder(instance=instance, queryset=queryset)
        b.build()
        self._print_balance(instance)
        self._assertEqualBalance(instance, BalanceReport(
            items=[
                BalanceReportItem(pk=b.make_key(self.p1, self.acc1, self.instr1_bond_chf, None),
                                  portfolio=self.p1, account=self.acc1, instrument=self.instr1_bond_chf, currency=None,
                                  balance_position=100.000000, market_value_system_ccy=18.450000),
                BalanceReportItem(pk=b.make_key(self.p1, self.acc1, self.instr2_stock, None),
                                  portfolio=self.p1, account=self.acc1, instrument=self.instr2_stock, currency=None,
                                  balance_position=-200.000000, market_value_system_ccy=-485.333333),

                BalanceReportItem(pk=b.make_key(self.p1, self.acc1, None, self.usd),
                                  portfolio=self.p1, account=self.acc1, instrument=None, currency=self.usd,
                                  balance_position=-200.000000, market_value_system_ccy=-200.000000),
                BalanceReportItem(pk=b.make_key(self.p1, self.acc1, None, self.rub),
                                  portfolio=self.p1, account=self.acc1, instrument=None, currency=self.rub,
                                  balance_position=0.000000, market_value_system_ccy=0.000000),
                BalanceReportItem(pk=b.make_key(self.p1, self.acc1, None, self.eur),
                                  portfolio=self.p1, account=self.acc1, instrument=None, currency=self.eur,
                                  balance_position=1000.000000, market_value_system_ccy=1300.000000),
            ],
            summary=BalanceReportSummary(invested_value_system_ccy=1286.666667,
                                         current_value_system_ccy=633.116667,
                                         p_l_system_ccy=-653.550000)
        ))

    def test_balance2(self):
        queryset = Transaction.objects.filter(pk__in=self.trn_2)

        instance = BalanceReport(master_user=self.m,
                                 begin_date=None, end_date=date(2016, 3, 15),
                                 use_portfolio=False, use_account=False,
                                 show_transaction_details=False)
        b = BalanceReport2Builder(instance=instance, queryset=queryset)
        b.build()
        self._print_balance(instance)
        self._assertEqualBalance(instance, BalanceReport(
            items=[
                BalanceReportItem(pk=b.make_key(None, None, self.instr1_bond_chf, None),
                                  portfolio=None, account=None, instrument=self.instr1_bond_chf, currency=None,
                                  balance_position=100.000000, market_value_system_ccy=18.450000),
                BalanceReportItem(pk=b.make_key(None, None, self.instr2_stock, None),
                                  portfolio=None, account=None, instrument=self.instr2_stock, currency=None,
                                  balance_position=-200.000000, market_value_system_ccy=-485.333333),

                BalanceReportItem(pk=b.make_key(None, None, None, self.usd),
                                  portfolio=None, account=None, instrument=None, currency=self.usd,
                                  balance_position=-200.000000, market_value_system_ccy=-200.000000),
                BalanceReportItem(pk=b.make_key(None, None, None, self.eur),
                                  portfolio=None, account=None, instrument=None, currency=self.eur,
                                  balance_position=1000.000000, market_value_system_ccy=1300.000000),
                BalanceReportItem(pk=b.make_key(None, None, None, self.chf),
                                  portfolio=None, account=None, instrument=None, currency=self.chf,
                                  balance_position=30.000000, market_value_system_ccy=27.000000),
                BalanceReportItem(pk=b.make_key(None, None, None, self.rub),
                                  portfolio=None, account=None, instrument=None, currency=self.rub,
                                  balance_position=-1000.000000, market_value_system_ccy=-13.333333),
            ],
            summary=BalanceReportSummary(invested_value_system_ccy=1286.666667,
                                         current_value_system_ccy=646.783333,
                                         p_l_system_ccy=-639.883333)
        ))

        instance = BalanceReport(master_user=self.m,
                                 begin_date=None, end_date=date(2016, 3, 15),
                                 use_portfolio=False, use_account=True,
                                 show_transaction_details=False)
        b = BalanceReport2Builder(instance=instance, queryset=queryset)
        b.build()
        self._print_balance(instance)
        self._assertEqualBalance(instance, BalanceReport(
            items=[
                BalanceReportItem(pk=b.make_key(None, self.acc1, self.instr1_bond_chf, None),
                                  portfolio=None, account=self.acc1, instrument=self.instr1_bond_chf, currency=None,
                                  balance_position=100.000000, market_value_system_ccy=18.450000),
                BalanceReportItem(pk=b.make_key(None, self.acc1, self.instr2_stock, None),
                                  portfolio=None, account=self.acc1, instrument=self.instr2_stock, currency=None,
                                  balance_position=-200.000000, market_value_system_ccy=-485.333333),

                BalanceReportItem(pk=b.make_key(None, self.acc1, None, self.usd),
                                  portfolio=None, account=self.acc1, instrument=None, currency=self.usd,
                                  balance_position=-200.000000, market_value_system_ccy=-200.000000),
                BalanceReportItem(pk=b.make_key(None, self.acc1, None, self.eur),
                                  portfolio=None, account=self.acc1, instrument=None, currency=self.eur,
                                  balance_position=1000.000000, market_value_system_ccy=1300.000000),
                BalanceReportItem(pk=b.make_key(None, self.acc1, None, self.chf),
                                  portfolio=None, account=self.acc1, instrument=None, currency=self.chf,
                                  balance_position=30.000000, market_value_system_ccy=27.000000),
                BalanceReportItem(pk=b.make_key(None, self.acc1, None, self.rub),
                                  portfolio=None, account=self.acc1, instrument=None, currency=self.rub,
                                  balance_position=-1000.000000, market_value_system_ccy=-13.333333),
            ],
            summary=BalanceReportSummary(invested_value_system_ccy=1286.666667,
                                         current_value_system_ccy=646.783333,
                                         p_l_system_ccy=-639.883333)
        ))

        instance = BalanceReport(master_user=self.m,
                                 begin_date=None, end_date=date(2016, 3, 15),
                                 use_portfolio=True, use_account=True,
                                 show_transaction_details=False)
        b = BalanceReport2Builder(instance=instance, queryset=queryset)
        b.build()
        self._print_balance(instance)
        self._assertEqualBalance(instance, BalanceReport(
            items=[
                BalanceReportItem(pk=b.make_key(self.p1, self.acc1, self.instr1_bond_chf, None),
                                  portfolio=self.p1, account=self.acc1, instrument=self.instr1_bond_chf, currency=None,
                                  balance_position=100.000000, market_value_system_ccy=18.450000),
                BalanceReportItem(pk=b.make_key(self.p1, self.acc1, self.instr2_stock, None),
                                  portfolio=self.p1, account=self.acc1, instrument=self.instr2_stock, currency=None,
                                  balance_position=-200.000000, market_value_system_ccy=-485.333333),

                BalanceReportItem(pk=b.make_key(self.p1, self.acc1, None, self.usd),
                                  portfolio=self.p1, account=self.acc1, instrument=None, currency=self.usd,
                                  balance_position=-200.000000, market_value_system_ccy=-200.000000),
                BalanceReportItem(pk=b.make_key(self.p1, self.acc1, None, self.eur),
                                  portfolio=self.p1, account=self.acc1, instrument=None, currency=self.eur,
                                  balance_position=1000.000000, market_value_system_ccy=1300.000000),
                BalanceReportItem(pk=b.make_key(self.p1, self.acc1, None, self.chf),
                                  portfolio=self.p1, account=self.acc1, instrument=None, currency=self.chf,
                                  balance_position=30.000000, market_value_system_ccy=27.000000),
                BalanceReportItem(pk=b.make_key(self.p1, self.acc1, None, self.rub),
                                  portfolio=self.p1, account=self.acc1, instrument=None, currency=self.rub,
                                  balance_position=-1000.000000, market_value_system_ccy=-13.333333),
            ],
            summary=BalanceReportSummary(invested_value_system_ccy=1286.666667,
                                         current_value_system_ccy=646.783333,
                                         p_l_system_ccy=-639.883333)
        ))

    def test_balance3(self):
        queryset = Transaction.objects.filter(pk__in=self.trn_3)

        instance = BalanceReport(master_user=self.m,
                                 begin_date=None, end_date=date(2016, 3, 15),
                                 use_portfolio=False, use_account=False,
                                 show_transaction_details=False)
        b = BalanceReport2Builder(instance=instance, queryset=queryset)
        b.build()
        self._print_balance(instance)
        self._assertEqualBalance(instance, BalanceReport(
            items=[
                BalanceReportItem(pk=b.make_key(None, None, self.instr1_bond_chf, None),
                                  portfolio=None, account=None, instrument=self.instr1_bond_chf, currency=None,
                                  balance_position=100.000000, market_value_system_ccy=18.450000),
                BalanceReportItem(pk=b.make_key(None, None, self.instr2_stock, None),
                                  portfolio=None, account=None, instrument=self.instr2_stock, currency=None,
                                  balance_position=-200.000000, market_value_system_ccy=-485.333333),

                BalanceReportItem(pk=b.make_key(None, None, None, self.usd),
                                  portfolio=None, account=None, instrument=None, currency=self.usd,
                                  balance_position=-200.000000, market_value_system_ccy=-200.000000),
                BalanceReportItem(pk=b.make_key(None, None, None, self.eur),
                                  portfolio=None, account=None, instrument=None, currency=self.eur,
                                  balance_position=1000.000000, market_value_system_ccy=1300.000000),
                BalanceReportItem(pk=b.make_key(None, None, None, self.chf),
                                  portfolio=None, account=None, instrument=None, currency=self.chf,
                                  balance_position=30.000000, market_value_system_ccy=27.000000),
                BalanceReportItem(pk=b.make_key(None, None, None, self.rub),
                                  portfolio=None, account=None, instrument=None, currency=self.rub,
                                  balance_position=-1000.000000, market_value_system_ccy=-13.333333),
                BalanceReportItem(pk=b.make_key(None, None, None, self.cad),
                                  portfolio=None, account=None, instrument=None, currency=self.cad,
                                  balance_position=80.000000, market_value_system_ccy=96.000000),
                BalanceReportItem(pk=b.make_key(None, None, None, self.mex),
                                  portfolio=None, account=None, instrument=None, currency=self.mex,
                                  balance_position=-150.000000, market_value_system_ccy=-22.500000),
            ],
            summary=BalanceReportSummary(invested_value_system_ccy=1286.666667,
                                         current_value_system_ccy=720.283333,
                                         p_l_system_ccy=-566.383333)
        ))

        instance = BalanceReport(master_user=self.m,
                                 begin_date=None, end_date=date(2016, 3, 15),
                                 use_portfolio=False, use_account=True,
                                 show_transaction_details=False)
        b = BalanceReport2Builder(instance=instance, queryset=queryset)
        b.build()
        self._print_balance(instance)
        self._assertEqualBalance(instance, BalanceReport(
            items=[
                BalanceReportItem(pk=b.make_key(None, self.acc1, self.instr1_bond_chf, None),
                                  portfolio=None, account=self.acc1, instrument=self.instr1_bond_chf, currency=None,
                                  balance_position=100.000000, market_value_system_ccy=18.450000),
                BalanceReportItem(pk=b.make_key(None, self.acc1, self.instr2_stock, None),
                                  portfolio=None, account=self.acc1, instrument=self.instr2_stock, currency=None,
                                  balance_position=-200.000000, market_value_system_ccy=-485.333333),

                BalanceReportItem(pk=b.make_key(None, self.acc1, None, self.usd),
                                  portfolio=None, account=self.acc1, instrument=None, currency=self.usd,
                                  balance_position=-200.000000, market_value_system_ccy=-200.000000),
                BalanceReportItem(pk=b.make_key(None, self.acc1, None, self.eur),
                                  portfolio=None, account=self.acc1, instrument=None, currency=self.eur,
                                  balance_position=1000.000000, market_value_system_ccy=1300.000000),
                BalanceReportItem(pk=b.make_key(None, self.acc1, None, self.chf),
                                  portfolio=None, account=self.acc1, instrument=None, currency=self.chf,
                                  balance_position=30.000000, market_value_system_ccy=27.000000),
                BalanceReportItem(pk=b.make_key(None, self.acc1, None, self.rub),
                                  portfolio=None, account=self.acc1, instrument=None, currency=self.rub,
                                  balance_position=-1000.000000, market_value_system_ccy=-13.333333),
                BalanceReportItem(pk=b.make_key(None, self.acc1, None, self.cad),
                                  portfolio=None, account=self.acc1, instrument=None, currency=self.cad,
                                  balance_position=80.000000, market_value_system_ccy=96.000000),
                BalanceReportItem(pk=b.make_key(None, self.acc1, None, self.mex),
                                  portfolio=None, account=self.acc1, instrument=None, currency=self.mex,
                                  balance_position=-150.000000, market_value_system_ccy=-22.500000),
            ],
            summary=BalanceReportSummary(invested_value_system_ccy=1286.666667,
                                         current_value_system_ccy=720.283333,
                                         p_l_system_ccy=-566.383333)
        ))

        instance = BalanceReport(master_user=self.m,
                                 begin_date=None, end_date=date(2016, 3, 15),
                                 use_portfolio=True, use_account=True,
                                 show_transaction_details=False)
        b = BalanceReport2Builder(instance=instance, queryset=queryset)
        b.build()
        self._print_balance(instance)
        self._assertEqualBalance(instance, BalanceReport(
            items=[
                BalanceReportItem(pk=b.make_key(self.p1, self.acc1, self.instr1_bond_chf, None),
                                  portfolio=self.p1, account=self.acc1, instrument=self.instr1_bond_chf, currency=None,
                                  balance_position=100.000000, market_value_system_ccy=18.450000),
                BalanceReportItem(pk=b.make_key(self.p1, self.acc1, self.instr2_stock, None),
                                  portfolio=self.p1, account=self.acc1, instrument=self.instr2_stock, currency=None,
                                  balance_position=-200.000000, market_value_system_ccy=-485.333333),

                BalanceReportItem(pk=b.make_key(self.p1, self.acc1, None, self.usd),
                                  portfolio=self.p1, account=self.acc1, instrument=None, currency=self.usd,
                                  balance_position=-200.000000, market_value_system_ccy=-200.000000),
                BalanceReportItem(pk=b.make_key(self.p1, self.acc1, None, self.eur),
                                  portfolio=self.p1, account=self.acc1, instrument=None, currency=self.eur,
                                  balance_position=1000.000000, market_value_system_ccy=1300.000000),
                BalanceReportItem(pk=b.make_key(self.p1, self.acc1, None, self.chf),
                                  portfolio=self.p1, account=self.acc1, instrument=None, currency=self.chf,
                                  balance_position=30.000000, market_value_system_ccy=27.000000),
                BalanceReportItem(pk=b.make_key(self.p1, self.acc1, None, self.rub),
                                  portfolio=self.p1, account=self.acc1, instrument=None, currency=self.rub,
                                  balance_position=-1000.000000, market_value_system_ccy=-13.333333),
                BalanceReportItem(pk=b.make_key(self.p1, self.acc1, None, self.cad),
                                  portfolio=self.p1, account=self.acc1, instrument=None, currency=self.cad,
                                  balance_position=80.000000, market_value_system_ccy=96.000000),
                BalanceReportItem(pk=b.make_key(self.p1, self.acc1, None, self.mex),
                                  portfolio=self.p1, account=self.acc1, instrument=None, currency=self.mex,
                                  balance_position=-150.000000, market_value_system_ccy=-22.500000),
            ],
            summary=BalanceReportSummary(invested_value_system_ccy=1286.666667,
                                         current_value_system_ccy=720.283333,
                                         p_l_system_ccy=-566.383333)
        ))

    def test_balance1_w_dates(self):
        queryset = Transaction.objects.filter(pk__in=self.trn_1)
        instance = BalanceReport(master_user=self.m,
                                 begin_date=None, end_date=date(2016, 3, 5),
                                 use_portfolio=False, use_account=True,
                                 show_transaction_details=False)
        b = BalanceReport2Builder(instance=instance, queryset=queryset)
        b.build()
        self._print_balance_transactions(instance.transactions)
        self._print_balance(instance)
        self._assertEqualBalance(instance, BalanceReport(
            items=[
                BalanceReportItem(pk=b.make_key(None, self.acc1, self.instr1_bond_chf, None),
                                  portfolio=None, account=self.acc1, instrument=self.instr1_bond_chf, currency=None,
                                  balance_position=100.000000, market_value_system_ccy=18.450000),

                BalanceReportItem(pk=b.make_key(None, self.acc1, None, self.eur),
                                  portfolio=None, account=self.acc1, instrument=None, currency=self.eur,
                                  balance_position=1000.000000, market_value_system_ccy=1300.000000),
                BalanceReportItem(pk=b.make_key(None, self.prov_acc1, None, self.usd),
                                  portfolio=None, account=self.prov_acc1, instrument=None, currency=self.usd,
                                  balance_position=-200.000000, market_value_system_ccy=-200.000000),
                BalanceReportItem(pk=b.make_key(None, self.prov_acc1, None, self.rub),
                                  portfolio=None, account=self.prov_acc1, instrument=None, currency=self.rub,
                                  balance_position=-1000.000000, market_value_system_ccy=-13.333333),
            ],
            summary=BalanceReportSummary(invested_value_system_ccy=1300.000000,
                                         current_value_system_ccy=1105.116667,
                                         p_l_system_ccy=-194.883333)
        ))

        queryset = Transaction.objects.filter(pk__in=self.trn_1)
        instance = BalanceReport(master_user=self.m,
                                 begin_date=None, end_date=date(2016, 3, 6),
                                 use_portfolio=False, use_account=True,
                                 show_transaction_details=False)
        b = BalanceReport2Builder(instance=instance, queryset=queryset)
        b.build()

        self._print_balance(instance)
        self._assertEqualBalance(instance, BalanceReport(
            items=[
                BalanceReportItem(pk=b.make_key(None, self.acc1, self.instr1_bond_chf, None),
                                  portfolio=None, account=self.acc1, instrument=self.instr1_bond_chf, currency=None,
                                  balance_position=100.000000, market_value_system_ccy=18.450000),
                BalanceReportItem(pk=b.make_key(None, self.acc1, self.instr2_stock, None),
                                  portfolio=None, account=self.acc1, instrument=self.instr2_stock, currency=None,
                                  balance_position=-200.000000, market_value_system_ccy=-485.333333),

                BalanceReportItem(pk=b.make_key(None, self.acc1, None, self.eur),
                                  portfolio=None, account=self.acc1, instrument=None, currency=self.eur,
                                  balance_position=1000.000000, market_value_system_ccy=1300.000000),
                BalanceReportItem(pk=b.make_key(None, self.acc1, None, self.usd),
                                  portfolio=None, account=self.acc1, instrument=None, currency=self.usd,
                                  balance_position=-200.000000, market_value_system_ccy=-200.000000),
                BalanceReportItem(pk=b.make_key(None, self.acc1, None, self.rub),
                                  portfolio=None, account=self.acc1, instrument=None, currency=self.rub,
                                  balance_position=1000.000000, market_value_system_ccy=13.333333),
            ],
            summary=BalanceReportSummary(invested_value_system_ccy=1300.000000,
                                         current_value_system_ccy=646.450000,
                                         p_l_system_ccy=-653.550000)
        ))
