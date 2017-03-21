import logging
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils.functional import cached_property

from poms.accounts.models import AccountType, Account
from poms.currencies.models import Currency, CurrencyHistory
from poms.instruments.models import Instrument, PriceHistory, PricingPolicy, CostMethod, InstrumentType, \
    InstrumentClass, \
    AccrualCalculationSchedule, AccrualCalculationModel, Periodicity
from poms.portfolios.models import Portfolio
from poms.reports.builders import Report, ReportBuilder, VirtualTransaction, ReportItem
from poms.strategies.models import Strategy1Group, Strategy1Subgroup, Strategy1
from poms.transactions.models import Transaction, TransactionClass
from poms.users.models import MasterUser, Member

_l = logging.getLogger('poms.reports')


class ReportTestCase(TestCase):
    def setUp(self):
        _l.debug('')
        _l.debug('')
        # _l.debug('*' * 100)

        # if pandas:
        #     pandas.set_option('display.width', 10000)
        #     pandas.set_option('display.max_rows', 100)
        #     pandas.set_option('display.max_columns', 1000)
        #     pandas.set_option('precision', 4)
        #     pandas.set_option('display.float_format', '{:.4f}'.format)

        self.report_date = date(2016, 3, 1)

        user = User.objects.create_user('a1')
        self.m = MasterUser.objects.create_master_user(user=user, name='a1_m1')
        self.member = Member.objects.create(master_user=self.m, user=user, is_owner=True, is_admin=True)

        self.pp = PricingPolicy.objects.create(master_user=self.m)

        self.usd = self.m.system_currency
        # self.eur, _ = Currency.objects.get_or_create(user_code='EUR', master_user=self.m, defaults={'name': 'EUR'})
        # self.chf, _ = Currency.objects.get_or_create(user_code='CHF', master_user=self.m, defaults={'name': 'CHF'})
        # self.cad, _ = Currency.objects.get_or_create(user_code='CAD', master_user=self.m, defaults={'name': 'CAD'})
        # self.mex, _ = Currency.objects.get_or_create(user_code='MEX', master_user=self.m, defaults={'name': 'MEX'})
        # self.rub, _ = Currency.objects.get_or_create(user_code='RUB', master_user=self.m, defaults={'name': 'RUB'})
        # self.gbp, _ = Currency.objects.get_or_create(user_code='GBP', master_user=self.m, defaults={'name': 'GBP'})
        self.eur = self._ccy('EUR')
        self.chf = self._ccy('CHF')
        self.cad = self._ccy('CAD')
        self.mex = self._ccy('MEX')
        self.rub = self._ccy('RUB')
        self.gbp = self._ccy('GBP')

        CurrencyHistory.objects.all().delete()
        for days in range(0, 29):
            d = self._d(days)
            # CurrencyHistory.objects.create(currency=self.eur, pricing_policy=self.pp, date=d, fx_rate=1.3)
            # CurrencyHistory.objects.create(currency=self.chf, pricing_policy=self.pp, date=d, fx_rate=0.9)
            # CurrencyHistory.objects.create(currency=self.cad, pricing_policy=self.pp, date=d, fx_rate=1.2)
            # CurrencyHistory.objects.create(currency=self.mex, pricing_policy=self.pp, date=d, fx_rate=0.15)
            # CurrencyHistory.objects.create(currency=self.rub, pricing_policy=self.pp, date=d, fx_rate=1.0 / 75.0)
            # CurrencyHistory.objects.create(currency=self.gbp, pricing_policy=self.pp, date=d, fx_rate=1.6)
            self._ccy_hist(self.eur, d, 1.3)
            self._ccy_hist(self.chf, d, 0.9)
            self._ccy_hist(self.cad, d, 1.2)
            self._ccy_hist(self.mex, d, 0.15)
            self._ccy_hist(self.rub, d, 1.0 / 75.0)
            self._ccy_hist(self.gbp, d, 1.6)

        d = self._d(30)
        # CurrencyHistory.objects.create(currency=self.eur, pricing_policy=self.pp, date=d, fx_rate=1.2)
        # CurrencyHistory.objects.create(currency=self.chf, pricing_policy=self.pp, date=d, fx_rate=0.8)
        # CurrencyHistory.objects.create(currency=self.cad, pricing_policy=self.pp, date=d, fx_rate=1.1)
        # CurrencyHistory.objects.create(currency=self.mex, pricing_policy=self.pp, date=d, fx_rate=0.1)
        # CurrencyHistory.objects.create(currency=self.rub, pricing_policy=self.pp, date=d, fx_rate=1.0 / 100.0)
        # CurrencyHistory.objects.create(currency=self.gbp, pricing_policy=self.pp, date=d, fx_rate=1.5)
        self._ccy_hist(self.eur, d, 1.2)
        self._ccy_hist(self.chf, d, 0.8)
        self._ccy_hist(self.cad, d, 1.1)
        self._ccy_hist(self.mex, d, 0.1)
        self._ccy_hist(self.rub, d, 1.0 / 100.0)
        self._ccy_hist(self.gbp, d, 1.5)

        # self.bond0 = Instrument.objects.create(master_user=self.m, name="bond0, USD/USD",
        #                                        instrument_type=self.m.instrument_type,
        #                                        pricing_currency=self.usd, price_multiplier=1.0,
        #                                        accrued_currency=self.usd, accrued_multiplier=1.0)
        # self.bond1 = Instrument.objects.create(master_user=self.m, name="bond1, CHF/CHF",
        #                                        instrument_type=self.m.instrument_type,
        #                                        pricing_currency=self.chf, price_multiplier=0.01,
        #                                        accrued_currency=self.chf, accrued_multiplier=0.01)
        # self.bond2 = Instrument.objects.create(master_user=self.m, name="bond2, USD/USD",
        #                                        instrument_type=self.m.instrument_type,
        #                                        pricing_currency=self.usd, price_multiplier=0.01,
        #                                        accrued_currency=self.usd, accrued_multiplier=0.01)
        # self.bond3 = Instrument.objects.create(master_user=self.m, name="bond3, USD/USD",
        #                                        instrument_type=self.m.instrument_type,
        #                                        pricing_currency=self.usd, price_multiplier=0.01,
        #                                        accrued_currency=self.usd, accrued_multiplier=0.01)
        #
        # self.stock0 = Instrument.objects.create(master_user=self.m, name="stock1, USD/RUB",
        #                                         instrument_type=self.m.instrument_type,
        #                                         pricing_currency=self.usd, price_multiplier=1.0,
        #                                         accrued_currency=self.usd, accrued_multiplier=1.0)
        # self.stock1 = Instrument.objects.create(master_user=self.m, name="stock1, GBP/RUB",
        #                                         instrument_type=self.m.instrument_type,
        #                                         pricing_currency=self.gbp, price_multiplier=1.0,
        #                                         accrued_currency=self.rub, accrued_multiplier=1.0)
        # self.stock2 = Instrument.objects.create(master_user=self.m, name="stock2, USD/USD",
        #                                         instrument_type=self.m.instrument_type,
        #                                         pricing_currency=self.usd, price_multiplier=1.0,
        #                                         accrued_currency=self.usd, accrued_multiplier=1.0)
        self.bond0 = self._instr('bond0', pricing_ccy=self.usd, price_mult=1.0, accrued_ccy=self.usd, accrued_mult=1.0)
        self.bond1 = self._instr('bond1', pricing_ccy=self.chf, price_mult=0.01, accrued_ccy=self.chf, accrued_mult=0.01)
        self.bond2 = self._instr('bond2', pricing_ccy=self.usd, price_mult=0.01, accrued_ccy=self.usd, accrued_mult=0.01)
        self.bond3 = self._instr('bond3', pricing_ccy=self.usd, price_mult=0.01, accrued_ccy=self.usd, accrued_mult=0.01)
        self.stock0 = self._instr('stock0', pricing_ccy=self.usd, price_mult=1.0, accrued_ccy=self.usd, accrued_mult=1.0)
        self.stock1 = self._instr('stock1', pricing_ccy=self.gbp, price_mult=1.0, accrued_ccy=self.rub, accrued_mult=1.0)
        self.stock2 = self._instr('stock2', pricing_ccy=self.usd, price_mult=1.0, accrued_ccy=self.usd, accrued_mult=1.0)

        PriceHistory.objects.all().delete()
        for days in range(0, 29):
            d = self._d(days)
            # PriceHistory.objects.create(instrument=self.bond0, pricing_policy=self.pp, date=d, principal_price=1.0, accrued_price=1.0)
            # PriceHistory.objects.create(instrument=self.bond1, pricing_policy=self.pp, date=d, principal_price=20., accrued_price=0.5)
            # PriceHistory.objects.create(instrument=self.bond2, pricing_policy=self.pp, date=d, principal_price=20., accrued_price=0.5)
            # PriceHistory.objects.create(instrument=self.stock1, pricing_policy=self.pp, date=d, principal_price=1.5, accrued_price=2.0)
            # PriceHistory.objects.create(instrument=self.stock2, pricing_policy=self.pp, date=d, principal_price=1.5, accrued_price=2.0)
            self._instr_hist(self.bond0, d, 1.0, 1.0)
            self._instr_hist(self.bond1, d, 20.0, 0.5)
            self._instr_hist(self.bond2, d, 20.0, 0.5)
            self._instr_hist(self.stock1, d, 1.5, 2.0)
            self._instr_hist(self.stock2, d, 1.5, 2.0)

        self.at1 = AccountType.objects.create(master_user=self.m, name='at1', show_transaction_details=False)
        self.at2 = AccountType.objects.create(master_user=self.m, name='at2', show_transaction_details=False)
        self.at3 = AccountType.objects.create(master_user=self.m, name='at3', show_transaction_details=True)
        self.a1_1 = Account.objects.create(master_user=self.m, name='a1_1', type=self.at1)
        self.a1_2 = Account.objects.create(master_user=self.m, name='a1_2', type=self.at1)
        self.a2_3 = Account.objects.create(master_user=self.m, name='a2_3', type=self.at2)
        self.a3_4 = Account.objects.create(master_user=self.m, name='a3_4', type=self.at3)

        self.p1 = Portfolio.objects.create(master_user=self.m, name='p1')
        self.p2 = Portfolio.objects.create(master_user=self.m, name='p2')
        self.p3 = Portfolio.objects.create(master_user=self.m, name='p3')
        self.p4 = Portfolio.objects.create(master_user=self.m, name='p4')

        self.s1_1 = Strategy1Group.objects.create(master_user=self.m, name='1')
        self.s1_1_1 = Strategy1Subgroup.objects.create(master_user=self.m, group=self.s1_1, name='1-1')
        self.s1_1_1_1 = Strategy1.objects.create(master_user=self.m, subgroup=self.s1_1_1, name='1-1-1')
        self.s1_1_1_2 = Strategy1.objects.create(master_user=self.m, subgroup=self.s1_1_1, name='1-1-2')
        self.s1_1_1_3 = Strategy1.objects.create(master_user=self.m, subgroup=self.s1_1_1, name='1-1-3')
        self.s1_1_1_4 = Strategy1.objects.create(master_user=self.m, subgroup=self.s1_1_1, name='1-1-4')
        self.s1_1_2 = Strategy1Subgroup.objects.create(master_user=self.m, group=self.s1_1, name='1-2')
        self.s1_1_2_1 = Strategy1.objects.create(master_user=self.m, subgroup=self.s1_1_2, name='1-2-1')
        self.s1_1_2_2 = Strategy1.objects.create(master_user=self.m, subgroup=self.s1_1_2, name='1-2-2')
        self.s1_1_2_3 = Strategy1.objects.create(master_user=self.m, subgroup=self.s1_1_2, name='1-2-3')
        self.s1_1_2_4 = Strategy1.objects.create(master_user=self.m, subgroup=self.s1_1_2, name='1-2-4')
        self.s1_2 = Strategy1Group.objects.create(master_user=self.m, name='2')
        self.s1_2_1 = Strategy1Subgroup.objects.create(master_user=self.m, group=self.s1_2, name='2-1')
        self.s1_2_1_1 = Strategy1.objects.create(master_user=self.m, subgroup=self.s1_2_1, name='2-1-1')
        self.s1_2_1_2 = Strategy1.objects.create(master_user=self.m, subgroup=self.s1_2_1, name='2-1-2')
        self.s1_2_1_3 = Strategy1.objects.create(master_user=self.m, subgroup=self.s1_2_1, name='2-1-3')
        self.s1_2_1_4 = Strategy1.objects.create(master_user=self.m, subgroup=self.s1_2_1, name='2-1-4')
        self.s1_2_2 = Strategy1Subgroup.objects.create(master_user=self.m, group=self.s1_2, name='2-2')
        self.s1_2_2_1 = Strategy1.objects.create(master_user=self.m, subgroup=self.s1_2_2, name='2-2-1')
        self.s1_2_2_2 = Strategy1.objects.create(master_user=self.m, subgroup=self.s1_2_2, name='2-2-2')
        self.s1_2_2_3 = Strategy1.objects.create(master_user=self.m, subgroup=self.s1_2_2, name='2-2-3')
        self.s1_2_2_4 = Strategy1.objects.create(master_user=self.m, subgroup=self.s1_2_2, name='2-2-4')

        # for g_i in range(0, 10):
        #     g = Strategy1Group.objects.create(master_user=self.m, name='%s' % (g_i,))
        #     setattr(self, 's1_%s' % (g_i,), g)
        #     for sg_i in range(0, 10):
        #         sg = Strategy1Subgroup.objects.create(master_user=self.m, group=g, name='%s-%s' % (g_i, sg_i))
        #         setattr(self, 's1_%s_%s' % (g_i, sg_i), sg)
        #         for s_i in range(0, 10):
        #             s = Strategy1.objects.create(master_user=self.m, subgroup=sg, name='%s-%s-%s' % (g_i, sg_i, s_i))
        #             setattr(self, 's1_%s_%s_%s' % (g_i, sg_i, s_i), s)

        # from django.conf import settings
        # settings.DEBUG = True
        pass

    def _d(self, days=None):
        if days is None or days == 0:
            return self.report_date
        else:
            return self.report_date + timedelta(days=days)

    def _t(self, master=None, t_class=None, p=None, instr=None, trn_ccy=None, position=0.0,
           stl_ccy=None, cash=None, principal=0.0, carry=0.0, overheads=0.0,
           acc_date=None, acc_date_days=-1, cash_date=None, cash_date_days=-1,
           acc_pos=None, acc_cash=None, acc_interim=None, fx_rate=0.0,
           s1_pos=None, s1_cash=None, s2_pos=None, s2_cash=None, s3_pos=None, s3_cash=None,
           link_instr=None, alloc_bl=None, alloc_pl=None,
           save=True):
        t = Transaction()

        t.master_user = master if master else self.m
        t.transaction_class = t_class

        t.instrument = instr
        t.transaction_currency = trn_ccy
        t.position_size_with_sign = position

        t.settlement_currency = stl_ccy or self.m.currency
        t.cash_consideration = cash if cash is not None else (principal + carry + overheads)
        t.principal_with_sign = principal
        t.carry_with_sign = carry
        t.overheads_with_sign = overheads

        t.accounting_date = acc_date if acc_date else self._d(acc_date_days)
        t.cash_date = cash_date if cash_date else self._d(cash_date_days)
        t.transaction_date = min(t.accounting_date, t.cash_date)

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

        t.linked_instrument = link_instr or self.m.instrument
        t.allocation_balance = alloc_bl or self.m.instrument
        t.allocation_pl = alloc_pl or self.m.instrument
        if save:
            t.save()
        return t

    def _ccy(self, code, attr=None):
        val, created = Currency.objects.get_or_create(user_code=code, master_user=self.m, defaults={'name': code})
        if attr:
            setattr(self, attr, val)
        return val

    def _instr(self, code, instr_type=None, pricing_ccy=None, price_mult=1.0, accrued_ccy=None, accrued_mult=1.0,
               code_fmt='%(code)s %(pricing_ccy)s/%(accrued_ccy)s'):
        instr_type = instr_type or self.m.instrument_type
        pricing_ccy = pricing_ccy or self.usd
        accrued_ccy = accrued_ccy or self.usd
        return Instrument.objects.create(
            master_user=self.m,
            name=code_fmt % {
                'code': code,
                'pricing_ccy': pricing_ccy.user_code,
                'accrued_ccy': accrued_ccy.user_code,
            },
            instrument_type=instr_type,
            pricing_currency=pricing_ccy,
            price_multiplier=price_mult,
            accrued_currency=accrued_ccy,
            accrued_multiplier=accrued_mult
        )

    def _instr_hist(self, instr, d, principal_price, accrued_price):
        return PriceHistory.objects.create(instrument=instr, pricing_policy=self.pp, date=d,
                                           principal_price=principal_price, accrued_price=accrued_price)

    def _ccy_hist(self, ccy, d, fx):
        return CurrencyHistory.objects.create(currency=ccy, pricing_policy=self.pp, date=d, fx_rate=fx)

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

    @cached_property
    def _avco(self):
        return CostMethod.objects.get(pk=CostMethod.AVCO)

    @cached_property
    def _fifo(self):
        return CostMethod.objects.get(pk=CostMethod.FIFO)

    def _print_transactions(self, transactions, columns=None):
        _l.debug('')
        _l.debug('Transactions: ')
        VirtualTransaction.dumps(transactions, columns=columns)

    def _print_items(self, name, builder, items, columns=None):
        _l.debug('')
        _l.debug('%s:', name)
        ReportItem.dumps(items, columns=columns)

    def _dump(self, builder, name, show_trns=True, show_items=True, trn_columns=None, item_columns=None):
        if show_trns or show_items:
            _l.debug('-' * 100)
            _l.debug('Report: %s', name)
            _l.debug('-' * 100)

            if show_trns:
                self._print_transactions(builder.instance.transactions, columns=trn_columns)

            if show_items:
                self._print_items('Items', builder, builder.instance.items, columns=item_columns)

    def _test_avco_prtfl_0(self):
        self._t(t_class=self._buy, instr=self.bond0, position=5,
                stl_ccy=self.usd, principal=-10.0,
                acc_date_days=1, cash_date_days=1,
                p=self.p1,
                acc_pos=self.a1_1, acc_cash=self.a1_1,
                s1_pos=self.s1_1_1_1, s1_cash=self.s1_1_1_1)

        self._t(t_class=self._buy, instr=self.bond0, position=5,
                stl_ccy=self.usd, principal=-15.0,
                acc_date_days=2, cash_date_days=2,
                p=self.p1,
                acc_pos=self.a1_1, acc_cash=self.a1_1,
                s1_pos=self.s1_1_1_1, s1_cash=self.s1_1_1_1)

        self._t(t_class=self._sell, instr=self.bond0, position=-5,
                stl_ccy=self.usd, principal=20.0,
                acc_date_days=3, cash_date_days=3,
                p=self.p2,
                acc_pos=self.a1_1, acc_cash=self.a1_1,
                s1_pos=self.s1_1_1_1, s1_cash=self.s1_1_1_1)

        r = Report(master_user=self.m, pricing_policy=self.pp, report_date=self._d(14),
                   cost_method=self._avco,
                   portfolio_mode=Report.MODE_IGNORE)
        b = ReportBuilder(instance=r)
        b.build()
        self._dump(b, 'test_avco_prtfl_0: IGNORE')

        r = Report(master_user=self.m, pricing_policy=self.pp, report_date=self._d(14),
                   cost_method=self._avco,
                   portfolio_mode=Report.MODE_INDEPENDENT)
        b = ReportBuilder(instance=r)
        b.build()
        self._dump(b, 'test_avco_prtfl_0: INDEPENDENT')

    def _test_avco_acc_0(self):
        self._t(t_class=self._buy, instr=self.bond0, position=5,
                stl_ccy=self.usd, principal=-10.0,
                acc_date_days=1, cash_date_days=1,
                p=self.p1,
                acc_pos=self.a1_1, acc_cash=self.a1_1,
                s1_pos=self.s1_1_1_1, s1_cash=self.s1_1_1_1)

        self._t(t_class=self._buy, instr=self.bond0, position=5,
                stl_ccy=self.usd, principal=-15.0,
                acc_date_days=2, cash_date_days=2,
                p=self.p1,
                acc_pos=self.a1_1, acc_cash=self.a1_1,
                s1_pos=self.s1_1_1_1, s1_cash=self.s1_1_1_1)

        self._t(t_class=self._sell, instr=self.bond0, position=-5,
                stl_ccy=self.usd, principal=20.0,
                acc_date_days=3, cash_date_days=3,
                p=self.p1,
                acc_pos=self.a1_2, acc_cash=self.a1_2,
                s1_pos=self.s1_1_1_1, s1_cash=self.s1_1_1_1)

        r = Report(master_user=self.m, pricing_policy=self.pp, report_date=self._d(14),
                   cost_method=self._avco,
                   account_mode=Report.MODE_IGNORE)
        b = ReportBuilder(instance=r)
        b.build()
        self._dump(b, 'test_avco_acc_0: IGNORE')

        r = Report(master_user=self.m, pricing_policy=self.pp, report_date=self._d(14),
                   cost_method=self._avco,
                   account_mode=Report.MODE_INDEPENDENT)
        b = ReportBuilder(instance=r)
        b.build()
        self._dump(b, 'test_avco_acc_0: INDEPENDENT')

    def _test_avco_str1_0(self):
        self._t(t_class=self._buy, instr=self.bond0, position=5,
                stl_ccy=self.usd, principal=-10.0,
                acc_date_days=1, cash_date_days=1,
                p=self.p1,
                acc_pos=self.a1_1, acc_cash=self.a1_1,
                s1_pos=self.s1_1_1_1, s1_cash=self.s1_1_1_1)

        self._t(t_class=self._buy, instr=self.bond0, position=5,
                stl_ccy=self.usd, principal=-15.0,
                acc_date_days=2, cash_date_days=2,
                p=self.p1,
                acc_pos=self.a1_1, acc_cash=self.a1_1,
                s1_pos=self.s1_1_1_1, s1_cash=self.s1_1_1_1)

        self._t(t_class=self._sell, instr=self.bond0, position=-5,
                stl_ccy=self.usd, principal=20.0,
                acc_date_days=3, cash_date_days=3,
                p=self.p1,
                acc_pos=self.a1_1, acc_cash=self.a1_1,
                s1_pos=self.s1_1_1_2, s1_cash=self.s1_1_1_2)

        r = Report(master_user=self.m, pricing_policy=self.pp, report_date=self._d(14),
                   cost_method=self._avco,
                   strategy1_mode=Report.MODE_INDEPENDENT)
        b = ReportBuilder(instance=r)
        b.build()
        self._dump(b, 'test_avco_str1_0: NON_OFFSETTING')

        r = Report(master_user=self.m, pricing_policy=self.pp, report_date=self._d(14),
                   cost_method=self._avco,
                   strategy1_mode=Report.MODE_INTERDEPENDENT)
        b = ReportBuilder(instance=r)
        b.build()
        self._dump(b, 'test_avco_str1_0: OFFSETTING')

    def _test_balance_0(self):
        self._t(t_class=self._cash_inflow, trn_ccy=self.eur, position=1000, fx_rate=1.3)
        self._t(t_class=self._cash_outflow, trn_ccy=self.usd, position=-1000, acc_date_days=1, cash_date_days=1,
                fx_rate=1.0)

        r = Report(master_user=self.m, pricing_policy=self.pp, report_date=self._d(14))
        b = ReportBuilder(instance=r)
        b.build()
        self._dump(b, 'test_balance_0')

    def test_balance_1(self):
        self._t(t_class=self._cash_inflow, stl_ccy=self.usd, trn_ccy=self.usd, position=1000, fx_rate=1.0)
        self._t(t_class=self._buy,
                instr=self.bond0, position=100,
                stl_ccy=self.usd, principal=-180., carry=-5., overheads=-15.,
                acc_date_days=3, cash_date_days=5)

        r = Report(master_user=self.m, pricing_policy=self.pp, report_date=self._d(14))
        b = ReportBuilder(instance=r)
        b.build()
        self._dump(b, 'test_balance_1')

    def _test_build_position_only(self):
        self._t(t_class=self._cash_inflow, stl_ccy=self.usd, trn_ccy=self.usd, position=1000, fx_rate=1.0)

        self._t(t_class=self._buy,
                instr=self.bond0, position=100,
                stl_ccy=self.usd, principal=-180., carry=-5., overheads=-15.,
                acc_date_days=1, cash_date_days=1)

        self._t(t_class=self._buy,
                instr=self.bond1, position=100,
                stl_ccy=self.usd, principal=-180., carry=-5., overheads=-15.,
                acc_date_days=2, cash_date_days=2)

        self._t(t_class=self._sell,
                instr=self.bond1, position=-100,
                trn_ccy=self.rub,
                stl_ccy=self.chf, principal=180., carry=5., overheads=-15.,
                acc_date_days=3, cash_date_days=3)

        r = Report(master_user=self.m, pricing_policy=self.pp, report_date=self._d(14))
        b = ReportBuilder(instance=r)
        b.build_position_only()
        self._dump(b, 'test_build_position_only',
                   item_columns=['type_code', 'instr', 'ccy', 'prtfl', 'acc', 'str1', 'str2', 'str3', 'alloc_bl',
                                 'alloc_pl', 'pos_size', ])

    def _test_balance_2(self):
        self._t(t_class=self._cash_inflow, trn_ccy=self.eur, position=1000, fx_rate=1.3)
        self._t(t_class=self._buy,
                instr=self.bond1, position=100,
                stl_ccy=self.usd, principal=-180., carry=-5., overheads=-15.,
                acc_date_days=3, cash_date_days=5)
        self._t(t_class=self._buy,
                instr=self.stock1, position=-200,
                stl_ccy=self.rub, principal=1100., carry=0., overheads=-100.,
                acc_date_days=5, cash_date_days=3)
        self._t(t_class=self._cash_outflow,
                trn_ccy=self.rub, position=-1000,
                principal=0., carry=0., overheads=0.,
                acc_date_days=6, cash_date_days=6,
                fx_rate=1 / 75.)

        r = Report(master_user=self.m, pricing_policy=self.pp, report_date=self._d(14))
        b = ReportBuilder(instance=r)
        b.build()
        self._dump(b, 'test_balance_2')

    def _test_balance_3(self):
        # self._t(t_class=self._cash_inflow, trn_ccy=self.usd, position=1000, fx_rate=1.3)
        self._t(t_class=self._buy,
                instr=self.bond0, position=5,
                stl_ccy=self.usd, principal=-10., carry=-0., overheads=-0.,
                acc_date_days=1, cash_date_days=1)
        self._t(t_class=self._buy,
                instr=self.bond0, position=5,
                stl_ccy=self.usd, principal=-15., carry=-0., overheads=-0.,
                acc_date_days=2, cash_date_days=2)
        self._t(t_class=self._sell,
                instr=self.bond0, position=-5,
                stl_ccy=self.usd, principal=20., carry=0., overheads=0.,
                acc_date_days=3, cash_date_days=3)

        r = Report(master_user=self.m, pricing_policy=self.pp, report_date=self._d(14))
        b = ReportBuilder(instance=r)
        b.build()
        self._dump(b, 'test_balance_3')

    def _test_pl_0(self):
        self._t(t_class=self._cash_inflow, trn_ccy=self.usd, position=1000, fx_rate=1.3)

        self._t(t_class=self._buy, instr=self.bond0, position=100,
                stl_ccy=self.usd, principal=-180., carry=-5., overheads=-15.,
                acc_date_days=3, cash_date_days=5)

        r = Report(master_user=self.m, pricing_policy=self.pp, report_date=self._d(14))
        b = ReportBuilder(instance=r)
        b.build()
        self._dump(b, 'test_pl_0')

    def _test_pl_1(self):
        self._t(t_class=self._cash_inflow, trn_ccy=self.eur, position=1000, fx_rate=1.3)

        self._t(t_class=self._buy, instr=self.bond1, position=100,
                stl_ccy=self.usd, principal=-180., carry=-5., overheads=-15.,
                acc_date_days=3, cash_date_days=5)

        self._t(t_class=self._buy, instr=self.stock1, position=-200,
                stl_ccy=self.rub, principal=1100., carry=0., overheads=-100.,
                acc_date_days=5, cash_date_days=3)

        self._t(t_class=self._cash_outflow, trn_ccy=self.rub, position=-1000,
                principal=0., carry=0., overheads=0.,
                acc_date_days=6, cash_date_days=6, fx_rate=1 / 75.)

        self._t(t_class=self._instrument_pl, instr=self.stock1, position=0.,
                stl_ccy=self.chf, principal=0., carry=11., overheads=-1.,
                acc_date_days=7, cash_date_days=7)

        self._t(t_class=self._instrument_pl, instr=self.bond1, position=0.,
                stl_ccy=self.chf, principal=0., carry=20., overheads=0.,
                acc_date_days=8, cash_date_days=8)

        self._t(t_class=self._transaction_pl, position=0.,
                stl_ccy=self.rub, principal=0., carry=-900., overheads=-100.,
                acc_date_days=8, cash_date_days=8)

        r = Report(master_user=self.m, pricing_policy=self.pp, report_date=self._d(14))
        b = ReportBuilder(instance=r)
        b.build()
        self._dump(b, 'test_pl_1')

    # def _test_pl_real_unreal_1(self):
    #     s1 = self.s1_1_1_1
    #     s2 = self.s1_1_1_2
    #     s3 = self.s1_1_1_3
    #     s4 = self.s1_1_1_4
    #
    #     instr = Instrument.objects.create(master_user=self.m, name="I1, USD/USD",
    #                                       instrument_type=self.m.instrument_type,
    #                                       pricing_currency=self.usd, price_multiplier=1.0,
    #                                       accrued_currency=self.usd, accrued_multiplier=1.0)
    #
    #     PriceHistory.objects.create(instrument=instr, pricing_policy=self.pp,
    #                                 date=self._d(1), principal_price=8.0, accrued_price=0.0)
    #     PriceHistory.objects.create(instrument=instr, pricing_policy=self.pp,
    #                                 date=self._d(2), principal_price=10.0, accrued_price=0.0)
    #     PriceHistory.objects.create(instrument=instr, pricing_policy=self.pp,
    #                                 date=self._d(3), principal_price=10.5, accrued_price=0.0)
    #     PriceHistory.objects.create(instrument=instr, pricing_policy=self.pp,
    #                                 date=self._d(4), principal_price=11.0, accrued_price=0.0)
    #     PriceHistory.objects.create(instrument=instr, pricing_policy=self.pp,
    #                                 date=self._d(5), principal_price=11.5, accrued_price=0.0)
    #     PriceHistory.objects.create(instrument=instr, pricing_policy=self.pp,
    #                                 date=self._d(6), principal_price=12.0, accrued_price=0.0)
    #     PriceHistory.objects.create(instrument=instr, pricing_policy=self.pp,
    #                                 date=self._d(7), principal_price=12.5, accrued_price=0.0)
    #     PriceHistory.objects.create(instrument=instr, pricing_policy=self.pp,
    #                                 date=self._d(8), principal_price=13.0, accrued_price=0.0)
    #
    #     PriceHistory.objects.create(instrument=instr, pricing_policy=self.pp,
    #                                 date=self._d(14), principal_price=15.0, accrued_price=0.0)
    #
    #     self._t(t_class=self._sell, instr=instr, position=-5,
    #             stl_ccy=self.usd, principal=40.0, carry=0.0, overheads=0.0,
    #             acc_date_days=1, cash_date_days=1, s1_pos=s1, s1_cash=s1)
    #
    #     self._t(t_class=self._buy, instr=instr, position=10,
    #             stl_ccy=self.usd, principal=-100.0, carry=0.0, overheads=0.0,
    #             acc_date_days=2, cash_date_days=2, s1_pos=s1, s1_cash=s1)
    #
    #     self._t(t_class=self._buy, instr=instr, position=10,
    #             stl_ccy=self.usd, principal=-105.0, carry=0.0, overheads=0.0,
    #             acc_date_days=3, cash_date_days=3, s1_pos=s1, s1_cash=s1)
    #
    #     self._t(t_class=self._buy, instr=instr, position=10,
    #             stl_ccy=self.usd, principal=-110.0, carry=0.0, overheads=0.0,
    #             acc_date_days=4, cash_date_days=4, s1_pos=s1, s1_cash=s1)
    #
    #     self._t(t_class=self._sell, instr=instr, position=-20,
    #             stl_ccy=self.usd, principal=230.0, carry=0.0, overheads=0.0,
    #             acc_date_days=5, cash_date_days=5, s1_pos=s2, s1_cash=s2)
    #
    #     self._t(t_class=self._buy, instr=instr, position=10,
    #             stl_ccy=self.usd, principal=-120.0, carry=0.0, overheads=0.0,
    #             acc_date_days=6, cash_date_days=6, s1_pos=s3, s1_cash=s3)
    #
    #     self._t(t_class=self._sell, instr=instr, position=-20,
    #             stl_ccy=self.usd, principal=250.0, carry=0.0, overheads=0.0,
    #             acc_date_days=7, cash_date_days=7, s1_pos=s2, s1_cash=s2)
    #
    #     self._t(t_class=self._sell, instr=instr, position=-10,
    #             stl_ccy=self.usd, principal=130.0, carry=0.0, overheads=0.0,
    #             acc_date_days=8, cash_date_days=8, s1_pos=s4, s1_cash=s4)
    #
    #     r = Report(master_user=self.m, pricing_policy=self.pp, report_date=self._d(14),
    #                cost_method=self._avco)
    #     b = ReportBuilder(instance=r)
    #     b.build()
    #     self._dump(b, 'test_pl_real_unreal_1')

    # def _test_pl_fx_fix_full_0(self):
    #     instr = Instrument.objects.create(master_user=self.m, name="I1, RUB/RUB",
    #                                       instrument_type=self.m.instrument_type,
    #                                       pricing_currency=self.rub, price_multiplier=1.0,
    #                                       accrued_currency=self.rub, accrued_multiplier=1.0)
    #
    #     # self.m.system_currency = self.cad
    #     # self.m.save()
    #
    #     self._instr_hist(instr, self._d(101), 1.0, 1.0)
    #     self._instr_hist(instr, self._d(102), 1.0, 1.0)
    #     self._instr_hist(instr, self._d(103), 1.0, 1.0)
    #     self._instr_hist(instr, self._d(104), 240.0, 160.0)
    #
    #     self._ccy_hist(self.gbp, self._d(101), 1.1)
    #     self._ccy_hist(self.eur, self._d(102), 1.15)
    #     self._ccy_hist(self.chf, self._d(103), 0.9)
    #
    #     self._ccy_hist(self.gbp, self._d(104), 1.2)
    #     self._ccy_hist(self.eur, self._d(104), 1.1)
    #     self._ccy_hist(self.chf, self._d(104), 1.0)
    #     self._ccy_hist(self.cad, self._d(104), 0.9)
    #     self._ccy_hist(self.rub, self._d(104), 1.0 / 65.0)
    #     # for ch in CurrencyHistory.objects.order_by('currency__user_code', '-date').filter(date__gte=self._d(100)):
    #     #     _l.debug(ch.currency.user_code, ch.date, ch.fx_rate)
    #
    #     self._t(t_class=self._buy, instr=instr, position=5,
    #             stl_ccy=self.gbp, principal=-20.0, carry=-5.0,
    #             trn_ccy=self.usd, fx_rate=1.5,
    #             acc_date_days=101, cash_date_days=101)
    #
    #     self._t(t_class=self._buy, instr=instr, position=5,
    #             stl_ccy=self.eur, principal=-22.0, carry=-8.0,
    #             trn_ccy=self.usd, fx_rate=1.3,
    #             acc_date_days=102, cash_date_days=102)
    #
    #     self._t(t_class=self._sell, instr=instr, position=-5,
    #             stl_ccy=self.chf, principal=25.0, carry=9.0,
    #             trn_ccy=self.usd, fx_rate=1.1,
    #             acc_date_days=103, cash_date_days=103)
    #
    #     r = Report(master_user=self.m, pricing_policy=self.pp, report_date=self._d(104), report_currency=self.cad,
    #                cost_method=self._avco)
    #     b = ReportBuilder(instance=r)
    #     b.build()
    #     self._dump(b, 'test_pl_fx_fix_full_0')

    def _test_pl_full_fx_fixed_buy_sell_1(self):
        instr = Instrument.objects.create(master_user=self.m, name="I1, RUB/RUB",
                                          instrument_type=self.m.instrument_type,
                                          pricing_currency=self.rub, price_multiplier=1.0,
                                          accrued_currency=self.rub, accrued_multiplier=1.0)

        # self.m.system_currency = self.cad
        # self.m.save()

        self._instr_hist(instr, self._d(101), 1.0, 1.0)
        self._instr_hist(instr, self._d(104), 240.0, 160.0)

        self._ccy_hist(self.gbp, self._d(101), 1.45)
        self._ccy_hist(self.gbp, self._d(104), 1.3)

        self._ccy_hist(self.eur, self._d(101), 1.25)
        self._ccy_hist(self.eur, self._d(104), 1.1)

        self._ccy_hist(self.rub, self._d(101), 1 / 60)
        self._ccy_hist(self.rub, self._d(104), 1 / 65)

        self._ccy_hist(self.chf, self._d(101), 1.15)
        self._ccy_hist(self.chf, self._d(104), 1.05)

        self._ccy_hist(self.cad, self._d(101), 1.1)
        self._ccy_hist(self.cad, self._d(104), 1.2)

        self._t(t_class=self._buy, instr=instr, position=5,
                stl_ccy=self.gbp, principal=-20.0, carry=-5.0,
                trn_ccy=self.rub, fx_rate=80,
                acc_date_days=101, cash_date_days=101)

        self._t(t_class=self._buy, instr=instr, position=5,
                stl_ccy=self.eur, principal=-22.0, carry=-8.0,
                trn_ccy=self.usd, fx_rate=1.3,
                acc_date_days=101, cash_date_days=101)

        self._t(t_class=self._sell, instr=instr, position=-5,
                stl_ccy=self.chf, principal=25.0, carry=9.0,
                trn_ccy=self.usd, fx_rate=1.1,
                acc_date_days=101, cash_date_days=101)

        r = Report(master_user=self.m, pricing_policy=self.pp, report_date=self._d(104), report_currency=self.cad,
                   cost_method=self._avco, approach_multiplier=1.0)
        b = ReportBuilder(instance=r)
        b.build()
        self._dump(b, 'test_pl_full_fx_fixed_buy_sell_1')

    def _test_pl_full_fx_fixed_cash_in_out_1(self):
        self._ccy_hist(self.gbp, self._d(101), 1.45)
        self._ccy_hist(self.gbp, self._d(104), 1.2)

        self._ccy_hist(self.chf, self._d(101), 1.15)
        self._ccy_hist(self.chf, self._d(104), 1.1)

        self._ccy_hist(self.cad, self._d(101), 0.85)
        self._ccy_hist(self.cad, self._d(104), 0.9)

        self._t(t_class=self._cash_inflow,
                trn_ccy=self.gbp, position=0,
                stl_ccy=self.chf, cash=100, fx_rate=0.75,
                acc_date_days=101, cash_date_days=101,
                alloc_bl=self.bond1, alloc_pl=self.bond2)

        self._t(t_class=self._cash_inflow,
                trn_ccy=self.gbp, position=0,
                stl_ccy=self.rub, cash=100, fx_rate=0.75,
                acc_date_days=101, cash_date_days=101,
                alloc_bl=self.bond1, alloc_pl=self.bond2)

        r = Report(master_user=self.m, pricing_policy=self.pp, report_date=self._d(104), report_currency=self.cad,
                   cost_method=self._avco)
        b = ReportBuilder(instance=r)
        b.build()
        self._dump(b, 'test_pl_full_fx_fixed_cash_in_out_1')

    def _test_pl_full_fx_fixed_instr_pl_1(self):
        self._ccy_hist(self.gbp, self._d(101), 1.45)
        self._ccy_hist(self.gbp, self._d(104), 1.2)

        self._ccy_hist(self.chf, self._d(101), 1.15)
        self._ccy_hist(self.chf, self._d(104), 1.1)

        self._ccy_hist(self.cad, self._d(101), 0.85)
        self._ccy_hist(self.cad, self._d(104), 0.9)

        self._t(t_class=self._instrument_pl,
                instr=self.bond0,
                trn_ccy=self.gbp, position=0,
                stl_ccy=self.chf, carry=1000, overheads=-20, fx_rate=0.75,
                acc_date_days=101, cash_date_days=101,
                alloc_bl=self.bond1, alloc_pl=self.bond2)

        r = Report(master_user=self.m, pricing_policy=self.pp, report_date=self._d(104), report_currency=self.cad,
                   cost_method=self._avco)
        b = ReportBuilder(instance=r)
        b.build()
        self._dump(b, 'test_pl_full_fx_fixed_instr_pl_1')

    def _test_pl_full_fx_fixed_trn_pl_1(self):
        self._ccy_hist(self.gbp, self._d(101), 1.45)
        self._ccy_hist(self.gbp, self._d(104), 1.2)

        self._ccy_hist(self.chf, self._d(101), 1.15)
        self._ccy_hist(self.chf, self._d(104), 1.1)

        self._ccy_hist(self.cad, self._d(101), 0.85)
        self._ccy_hist(self.cad, self._d(104), 0.9)

        self._t(t_class=self._transaction_pl,
                trn_ccy=self.gbp, position=0,
                stl_ccy=self.chf, carry=1000, overheads=-20, fx_rate=0.75,
                acc_date_days=101, cash_date_days=101,
                alloc_bl=self.bond1, alloc_pl=self.bond2)

        r = Report(master_user=self.m, pricing_policy=self.pp, report_date=self._d(104), report_currency=self.cad,
                   cost_method=self._avco)
        b = ReportBuilder(instance=r)
        b.build()
        self._dump(b, 'test_pl_full_fx_fixed_trn_pl_1')

    def _test_pl_full_fx_fixed_fx_trade_1(self):
        self._ccy_hist(self.gbp, self._d(101), 1.45)
        self._ccy_hist(self.gbp, self._d(104), 1.2)

        self._ccy_hist(self.chf, self._d(101), 1.15)
        self._ccy_hist(self.chf, self._d(104), 1.1)

        self._ccy_hist(self.cad, self._d(101), 0.85)
        self._ccy_hist(self.cad, self._d(104), 0.9)

        self._ccy_hist(self.rub, self._d(101), 1 / 60)
        self._ccy_hist(self.rub, self._d(104), 1 / 65)

        self._t(t_class=self._fx_tade,
                trn_ccy=self.gbp, position=100,
                stl_ccy=self.chf, principal=-140,
                acc_date_days=101, cash_date_days=101,
                alloc_bl=self.bond1, alloc_pl=self.bond2)

        self._t(t_class=self._fx_tade,
                trn_ccy=self.gbp, position=100,
                stl_ccy=self.rub, principal=-140,
                acc_date_days=101, cash_date_days=101,
                alloc_bl=self.bond1, alloc_pl=self.bond2)

        r = Report(master_user=self.m, pricing_policy=self.pp, report_date=self._d(104), report_currency=self.cad,
                   cost_method=self._avco)
        b = ReportBuilder(instance=r)
        b.build()
        self._dump(b, 'test_pl_full_fx_fixed_fx_trade_1')

    def _test_mismatch_0(self):
        for i in range(0, 2):
            self._t(t_class=self._buy,
                    instr=self.bond0, position=100,
                    stl_ccy=self.cad, cash=-10, principal=0, carry=0, overheads=0,
                    p=self.p1, acc_pos=self.a1_1,
                    link_instr=self.bond1)

            self._t(t_class=self._buy,
                    instr=self.bond0, position=100,
                    stl_ccy=self.chf, cash=0, principal=-10, carry=0, overheads=0,
                    p=self.p1, acc_pos=self.a1_1,
                    link_instr=self.bond1)

            self._t(t_class=self._buy,
                    instr=self.bond0, position=100,
                    stl_ccy=self.usd, cash=0, principal=0, carry=10, overheads=0,
                    p=self.p2, acc_pos=self.a1_2,
                    link_instr=self.bond1)

            self._t(t_class=self._buy,
                    instr=self.bond0, position=100,
                    stl_ccy=self.rub, cash=0, principal=0, carry=0, overheads=10,
                    p=self.p2, acc_pos=self.a1_2,
                    link_instr=self.bond1)

        r = Report(master_user=self.m, pricing_policy=self.pp, report_date=self._d(14))
        b = ReportBuilder(instance=r)
        b.build()
        self._dump(b, 'test_mismatch_0')

    def _test_approach_alloc_0(self):
        # settings.DEBUG = True

        self.bond0.user_code = 'I1'
        self.bond0.price_multiplier = 5.0
        self.bond0.accrued_multiplier = 0.0
        self.bond0.save()
        self.bond1.user_code = 'A1'
        self.bond1.save()
        self.bond2.user_code = 'A2'
        self.bond2.save()
        self.bond3.user_code = 'A3'
        self.bond3.save()
        self._t(t_class=self._buy,
                instr=self.bond0, position=5,
                stl_ccy=self.usd, principal=-10, carry=0, overheads=0,
                alloc_bl=self.bond1, alloc_pl=self.bond1)

        self._t(t_class=self._buy,
                instr=self.bond0, position=5,
                stl_ccy=self.usd, principal=-15, carry=0, overheads=0,
                alloc_bl=self.bond2, alloc_pl=self.bond2)

        self._t(t_class=self._sell,
                instr=self.bond0, position=-5,
                stl_ccy=self.usd, principal=20, carry=0, overheads=0,
                alloc_bl=self.bond3, alloc_pl=self.bond3)

        r = Report(master_user=self.m, pricing_policy=self.pp, report_date=self._d(10),
                   approach_multiplier=1.0)
        b = ReportBuilder(instance=r)
        b.build()
        self._dump(b, 'test_approach_alloc_0')

    def _test_approach_alloc_1(self):
        self.bond0.user_code = 'instr1'
        self.bond0.save()
        self.bond1.user_code = 'A1'
        self.bond1.save()
        self.bond2.user_code = 'A2'
        self.bond2.save()
        self.bond3.user_code = 'A3'
        self.bond3.save()

        self._t(t_class=self._buy,
                instr=self.bond0, position=5,
                stl_ccy=self.usd, principal=-100, carry=0, overheads=0,
                alloc_bl=self.bond1, alloc_pl=self.bond2)

        self._t(t_class=self._buy,
                instr=self.bond0, position=5,
                stl_ccy=self.usd, principal=-150, carry=0, overheads=0,
                alloc_bl=self.bond1, alloc_pl=self.bond2)

        self._t(t_class=self._sell,
                instr=self.bond0, position=-10,
                stl_ccy=self.usd, principal=450, carry=0, overheads=0,
                alloc_bl=self.bond1, alloc_pl=self.bond2)

        r = Report(master_user=self.m, pricing_policy=self.pp, report_date=self._d(0),
                   approach_multiplier=1.0)
        b = ReportBuilder(instance=r)
        b.build()
        self._dump(b, 'test_approach_alloc_1')

    def _test_approach_str1_0(self):
        self.bond0.user_code = 'I1'
        self.bond0.price_multiplier = 5.0
        self.bond0.accrued_multiplier = 0.0
        self.bond0.save()
        self.bond1.user_code = 'A1'
        self.bond1.save()
        self.bond2.user_code = 'A2'
        self.bond2.save()
        self.bond3.user_code = 'A3'
        self.bond3.save()
        approach_multiplier = 1.0

        self._t(t_class=self._buy,
                instr=self.bond0, position=5,
                stl_ccy=self.usd, principal=-10, carry=0, overheads=0,
                alloc_bl=self.bond1, alloc_pl=self.bond1,
                s1_pos=self.s1_1_1_1)

        self._t(t_class=self._buy,
                instr=self.bond0, position=5,
                stl_ccy=self.usd, principal=-15, carry=0, overheads=0,
                alloc_bl=self.bond2, alloc_pl=self.bond2,
                s1_pos=self.s1_1_1_2)

        self._t(t_class=self._sell,
                instr=self.bond0, position=-5,
                stl_ccy=self.usd, principal=20, carry=0, overheads=0,
                alloc_bl=self.bond3, alloc_pl=self.bond3,
                s1_pos=self.s1_1_1_3)

        r = Report(master_user=self.m, pricing_policy=self.pp, report_date=self._d(0),
                   approach_multiplier=approach_multiplier,
                   strategy1_mode=Report.MODE_INDEPENDENT)
        b = ReportBuilder(instance=r)
        b.build()
        self._dump(b, 'test_approach_str1_0: STRATEGY_INDEPENDENT')

        r = Report(master_user=self.m, pricing_policy=self.pp, report_date=self._d(0),
                   approach_multiplier=approach_multiplier,
                   strategy1_mode=Report.MODE_INTERDEPENDENT)
        b = ReportBuilder(instance=r)
        b.build()
        self._dump(b, 'test_approach_str1_0: STRATEGY_INTERDEPENDENT')

    def _test_instr_contract_for_difference(self):
        tinstr = InstrumentType.objects.create(master_user=self.m,
                                               instrument_class_id=InstrumentClass.CONTRACT_FOR_DIFFERENCE, name='cfd1')
        instr = Instrument.objects.create(master_user=self.m, name="cfd, USD/USD", instrument_type=tinstr,
                                          pricing_currency=self.usd, price_multiplier=1.0,
                                          accrued_currency=self.usd, accrued_multiplier=1.0)

        t0 = self._t(t_class=self._buy, instr=instr, position=3, acc_date_days=1, cash_date_days=1,
                     stl_ccy=self.usd, cash=0, principal=-3600000, carry=-5000, overheads=-100)
        t1 = self._t(t_class=self._buy, instr=instr, position=2, acc_date_days=2, cash_date_days=2,
                     stl_ccy=self.usd, cash=0, principal=-2450000, carry=-2000, overheads=-100)
        t2 = self._t(t_class=self._buy, instr=instr, position=1, acc_date_days=3, cash_date_days=3,
                     stl_ccy=self.usd, cash=0, principal=-1230000, carry=-1000, overheads=-100)
        t3 = self._t(t_class=self._sell, instr=instr, position=-1, acc_date_days=4, cash_date_days=4,
                     stl_ccy=self.usd, cash=0, principal=1250000, carry=8000, overheads=-100)
        t4 = self._t(t_class=self._sell, instr=instr, position=-3, acc_date_days=5, cash_date_days=5,
                     stl_ccy=self.usd, cash=0, principal=3825000, carry=9000, overheads=-100)

        from poms.transactions.utils import calc_cash_for_contract_for_difference
        calc_cash_for_contract_for_difference(transaction=None,
                                              instrument=instr,
                                              portfolio=self.m.portfolio,
                                              account=self.m.account,
                                              member=None,
                                              is_calculate_for_newer=False,
                                              is_calculate_for_all=True,
                                              save=True)

    def _test_xnpv_xirr_duration(self):
        from poms.common.formula_accruals import f_xnpv, f_xirr, f_duration
        from datetime import date

        # dates = [date(2008, 1, 1), date(2008, 3, 1), date(2008, 10, 30), date(2009, 2, 15), date(2009, 4, 1), ]
        # values = [-10000, 2750, 4250, 3250, 2750, ]

        # dates = [date(2016, 2, 16), date(2016, 3, 10), date(2016, 9, 1), date(2017, 1, 17), ]
        # values = [-90, 5, 5, 105, ]

        dates = [date(2016, 2, 16), date(2016, 3, 10), date(2016, 9, 1), date(2017, 1, 17), ]
        values = [-90, 5, 5, 105, ]
        data = [(d, v) for d, v in zip(dates, values)]

        # xnpv    : 16.7366702148651
        # xirr    : 0.3291520343150294
        # duration: 0.6438341602180792
        _l.debug('>')
        _l.debug('xnpv.1: %s', f_xnpv(data, 0.09))
        _l.debug('xirr.1: %s', f_xirr(data))
        # _l.debug('xirr.2: %s', f_xirr(data, method='newton'))
        _l.debug('duration.1: %s', f_duration(data))

        import timeit
        for i in range(100, 1000, 100):
            _l.debug('timeit.xirr.1.skip: %s -> %s', i, timeit.Timer(lambda: f_xirr(data)).timeit(i))

        ti1 = Instrument.objects.create(master_user=self.m, name="a", instrument_type=self.m.instrument_type,
                                        pricing_currency=self.usd, price_multiplier=1.0,
                                        accrued_currency=self.usd, accrued_multiplier=1.0,
                                        maturity_date=date(2017, 1, 1), maturity_price=100)
        AccrualCalculationSchedule.objects.create(instrument=ti1,
                                                  accrual_start_date=date(2016, 1, 1),
                                                  first_payment_date=date(2016, 2, 1),
                                                  accrual_size=5,
                                                  accrual_calculation_model_id=AccrualCalculationModel.ACT_365,
                                                  periodicity_id=Periodicity.MONTHLY,
                                                  periodicity_n=1)
        _l.debug('get_future_accrual_payments.1: %s', ti1.get_future_accrual_payments())
        _l.debug('get_future_accrual_payments.2: %s', ti1.get_future_accrual_payments(begin_date=date(2016, 2, 27)))
        _l.debug('get_future_accrual_payments.2: %s', ti1.get_future_accrual_payments(begin_date=date(2016, 3, 1)))
        data = [(date(2016, 3, 14), 83)]
        _l.debug('get_future_accrual_payments.2: %s',
                 ti1.get_future_accrual_payments(data=data, begin_date=date(2016, 3, 15)))
        _l.debug('get_future_accrual_payments.2: %s', ti1.get_future_accrual_payments(data=data))

    def _test_xnpv_xirr_duration_perf(self):
        from poms.common.formula_accruals import f_xirr
        from datetime import date

        dates = [date(2016, 2, 16), date(2016, 3, 10), date(2016, 9, 1), date(2017, 1, 17), ]
        values = [-90, 5, 5, 105, ]
        data = [(d, v) for d, v in zip(dates, values)]

        import timeit

        _l.debug('-' * 79)
        _l.debug('xirr:')
        # for method in ['newton', 'brentq']:
        #     _l.debug('  method: %s', method)
        #     for i in range(1000, 30000, 1000):
        #         _l.debug('    %s -> %s', i, timeit.Timer(lambda: f_xirr(data, method=method)).timeit(i))
        for i in range(1000, 30000, 1000):
            _l.debug('    %s -> %s', i, timeit.Timer(lambda: f_xirr(data)).timeit(i))

    def _test_pl_date_interval_1(self):
        show_trns = False

        self._t(t_class=self._buy, instr=self.bond0, position=100,
                stl_ccy=self.usd, principal=-180., carry=-5., overheads=-15.,
                acc_date_days=1, cash_date_days=1)

        self._t(t_class=self._sell, instr=self.bond0, position=-50,
                stl_ccy=self.usd, principal=90., carry=2.5, overheads=-15.,
                acc_date_days=11, cash_date_days=11)

        self._t(t_class=self._sell, instr=self.bond0, position=-50,
                stl_ccy=self.usd, principal=90., carry=2.5, overheads=-15.,
                acc_date_days=21, cash_date_days=21)

        pl_first_date = self._d(10)
        # report_date = self._d(12)
        report_date = self._d(22)

        r = Report(master_user=self.m, pricing_policy=self.pp, report_date=pl_first_date)
        b = ReportBuilder(instance=r)
        b.build()
        self._dump(b, 'test_pl_date_interval_1: pl_first_date', show_trns=show_trns)

        r = Report(master_user=self.m, pricing_policy=self.pp, report_date=report_date)
        b = ReportBuilder(instance=r)
        b.build()
        self._dump(b, 'test_pl_date_interval_1: report_date', show_trns=show_trns)

        r = Report(master_user=self.m, pricing_policy=self.pp, pl_first_date=pl_first_date, report_date=report_date)
        b = ReportBuilder(instance=r)
        b.build()
        self._dump(b, 'test_pl_date_interval_1: pl_first_date abd report_date', show_trns=show_trns)
