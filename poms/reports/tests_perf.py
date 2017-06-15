import logging
import uuid
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils.functional import cached_property

from poms.accounts.models import AccountType, Account
from poms.currencies.models import Currency, CurrencyHistory
from poms.instruments.models import Instrument, PriceHistory, PricingPolicy, CostMethod, InstrumentType, \
    InstrumentClass, AccrualCalculationSchedule, AccrualCalculationModel, Periodicity, InstrumentFactorSchedule
from poms.portfolios.models import Portfolio
from poms.reports.builders.base_item import BaseReportItem
from poms.reports.builders.cash_flow_projection import CashFlowProjectionReportBuilder
from poms.reports.builders.cash_flow_projection_item import CashFlowProjectionReport
from poms.reports.builders.performance import PerformanceReportBuilder
from poms.reports.builders.performance_item import PerformanceReport
from poms.reports.tests_cf import AbstractReportTestMixin
from poms.strategies.models import Strategy1Group, Strategy1Subgroup, Strategy1, Strategy2Group, Strategy2Subgroup, \
    Strategy2, Strategy3Subgroup, Strategy3Group, Strategy3
from poms.transactions.models import Transaction, TransactionClass, TransactionType
from poms.users.models import MasterUser, Member

_l = logging.getLogger('poms.reports')


class PerfReportTestCase(AbstractReportTestMixin, TestCase):
    def _dumps(self, items):
        _l.info('Items: \n %s',
                BaseReportItem.sdumps(
                    items=items,
                    columns=[
                        'period_begin',
                        'period_end',
                        # 'period_name',
                        # 'period_key',
                        # 'portfolio',
                        'account',
                        # 'strategy1',
                        # 'strategy2',
                        # 'strategy3',
                        'return_pl',
                        'return_nav',
                        'accumulated_pl',
                        'pl_in_period',
                        'nav_change',
                        'nav_period_start',
                        'nav_period_end',
                        'cash_inflows',
                        'cash_outflows',
                        'time_weighted_cash_inflows',
                        'time_weighted_cash_outflows',
                        'avg_nav_in_period',
                        'cumulative_return_pl',
                        'cumulative_return_nav'
                    ],
                    transpose=True
                ))

    def test_perf1(self):
        # settings.DEBUG = True

        i1 = Instrument.objects.create(
            master_user=self.m,
            user_code='i1',
            instrument_type=self.m.instrument_type,
            pricing_currency=self.usd,
            price_multiplier=1.0,
            accrued_currency=self.usd,
            accrued_multiplier=1.0,
            maturity_date=date(2103, 1, 1),
            maturity_price=1000,
        )
        self._instr_hist(i1, date(2020, 1, 31), 1, 1)
        self._instr_hist(i1, date(2020, 2, 29), 1, 1)

        self._t_buy(
            instr=i1, position=10,
            stl_ccy=self.usd, principal=-10, carry=0, overheads=-1,
            acc_pos=self.a1_1, acc_cash=self.a1_2,
            acc_date=date(2020, 1, 10), cash_date=date(2020, 1, 10)
        )

        # self._t_buy(
        #     instr=i1, position=10,
        #     stl_ccy=self.usd, principal=-20, carry=0, overheads=-1,
        #     acc_pos=self.a1_1, acc_cash=self.a1_2,
        #     acc_date=date(2020, 2, 10), cash_date=date(2020, 2, 10)
        # )

        report = PerformanceReport(
            master_user=self.m,
            member=self.mm,
            begin_date=date(2020, 1, 1),
            end_date=date(2020, 12, 31),
            report_currency=self.usd,
            pricing_policy=self.pp,
            periods='date_group(transaction.accounting_date,[[None,None,timedelta(months=1),["[","%Y-%m-%d","/","","%Y-%m-%d","]"]]], "Err")',
        )
        report_builder = PerformanceReportBuilder(report)
        report_builder.build_performance()
        self._dumps(report.items)
