from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils.functional import cached_property

from poms.accounts.models import AccountType, Account
from poms.currencies.models import Currency, CurrencyHistory
from poms.instruments.models import Instrument, PriceHistory, PricingPolicy
from poms.portfolios.models import Portfolio
from poms.reports.builders import Report, ReportBuilder
from poms.strategies.models import Strategy1Group, Strategy1Subgroup, Strategy1
from poms.transactions.models import Transaction, TransactionClass
from poms.users.models import MasterUser

try:
    import pandas
except ImportError:
    pandas = None


class ReportTestCase(TestCase):
    def setUp(self):
        if pandas:
            pandas.set_option('display.width', 2000)
            pandas.set_option('display.max_rows', 2000)
            pandas.set_option('precision', 4)

        self.report_date = date(2016, 3, 1)

        user = User.objects.create_user('a1')
        self.m = MasterUser.objects.create_master_user(user=user, name='a1_m1')

        self.pp = PricingPolicy.objects.create(master_user=self.m)

        self.usd = self.m.system_currency
        self.eur, _ = Currency.objects.get_or_create(user_code='EUR', master_user=self.m, defaults={'name': 'EUR'})
        self.chf, _ = Currency.objects.get_or_create(user_code='CHF', master_user=self.m, defaults={'name': 'CHF'})
        self.cad, _ = Currency.objects.get_or_create(user_code='CAD', master_user=self.m, defaults={'name': 'CAD'})
        self.mex, _ = Currency.objects.get_or_create(user_code='MEX', master_user=self.m, defaults={'name': 'MEX'})
        self.rub, _ = Currency.objects.get_or_create(user_code='RUB', master_user=self.m, defaults={'name': 'RUB'})
        self.gbp, _ = Currency.objects.get_or_create(user_code='GBP', master_user=self.m, defaults={'name': 'GBP'})

        for days in range(0, 29):
            d = self._d(days)
            CurrencyHistory.objects.create(currency=self.eur, pricing_policy=self.pp, date=d, fx_rate=1.3)
            CurrencyHistory.objects.create(currency=self.chf, pricing_policy=self.pp, date=d, fx_rate=0.9)
            CurrencyHistory.objects.create(currency=self.cad, pricing_policy=self.pp, date=d, fx_rate=1.2)
            CurrencyHistory.objects.create(currency=self.mex, pricing_policy=self.pp, date=d, fx_rate=0.15)
            CurrencyHistory.objects.create(currency=self.rub, pricing_policy=self.pp, date=d, fx_rate=1. / 75.)
            CurrencyHistory.objects.create(currency=self.gbp, pricing_policy=self.pp, date=d, fx_rate=1.6)

        d = self._d(30)
        CurrencyHistory.objects.create(currency=self.eur, pricing_policy=self.pp, date=d, fx_rate=1.2)
        CurrencyHistory.objects.create(currency=self.chf, pricing_policy=self.pp, date=d, fx_rate=0.8)
        CurrencyHistory.objects.create(currency=self.cad, pricing_policy=self.pp, date=d, fx_rate=1.1)
        CurrencyHistory.objects.create(currency=self.mex, pricing_policy=self.pp, date=d, fx_rate=0.1)
        CurrencyHistory.objects.create(currency=self.rub, pricing_policy=self.pp, date=d, fx_rate=1. / 100.)
        CurrencyHistory.objects.create(currency=self.gbp, pricing_policy=self.pp, date=d, fx_rate=1.5)

        self.bond0 = Instrument.objects.create(master_user=self.m, name="bond0, USD/USD",
                                               instrument_type=self.m.instrument_type,
                                               pricing_currency=self.usd, price_multiplier=1.0,
                                               accrued_currency=self.usd, accrued_multiplier=1.0)
        self.bond1 = Instrument.objects.create(master_user=self.m, name="bond1, CHF/CHF",
                                               instrument_type=self.m.instrument_type,
                                               pricing_currency=self.chf, price_multiplier=0.01,
                                               accrued_currency=self.chf, accrued_multiplier=0.01)
        self.bond2 = Instrument.objects.create(master_user=self.m, name="bond2, USD/USD",
                                               instrument_type=self.m.instrument_type,
                                               pricing_currency=self.usd, price_multiplier=0.01,
                                               accrued_currency=self.usd, accrued_multiplier=0.01)

        self.stock0 = Instrument.objects.create(master_user=self.m, name="stock1, USD/RUB",
                                                instrument_type=self.m.instrument_type,
                                                pricing_currency=self.usd, price_multiplier=1.0,
                                                accrued_currency=self.usd, accrued_multiplier=1.0)
        self.stock1 = Instrument.objects.create(master_user=self.m, name="stock1, GBP/RUB",
                                                instrument_type=self.m.instrument_type,
                                                pricing_currency=self.gbp, price_multiplier=1.0,
                                                accrued_currency=self.rub, accrued_multiplier=1.0)
        self.stock2 = Instrument.objects.create(master_user=self.m, name="stock2, USD/USD",
                                                instrument_type=self.m.instrument_type,
                                                pricing_currency=self.usd, price_multiplier=1.0,
                                                accrued_currency=self.usd, accrued_multiplier=1.0)

        for days in range(0, 29):
            d = self._d(days)
            PriceHistory.objects.create(instrument=self.bond0, pricing_policy=self.pp, date=d, principal_price=1.0,
                                        accrued_price=1.0)
            PriceHistory.objects.create(instrument=self.bond1, pricing_policy=self.pp, date=d, principal_price=20.,
                                        accrued_price=0.5)
            PriceHistory.objects.create(instrument=self.bond2, pricing_policy=self.pp, date=d, principal_price=20.,
                                        accrued_price=0.5)
            PriceHistory.objects.create(instrument=self.stock1, pricing_policy=self.pp, date=d, principal_price=1.5,
                                        accrued_price=2.0)
            PriceHistory.objects.create(instrument=self.stock2, pricing_policy=self.pp, date=d, principal_price=1.5,
                                        accrued_price=2.0)

        self.at1 = AccountType.objects.create(master_user=self.m, name='at1', show_transaction_details=False)
        self.at2 = AccountType.objects.create(master_user=self.m, name='at2', show_transaction_details=False)
        self.at3 = AccountType.objects.create(master_user=self.m, name='at3', show_transaction_details=True)
        self.a1_1 = Account.objects.create(master_user=self.m, name='a1_1', type=self.at1)
        self.a1_2 = Account.objects.create(master_user=self.m, name='a1_2', type=self.at1)
        self.a2_3 = Account.objects.create(master_user=self.m, name='a2_3', type=self.at2)
        self.a3_4 = Account.objects.create(master_user=self.m, name='a3_4', type=self.at3)

        self.p1 = Portfolio.objects.create(master_user=self.m, name='p1')
        self.p2 = Portfolio.objects.create(master_user=self.m, name='p2')

        for g_i in range(0, 10):
            g = Strategy1Group.objects.create(master_user=self.m, name='%s' % (g_i,))
            setattr(self, 's1_%s' % (g_i,), g)
            for sg_i in range(0, 10):
                sg = Strategy1Subgroup.objects.create(master_user=self.m, group=g, name='%s-%s' % (g_i, sg_i))
                setattr(self, 's1_%s_%s' % (g_i, sg_i), sg)
                for s_i in range(0, 10):
                    s = Strategy1.objects.create(master_user=self.m, subgroup=sg, name='%s-%s-%s' % (g_i, sg_i, s_i))
                    setattr(self, 's1_%s_%s_%s' % (g_i, sg_i, s_i), s)

    def _d(self, days=None):
        if days is None or days == 0:
            return self.report_date
        else:
            return self.report_date + timedelta(days=days)

    def _t(self, master=None, t_class=None, p=None, instr=None, trn_ccy=None, position=None,
           settlement_ccy=None, cash_consideration=None, principal=0.0, carry=0.0, overheads=0.0,
           acc_date=None, acc_date_days=None, cash_date=None, cash_date_days=None,
           acc_pos=None, acc_cash=None, acc_interim=None, fx_rate=0.0,
           s1_pos=None, s1_cash=None, s2_pos=None, s2_cash=None, s3_pos=None, s3_cash=None):
        t = Transaction()

        t.master_user = master if master else self.m
        t.transaction_class = t_class

        t.instrument = instr
        t.transaction_currency = trn_ccy
        t.position_size_with_sign = position

        t.settlement_currency = settlement_ccy or self.m.currency
        t.cash_consideration = cash_consideration if cash_consideration is not None else (principal + carry + overheads)
        t.principal_with_sign = principal
        t.carry_with_sign = carry
        t.overheads_with_sign = overheads

        t.accounting_date = acc_date if acc_date else self._d(acc_date_days)
        t.cash_date = cash_date if cash_date else self._d(cash_date_days)

        t.portfolio = p or self.m.portfolio

        t.account_position = acc_pos or self.m.account
        t.account_cash = acc_cash or self.m.account
        t.account_interim = acc_interim or self.m.account

        t.strategy1_position = s1_pos or self.m.strategy1
        t.strategy1_cash = s1_cash or self.m.strategy1
        t.strategy2_position = s2_pos or self.m.strategy2
        t.strategy2_cash = s2_cash or self.m.strategy2
        t.strategy3_position = s3_pos or self.m.strategy3
        t.strategy3_cash = s3_cash or self.m.strategy3

        t.reference_fx_rate = fx_rate

        t.save()
        return t

    @cached_property
    def _cash_inflow(self):
        return TransactionClass.objects.get(id=TransactionClass.CASH_INFLOW)

    @cached_property
    def _cash_outflow(self):
        return TransactionClass.objects.get(id=TransactionClass.CASH_OUTFLOW)

    @cached_property
    def _buy(self):
        return TransactionClass.objects.get(id=TransactionClass.BUY)

    @cached_property
    def _sell(self):
        return TransactionClass.objects.get(id=TransactionClass.SELL)

    @cached_property
    def _instrument_pl(self):
        return TransactionClass.objects.get(id=TransactionClass.INSTRUMENT_PL)

    @cached_property
    def _transaction_pl(self):
        return TransactionClass.objects.get(id=TransactionClass.TRANSACTION_PL)

    @cached_property
    def _fx_tade(self):
        return TransactionClass.objects.get(id=TransactionClass.FX_TRADE)

    @cached_property
    def _transfer(self):
        return TransactionClass.objects.get(id=TransactionClass.TRANSFER)

    @cached_property
    def _fx_transfer(self):
        return TransactionClass.objects.get(id=TransactionClass.FX_TRANSFER)

    def _print_table(self, data, columns):
        if pandas:
            print(pandas.DataFrame(data=data, columns=columns))
        else:
            print(columns)
            for r in data:
                print(r)

    def _print_transactions(self, builder):
        fields = [
            'pk', 'transaction_class', 'accounting_date', 'cash_date',
            'instrument', 'transaction_currency', 'position_size_with_sign',
            'settlement_currency', 'cash_consideration', 'principal_with_sign', 'carry_with_sign',
            'overheads_with_sign', 'multiplier',
        ]
        columns = [
            'pk', 'class', 'acc_date', 'cash_date',
            'instr', 'transaction_ccy', 'position',
            'settlement_ccy', 'cash_consideration', 'principal', 'carry',
            'overheads', 'multiplier',
        ]
        if builder.instance.detail_by_portfolio:
            fields += [
                'portfolio',
            ]
            columns += [
                'portfolio',
            ]
        if builder.instance.detail_by_account:
            fields += [
                'account_position', 'account_cash', 'account_interim',
            ]
            columns += [
                'acc_pos', 'acc_cash', 'acc_interim',
            ]
        if builder.instance.detail_by_strategy1:
            fields += [
                'strategy1_position', 'strategy1_cash',
            ]
            columns += [
                's1_pos', 's1_cash',
            ]
        if builder.instance.detail_by_strategy2:
            fields += [
                'strategy2_position', 'strategy2_cash',
            ]
            columns += [
                's2_pos', 's2_cash',
            ]
        if builder.instance.detail_by_strategy3:
            fields += [
                'strategy3_position', 'strategy3_cash',
            ]
            columns += [
                's3_pos', 's3_cash',
            ]
        data = []
        for t in builder.transactions:
            row = []
            for f in fields:
                row.append(getattr(t, f, None))
            data.append(row)

        print('-' * 100)
        print('Transactions: ')
        self._print_table(data, columns)

    def _print_items(self, builder, items_attr, name):
        items = getattr(builder.instance, items_attr)
        if not items:
            return
        fields = [
            'type_code', 'user_code', 'instrument', 'currency', 'position_size_with_sign',
            'market_value_system_ccy', 'principal_with_sign_system_ccy', 'carry_with_sign_system_ccy',
            'overheads_with_sign_system_ccy', 'total_with_sign_system_ccy',
        ]
        columns = [
            'type', 'user_code', 'instr', 'ccy', 'position', 'market_value', 'principal', 'carry',
            'overheads', 'total',
        ]
        if builder.instance.detail_by_portfolio:
            fields += [
                'portfolio',
            ]
            columns += [
                'prtfl',
            ]
        if builder.instance.detail_by_account:
            fields += [
                'account',
            ]
            columns += [
                'acc',
            ]
        if builder.instance.detail_by_strategy1:
            fields += [
                'strategy1',
            ]
            columns += [
                's1',
            ]
        if builder.instance.detail_by_strategy2:
            fields += [
                'strategy2',
            ]
            columns += [
                's2',
            ]
        if builder.instance.detail_by_strategy3:
            fields += [
                'strategy3',
            ]
            columns += [
                's3',
            ]
        if builder.instance.show_transaction_details:
            fields += [
                'detail_transaction',
            ]
            columns += [
                'detail_trn',
            ]

        data = []
        for i in items:
            row = []
            for f in fields:
                row.append(getattr(i, f, None))
            data.append(row)

        print('-' * 100)
        print('%s:' % name)
        # print(pd.DataFrame(data=data, columns=columns))
        self._print_table(data=data, columns=columns)

    def _print_summary(self, builder):
        fields = [
            'market_value_system_ccy',
            'principal_with_sign_system_ccy',
            'carry_with_sign_system_ccy',
            'overheads_with_sign_system_ccy',
            'total_with_sign_system_ccy',
        ]
        columns = [
            'market_value',
            'principal',
            'carry',
            'overheads',
            'total',
        ]

        print('-' * 100)
        print('Summary:')
        row = []
        for f in fields:
            row.append(getattr(builder.instance.summary, f, None))
        self._print_table(data=[row], columns=columns)

    def _dump(self, builder, name):
        print('*' * 100)
        print('Report: %s' % name)
        self._print_transactions(builder)
        self._print_items(builder, 'items', 'Items')
        self._print_items(builder, 'invested_items', 'Invested')
        self._print_summary(builder)
        pass

    def _test_balance_0(self):
        self._t(t_class=self._cash_inflow, trn_ccy=self.eur, position=1000, fx_rate=1.3)
        self._t(t_class=self._cash_outflow, trn_ccy=self.usd, position=-1000, acc_date_days=6, cash_date_days=6,
                fx_rate=1 / 75.)

        r = Report(master_user=self.m, pricing_policy=self.pp, report_date=self._d(14))
        b = ReportBuilder(instance=r)
        b.build()
        self._dump(b, 'balance_0')

    def _test_balance_1(self):
        self._t(t_class=self._cash_inflow, trn_ccy=self.usd, position=1000, fx_rate=1.3)
        self._t(t_class=self._buy,
                instr=self.bond0, position=100,
                settlement_ccy=self.usd, principal=-180., carry=-5., overheads=-15.,
                acc_date_days=3, cash_date_days=5)

        r = Report(master_user=self.m, pricing_policy=self.pp, report_date=self._d(14))
        b = ReportBuilder(instance=r)
        b.build()
        self._dump(b, 'balance_1')

    def _test_balance_2(self):
        self._t(t_class=self._cash_inflow, trn_ccy=self.eur, position=1000, fx_rate=1.3)
        self._t(t_class=self._buy,
                instr=self.bond1, position=100,
                settlement_ccy=self.usd, principal=-180., carry=-5., overheads=-15.,
                acc_date_days=3, cash_date_days=5)
        self._t(t_class=self._buy,
                instr=self.stock1, position=-200,
                settlement_ccy=self.rub, principal=1100., carry=0., overheads=-100.,
                acc_date_days=5, cash_date_days=3)
        self._t(t_class=self._cash_outflow,
                trn_ccy=self.rub, position=-1000,
                principal=0., carry=0., overheads=0.,
                acc_date_days=6, cash_date_days=6,
                fx_rate=1 / 75.)

        r = Report(master_user=self.m, pricing_policy=self.pp, report_date=self._d(14))
        b = ReportBuilder(instance=r)
        b.build()
        self._dump(b, 'balance_2')

    def _test_pl_0(self):
        self._t(t_class=self._cash_inflow, trn_ccy=self.usd, position=1000, fx_rate=1.3)

        self._t(t_class=self._buy, instr=self.bond0, position=100,
                settlement_ccy=self.usd, principal=-180., carry=-5., overheads=-15.,
                acc_date_days=3, cash_date_days=5)

        r = Report(master_user=self.m, pricing_policy=self.pp, report_date=self._d(14))
        b = ReportBuilder(instance=r)
        b.build()
        self._dump(b, 'test_pl_0')

    def _test_pl_1(self):
        self._t(t_class=self._cash_inflow, trn_ccy=self.eur, position=1000, fx_rate=1.3)

        self._t(t_class=self._buy, instr=self.bond1, position=100,
                settlement_ccy=self.usd, principal=-180., carry=-5., overheads=-15.,
                acc_date_days=3, cash_date_days=5)

        self._t(t_class=self._buy, instr=self.stock1, position=-200,
                settlement_ccy=self.rub, principal=1100., carry=0., overheads=-100.,
                acc_date_days=5, cash_date_days=3)

        self._t(t_class=self._cash_outflow, trn_ccy=self.rub, position=-1000,
                principal=0., carry=0., overheads=0.,
                acc_date_days=6, cash_date_days=6, fx_rate=1 / 75.)

        self._t(t_class=self._instrument_pl, instr=self.stock1, position=0.,
                settlement_ccy=self.chf, principal=0., carry=11., overheads=-1.,
                acc_date_days=7, cash_date_days=7)

        self._t(t_class=self._instrument_pl, instr=self.bond1, position=0.,
                settlement_ccy=self.chf, principal=0., carry=20., overheads=0.,
                acc_date_days=8, cash_date_days=8)

        self._t(t_class=self._transaction_pl, position=0.,
                settlement_ccy=self.rub, principal=0., carry=-900., overheads=-100.,
                acc_date_days=8, cash_date_days=8)

        r = Report(master_user=self.m, pricing_policy=self.pp, report_date=self._d(14))
        b = ReportBuilder(instance=r)
        b.build()
        self._dump(b, 'test_pl_1')

    def _test_pl_real_unreal_0(self):
        # TODO: bad
        s1 = self.s1_1_1_1
        s2 = self.s1_1_1_2
        s3 = self.s1_1_1_3
        s4 = self.s1_1_1_4

        instr = Instrument.objects.create(master_user=self.m, name="I1, USD/USD",
                                          instrument_type=self.m.instrument_type,
                                          pricing_currency=self.usd, price_multiplier=1.0,
                                          accrued_currency=self.usd, accrued_multiplier=1.0)

        PriceHistory.objects.create(instrument=instr, pricing_policy=self.pp,
                                    date=self._d(1), principal_price=10.0, accrued_price=1.0)
        PriceHistory.objects.create(instrument=instr, pricing_policy=self.pp,
                                    date=self._d(2), principal_price=10.5, accrued_price=1.0)
        PriceHistory.objects.create(instrument=instr, pricing_policy=self.pp,
                                    date=self._d(3), principal_price=11.0, accrued_price=1.0)
        PriceHistory.objects.create(instrument=instr, pricing_policy=self.pp,
                                    date=self._d(4), principal_price=11.5, accrued_price=1.0)
        PriceHistory.objects.create(instrument=instr, pricing_policy=self.pp,
                                    date=self._d(5), principal_price=12.0, accrued_price=1.0)
        PriceHistory.objects.create(instrument=instr, pricing_policy=self.pp,
                                    date=self._d(6), principal_price=12.5, accrued_price=1.0)

        self._t(t_class=self._buy, instr=instr, position=10,
                settlement_ccy=self.usd, principal=-100., carry=0.0, overheads=0.0,
                acc_date_days=1, cash_date_days=1, s1_pos=s1)

        self._t(t_class=self._buy, instr=instr, position=10,
                settlement_ccy=self.usd, principal=-105., carry=0.0, overheads=0.0,
                acc_date_days=2, cash_date_days=2, s1_pos=s1)

        self._t(t_class=self._buy, instr=instr, position=10,
                settlement_ccy=self.usd, principal=-110., carry=0.0, overheads=0.0,
                acc_date_days=3, cash_date_days=3, s1_pos=s1)

        self._t(t_class=self._sell, instr=instr, position=-20,
                settlement_ccy=self.usd, principal=230., carry=0.0, overheads=0.0,
                acc_date_days=4, cash_date_days=4, s1_pos=s2)

        self._t(t_class=self._buy, instr=instr, position=10,
                settlement_ccy=self.usd, principal=-120., carry=0.0, overheads=0.0,
                acc_date_days=5, cash_date_days=5, s1_pos=s3)

        self._t(t_class=self._sell, instr=instr, position=-20,
                settlement_ccy=self.usd, principal=250., carry=0.0, overheads=0.0,
                acc_date_days=6, cash_date_days=6, s1_pos=s2)

        r = Report(master_user=self.m, pricing_policy=self.pp, report_date=self._d(14),
                   detail_by_strategy1=True)
        b = ReportBuilder(instance=r)
        b.build()
        self._dump(b, 'test_pl_real_unreal_0')

    def test_pl_real_unreal_1(self):
        s1 = self.s1_1_1_1
        s2 = self.s1_1_1_2
        s3 = self.s1_1_1_3
        s4 = self.s1_1_1_4

        instr = Instrument.objects.create(master_user=self.m, name="I1, USD/USD",
                                          instrument_type=self.m.instrument_type,
                                          pricing_currency=self.usd, price_multiplier=1.0,
                                          accrued_currency=self.usd, accrued_multiplier=1.0)

        PriceHistory.objects.create(instrument=instr, pricing_policy=self.pp,
                                    date=self._d(1), principal_price=8.0, accrued_price=1.0)
        PriceHistory.objects.create(instrument=instr, pricing_policy=self.pp,
                                    date=self._d(2), principal_price=10.0, accrued_price=1.0)
        PriceHistory.objects.create(instrument=instr, pricing_policy=self.pp,
                                    date=self._d(3), principal_price=10.5, accrued_price=1.0)
        PriceHistory.objects.create(instrument=instr, pricing_policy=self.pp,
                                    date=self._d(4), principal_price=11.0, accrued_price=1.0)
        PriceHistory.objects.create(instrument=instr, pricing_policy=self.pp,
                                    date=self._d(5), principal_price=11.5, accrued_price=1.0)
        PriceHistory.objects.create(instrument=instr, pricing_policy=self.pp,
                                    date=self._d(6), principal_price=12.0, accrued_price=1.0)
        PriceHistory.objects.create(instrument=instr, pricing_policy=self.pp,
                                    date=self._d(7), principal_price=12.5, accrued_price=1.0)
        PriceHistory.objects.create(instrument=instr, pricing_policy=self.pp,
                                    date=self._d(8), principal_price=13.0, accrued_price=1.0)

        self._t(t_class=self._sell, instr=instr, position=-5,
                settlement_ccy=self.usd, principal=40.0, carry=0.0, overheads=0.0,
                acc_date_days=1, cash_date_days=1, s1_pos=s1)

        self._t(t_class=self._buy, instr=instr, position=10,
                settlement_ccy=self.usd, principal=-100.0, carry=0.0, overheads=0.0,
                acc_date_days=2, cash_date_days=2, s1_pos=s1)

        self._t(t_class=self._buy, instr=instr, position=10,
                settlement_ccy=self.usd, principal=-105.0, carry=0.0, overheads=0.0,
                acc_date_days=3, cash_date_days=3, s1_pos=s1)

        self._t(t_class=self._buy, instr=instr, position=10,
                settlement_ccy=self.usd, principal=-110.0, carry=0.0, overheads=0.0,
                acc_date_days=4, cash_date_days=4, s1_pos=s1)

        self._t(t_class=self._sell, instr=instr, position=-20,
                settlement_ccy=self.usd, principal=230.0, carry=0.0, overheads=0.0,
                acc_date_days=5, cash_date_days=5, s1_pos=s2)

        self._t(t_class=self._buy, instr=instr, position=10,
                settlement_ccy=self.usd, principal=-120.0, carry=0.0, overheads=0.0,
                acc_date_days=6, cash_date_days=6, s1_pos=s3)

        self._t(t_class=self._sell, instr=instr, position=-20,
                settlement_ccy=self.usd, principal=250.0, carry=0.0, overheads=0.0,
                acc_date_days=7, cash_date_days=7, s1_pos=s2)

        self._t(t_class=self._sell, instr=instr, position=-10,
                settlement_ccy=self.usd, principal=130.0, carry=0.0, overheads=0.0,
                acc_date_days=8, cash_date_days=8, s1_pos=s4)

        r = Report(master_user=self.m, pricing_policy=self.pp, report_date=self._d(14),
                   detail_by_strategy1=True)
        b = ReportBuilder(instance=r)
        b.build()
        self._dump(b, 'test_pl_real_unreal_1')
