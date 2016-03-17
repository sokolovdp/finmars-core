from __future__ import unicode_literals, division

import pandas as pd

from poms.reports.backends.pl import PLReport2Builder
from poms.reports.models import PLReport, PLReportSummary, PLReportInstrument
from poms.reports.tests.base import BaseReportTestCase, n
from poms.transactions.models import Transaction, TransactionClass


class BalanceTestCase(BaseReportTestCase):
    def _print_pl_transactions(self, transactions):
        self._print_transactions(
            transactions,
            'transaction_class',
            'portfolio',
            'instrument', 'transaction_currency',
            'position_size_with_sign',
            'settlement_currency', 'cash_consideration',
            'principal_with_sign', 'carry_with_sign', 'overheads_with_sign',
            'principal_with_sign_system_ccy', 'carry_with_sign_system_ccy',
            'overheads_with_sign_system_ccy'
        )

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

    def _assertEqualPL(self, result, expected):
        self.assertEqual(len(result.items), len(expected.items), 'len items')

        r_expected = {i.pk: i for i in expected.items}

        for ri in result.items:
            ei = r_expected.pop(ri.pk)

            self.assertEqual(ri.portfolio, ei.portfolio, '%s - portfolio' % ri.pk)
            self.assertEqual(ri.account, ei.account, '%s - account' % ri.pk)
            self.assertEqual(ri.instrument, ei.instrument, '%s - instrument' % ri.pk)

            self.assertEqual(n(ri.principal_with_sign_system_ccy), n(ei.principal_with_sign_system_ccy),
                             '%s - principal_with_sign_system_ccy' % ri.pk)
            self.assertEqual(n(ri.carry_with_sign_system_ccy), n(ei.carry_with_sign_system_ccy),
                             '%s - carry_with_sign_system_ccy' % ri.pk)
            self.assertEqual(n(ri.overheads_with_sign_system_ccy), n(ei.overheads_with_sign_system_ccy),
                             '%s - overheads_with_sign_system_ccy' % ri.pk)
            self.assertEqual(n(ri.total_system_ccy), n(ei.total_system_ccy),
                             '%s - total_system_ccy' % ri.pk)

        self.assertEqual(n(result.summary.principal_with_sign_system_ccy),
                         n(expected.summary.principal_with_sign_system_ccy),
                         'principal_with_sign_system_ccy')
        self.assertEqual(n(result.summary.carry_with_sign_system_ccy),
                         n(expected.summary.carry_with_sign_system_ccy),
                         'carry_with_sign_system_ccy')
        self.assertEqual(n(result.summary.overheads_with_sign_system_ccy),
                         n(expected.summary.overheads_with_sign_system_ccy),
                         'overheads_with_sign_system_ccy')
        self.assertEqual(n(result.summary.total_system_ccy),
                         n(expected.summary.total_system_ccy),
                         'total_system_ccy')

    def test_simple_w_trnpl(self):
        queryset = Transaction.objects.filter(pk__in=self.simple_w_trnpl)

        instance = PLReport(master_user=self.m,
                            begin_date=None, end_date=None,
                            use_portfolio=False, use_account=False)
        b = PLReport2Builder(instance=instance, queryset=queryset)
        b.build()
        self._print_pl_transactions(instance.transactions)
        self._print_pl(instance)
        self._assertEqualPL(instance, PLReport(
            items=[
                PLReportInstrument(pk=b.make_key(None, None, self.instr1_bond_chf, None),
                                   portfolio=None, account=None, instrument=self.instr1_bond_chf,
                                   principal_with_sign_system_ccy=-162.000000, carry_with_sign_system_ccy=13.450000,
                                   overheads_with_sign_system_ccy=-15.000000, total_system_ccy=-163.550000),
                PLReportInstrument(pk=b.make_key(None, None, self.instr2_stock, None),
                                   portfolio=None, account=None, instrument=self.instr2_stock,
                                   principal_with_sign_system_ccy=-465.333333, carry_with_sign_system_ccy=4.566667,
                                   overheads_with_sign_system_ccy=-2.233333, total_system_ccy=-463.000000),
                PLReportInstrument(pk=b.make_key(None, None, None, None, TransactionClass.TRANSACTION_PL),
                                   portfolio=None, account=None, instrument=None,
                                   principal_with_sign_system_ccy=0.000000, carry_with_sign_system_ccy=-12.000000,
                                   overheads_with_sign_system_ccy=-1.333333, total_system_ccy=-13.333333),
            ],
            summary=PLReportSummary(principal_with_sign_system_ccy=-627.333333,
                                    carry_with_sign_system_ccy=6.016667,
                                    overheads_with_sign_system_ccy=-18.566667,
                                    total_system_ccy=-639.883333)
        ))

        instance = PLReport(master_user=self.m,
                            begin_date=None, end_date=None,
                            use_portfolio=False, use_account=True)
        b = PLReport2Builder(instance=instance, queryset=queryset)
        b.build()
        self._print_pl(instance)
        self._assertEqualPL(instance, PLReport(
            items=[
                PLReportInstrument(pk=b.make_key(None, self.acc1, self.instr1_bond_chf, None),
                                   portfolio=None, account=self.acc1, instrument=self.instr1_bond_chf,
                                   principal_with_sign_system_ccy=-162.000000, carry_with_sign_system_ccy=13.450000,
                                   overheads_with_sign_system_ccy=-15.000000, total_system_ccy=-163.550000),
                PLReportInstrument(pk=b.make_key(None, self.acc1, self.instr2_stock, None),
                                   portfolio=None, account=self.acc1, instrument=self.instr2_stock,
                                   principal_with_sign_system_ccy=-465.333333, carry_with_sign_system_ccy=4.566667,
                                   overheads_with_sign_system_ccy=-2.233333, total_system_ccy=-463.000000),
                PLReportInstrument(pk=b.make_key(None, self.acc1, None, None, TransactionClass.TRANSACTION_PL),
                                   portfolio=None, account=self.acc1, instrument=None,
                                   principal_with_sign_system_ccy=0.000000, carry_with_sign_system_ccy=-12.000000,
                                   overheads_with_sign_system_ccy=-1.333333, total_system_ccy=-13.333333),
            ],
            summary=PLReportSummary(principal_with_sign_system_ccy=-627.333333,
                                    carry_with_sign_system_ccy=6.016667,
                                    overheads_with_sign_system_ccy=-18.566667,
                                    total_system_ccy=-639.883333)
        ))

        instance = PLReport(master_user=self.m,
                            begin_date=None, end_date=None,
                            use_portfolio=True, use_account=True)
        b = PLReport2Builder(instance=instance, queryset=queryset)
        b.build()
        self._print_pl(instance)
        self._assertEqualPL(instance, PLReport(
            items=[
                PLReportInstrument(pk=b.make_key(self.p1, self.acc1, self.instr1_bond_chf, None),
                                   portfolio=self.p1, account=self.acc1, instrument=self.instr1_bond_chf,
                                   principal_with_sign_system_ccy=-162.000000, carry_with_sign_system_ccy=13.450000,
                                   overheads_with_sign_system_ccy=-15.000000, total_system_ccy=-163.550000),
                PLReportInstrument(pk=b.make_key(self.p1, self.acc1, self.instr2_stock, None),
                                   portfolio=self.p1, account=self.acc1, instrument=self.instr2_stock,
                                   principal_with_sign_system_ccy=-465.333333, carry_with_sign_system_ccy=4.566667,
                                   overheads_with_sign_system_ccy=-2.233333, total_system_ccy=-463.000000),
                PLReportInstrument(pk=b.make_key(self.p1, self.acc1, None, None, TransactionClass.TRANSACTION_PL),
                                   portfolio=self.p1, account=self.acc1, instrument=None,
                                   principal_with_sign_system_ccy=0.000000, carry_with_sign_system_ccy=-12.000000,
                                   overheads_with_sign_system_ccy=-1.333333, total_system_ccy=-13.333333),
            ],
            summary=PLReportSummary(principal_with_sign_system_ccy=-627.333333,
                                    carry_with_sign_system_ccy=6.016667,
                                    overheads_with_sign_system_ccy=-18.566667,
                                    total_system_ccy=-639.883333)
        ))

    def test_simple_w_fxtrade(self):
        queryset = Transaction.objects.filter(pk__in=self.simple_w_fxtrade)

        instance = PLReport(master_user=self.m,
                            begin_date=None, end_date=None,
                            use_portfolio=False, use_account=False)
        b = PLReport2Builder(instance=instance, queryset=queryset)
        b.build()
        self._print_pl_transactions(instance.transactions)
        self._print_pl(instance)
        self._assertEqualPL(instance, PLReport(
            items=[
                PLReportInstrument(pk=b.make_key(None, None, self.instr1_bond_chf, None),
                                   portfolio=None, account=None, instrument=self.instr1_bond_chf,
                                   principal_with_sign_system_ccy=-162.000000, carry_with_sign_system_ccy=13.450000,
                                   overheads_with_sign_system_ccy=-15.000000, total_system_ccy=-163.550000),
                PLReportInstrument(pk=b.make_key(None, None, self.instr2_stock, None),
                                   portfolio=None, account=None, instrument=self.instr2_stock,
                                   principal_with_sign_system_ccy=-465.333333, carry_with_sign_system_ccy=4.566667,
                                   overheads_with_sign_system_ccy=-2.233333, total_system_ccy=-463.000000),
                PLReportInstrument(pk=b.make_key(None, None, None, None, TransactionClass.TRANSACTION_PL),
                                   portfolio=None, account=None, instrument=None,
                                   principal_with_sign_system_ccy=0.000000, carry_with_sign_system_ccy=-12.000000,
                                   overheads_with_sign_system_ccy=-1.333333, total_system_ccy=-13.333333),
                PLReportInstrument(pk=b.make_key(None, None, None, None, TransactionClass.FX_TRADE),
                                   portfolio=None, account=None, instrument=None,
                                   principal_with_sign_system_ccy=75.000000, carry_with_sign_system_ccy=0.000000,
                                   overheads_with_sign_system_ccy=-1.500000, total_system_ccy=73.500000),
            ],
            summary=PLReportSummary(principal_with_sign_system_ccy=-552.333333,
                                    carry_with_sign_system_ccy=6.016667,
                                    overheads_with_sign_system_ccy=-20.066667,
                                    total_system_ccy=-566.383333)
        ))
