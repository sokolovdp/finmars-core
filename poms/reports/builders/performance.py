import logging
import time
from collections import OrderedDict
from datetime import date

from django.db import transaction
from django.db.models import Q
from django.utils.functional import cached_property, SimpleLazyObject

from poms.common import formula
from poms.reports.builders.base_builder import BaseReportBuilder
from poms.reports.builders.performance_item import PerformanceReport, PerformancePeriod
from poms.reports.builders.performance_virt_trn import PerformanceVirtualTransaction
from poms.reports.builders.pricing import FakeInstrumentPricingProvider, InstrumentPricingProvider, \
    FakeCurrencyFxRateProvider, CurrencyFxRateProvider
from poms.transactions.models import TransactionClass

_l = logging.getLogger('poms.reports')


class PerformanceReportBuilder(BaseReportBuilder):
    def __init__(self, instance, pricing_provider=None, fx_rate_provider=None):
        super(PerformanceReportBuilder, self).__init__(instance)

        self._pricing_provider = pricing_provider
        self._fx_rate_provider = fx_rate_provider
        self._transactions = None
        # self._periods = []
        # self._items = OrderedDict()

    def build(self):
        st = time.perf_counter()
        _l.debug('build transaction')

        with transaction.atomic():
            try:
                self._load()
                self._clone_if_need()
                self._process_periods()
                self._calc()

                # self.instance.items = [
                #     PerformanceReportItem(
                #         self.instance,
                #         id=x,
                #         period_name='P-%s' % (x // 10),
                #         period_begin=date_now() + timedelta(days=x // 10),
                #         period_end=date_now() + timedelta(days=(x + 1) // 10 - 1),
                #         portfolio=self.instance.master_user.portfolio,
                #         account=self.instance.master_user.account,
                #         strategy1=self.instance.master_user.strategy1,
                #         strategy2=self.instance.master_user.strategy2,
                #         strategy3=self.instance.master_user.strategy3,
                #     )
                #     for x in range(0, 200)]
                # for i in self.instance.items:
                #     i.random()

                if self.instance.has_errors:
                    self.instance.items = []

                self._refresh_from_db()
            finally:
                transaction.set_rollback(True)

        _l.debug('done: %s', (time.perf_counter() - st))
        return self.instance

    def _trn_qs(self):
        qs = super(PerformanceReportBuilder, self)._trn_qs()

        filters = Q()

        if self.instance.begin_date:
            filters &= Q(accounting_date__gte=self.instance.begin_date)

        if self.instance.end_date:
            filters &= Q(accounting_date__lte=self.instance.end_date)

        qs = qs.filter(filters)

        qs = qs.order_by('accounting_date', 'transaction_code')

        return qs

    def _load(self):
        _l.debug('> _load')

        trns = []

        qs = self._trn_qs()
        for t in qs:
            overrides = {}

            if self.instance.portfolio_mode == PerformanceReport.MODE_IGNORE:
                overrides['portfolio'] = self.instance.master_user.portfolio

            if self.instance.account_mode == PerformanceReport.MODE_IGNORE:
                overrides['account_position'] = self.instance.master_user.account
                overrides['account_cash'] = self.instance.master_user.account
                overrides['account_interim'] = self.instance.master_user.account

            if self.instance.strategy1_mode == PerformanceReport.MODE_IGNORE:
                overrides['strategy1_position'] = self.instance.master_user.strategy1
                overrides['strategy1_cash'] = self.instance.master_user.strategy1

            if self.instance.strategy2_mode == PerformanceReport.MODE_IGNORE:
                overrides['strategy2_position'] = self.instance.master_user.strategy2
                overrides['strategy2_cash'] = self.instance.master_user.strategy2

            if self.instance.strategy3_mode == PerformanceReport.MODE_IGNORE:
                overrides['strategy3_position'] = self.instance.master_user.strategy3
                overrides['strategy3_cash'] = self.instance.master_user.strategy3

            # if self.instance.allocation_mode == PerformanceReport.MODE_IGNORE:
            #     overrides['allocation_balance'] = self.instance.master_user.instrument
            #     overrides['allocation_pl'] = self.instance.master_user.instrument

            trn = PerformanceVirtualTransaction(
                report=self.instance,
                pricing_provider=self.pricing_provider,
                fx_rate_provider=self.fx_rate_provider,
                trn=t,
                overrides=overrides
            )
            trns.append(trn)

        self._transactions = trns

        _l.debug('< _load: %s', len(self._transactions))

    def _clone_if_need(self):
        _l.debug('> clone_transactions_if_need')

        res = []
        for trn in self._transactions:
            res.append(trn)

            if trn.trn_cls.id == TransactionClass.FX_TRADE:
                trn.is_hidden = True

                trn1, trn2 = trn.fx_trade_clone()
                res.append(trn1)
                res.append(trn2)

            elif trn.trn_cls.id == TransactionClass.TRANSFER:
                trn.is_hidden = True
                # split TRANSFER to sell/buy or buy/sell
                if trn.pos_size >= 0:
                    trn1, trn2 = trn.transfer_clone(self._trn_cls_sell, self._trn_cls_buy,
                                                    t1_pos_sign=1.0, t1_cash_sign=-1.0)
                else:
                    trn1, trn2 = trn.transfer_clone(self._trn_cls_buy, self._trn_cls_sell,
                                                    t1_pos_sign=-1.0, t1_cash_sign=1.0)
                res.append(trn1)
                res.append(trn2)

            elif trn.trn_cls.id == TransactionClass.FX_TRANSFER:
                trn.is_hidden = True

                trn1, trn2 = trn.fx_transfer_clone(trn_cls_out=self._trn_cls_cash_out,
                                                   trn_cls_in=self._trn_cls_cash_in)
                res.append(trn1)
                res.append(trn2)

        self._transactions = res

        _l.debug('< clone_transactions_if_need: %s', len(self._transactions))

    def _process_periods(self):
        _l.debug('> process periods')

        context = self.instance.context.copy()
        context['date_group_with_dates'] = True

        for trn in self._transactions:
            try:
                period = formula.safe_eval(self.instance.periods, names={'transaction': trn.trn}, context=context)
            except formula.InvalidExpression:
                self.instance.has_errors = True
                _l.debug('periods error', exc_info=True)
                return

            if isinstance(period, (tuple, list)):
                name, begin, end = period
                name = str(name)
                if not isinstance(begin, date) or not isinstance(end, date):
                    _l.debug('hacker detected on: %s', self.instance.periodss)
            else:
                name, begin, end = None, None, None

            trn.set_period(name=name, begin=begin, end=end)

        _l.debug('< process periods')

    @cached_property
    def _instruments(self):
        assert self._transactions is not None
        instruments = {}
        for trn in self._transactions:
            if trn.instr:
                instruments[trn.instr.id] = trn.instr
        return list(instruments.values())

    @cached_property
    def _currencies(self):
        assert self._transactions is not None
        currencies = {self.instance.report_currency.id: self.instance.report_currency}
        for trn in self._transactions:
            if trn.trn_ccy:
                currencies[trn.trn_ccy.id] = trn.trn_ccy
            currencies[trn.stl_ccy.id] = trn.stl_ccy
        return list(currencies.values())

    @cached_property
    def _dates(self):
        assert self._transactions is not None
        dates = {t.period_end for t in self._transactions if t.period_end != date.min}
        return dates

    @property
    def pricing_provider(self):
        def _factory():
            assert self._transactions is not None

            if self._pricing_provider is None:
                if self.instance.pricing_policy is None:
                    p = FakeInstrumentPricingProvider(self.instance.master_user, None, None)
                else:
                    p = InstrumentPricingProvider(self.instance.master_user, self.instance.pricing_policy, None)
                    p.fill_using_instruments_and_dates(instruments=self._instruments, dates=self._dates)
                self._pricing_provider = p
            return self._pricing_provider

        return SimpleLazyObject(_factory)

    @property
    def fx_rate_provider(self):
        def _factory():
            assert self._transactions is not None

            if self._fx_rate_provider is None:
                if self.instance.pricing_policy is None:
                    p = FakeCurrencyFxRateProvider(self.instance.master_user, None, None)
                else:
                    p = CurrencyFxRateProvider(self.instance.master_user, self.instance.pricing_policy, None)
                    p.fill_using_currencies_and_dates(currencies=self._currencies, dates=self._dates)
                self._fx_rate_provider = p
            return self._fx_rate_provider

        return SimpleLazyObject(_factory)

    # def _get_key(self, period_key=None, prtfl=None, acc=None, str1=None, str2=None, str3=None):
    #     if self.instance.portfolio_mode == PerformanceReport.MODE_IGNORE:
    #         prtfl = getattr(prtfl, 'id', None)
    #     elif self.instance.portfolio_mode == PerformanceReport.MODE_INDEPENDENT:
    #         prtfl = None
    #     elif self.instance.portfolio_mode == PerformanceReport.MODE_INTERDEPENDENT:
    #         prtfl = None
    #
    #     if self.instance.account_mode == PerformanceReport.MODE_IGNORE:
    #         acc = getattr(acc, 'id', None)
    #     elif self.instance.account_mode == PerformanceReport.MODE_INDEPENDENT:
    #         acc = None
    #     elif self.instance.account_mode == PerformanceReport.MODE_INTERDEPENDENT:
    #         acc = None
    #
    #     if self.instance.strategy1_mode == PerformanceReport.MODE_IGNORE:
    #         str1 = getattr(str1, 'id', None)
    #     elif self.instance.strategy1_mode == PerformanceReport.MODE_INDEPENDENT:
    #         str1 = None
    #     elif self.instance.strategy1_mode == PerformanceReport.MODE_INTERDEPENDENT:
    #         str1 = None
    #
    #     if self.instance.strategy2_mode == PerformanceReport.MODE_IGNORE:
    #         str2 = getattr(str2, 'id', None)
    #     elif self.instance.strategy2_mode == PerformanceReport.MODE_INDEPENDENT:
    #         str2 = None
    #     elif self.instance.strategy2_mode == PerformanceReport.MODE_INTERDEPENDENT:
    #         str2 = None
    #
    #     if self.instance.strategy3_mode == PerformanceReport.MODE_IGNORE:
    #         str3 = getattr(str3, 'id', None)
    #     elif self.instance.strategy3_mode == PerformanceReport.MODE_INDEPENDENT:
    #         str3 = None
    #     elif self.instance.strategy3_mode == PerformanceReport.MODE_INTERDEPENDENT:
    #         str3 = None
    #
    #     return (
    #         period_key,
    #         prtfl if prtfl is not None else 0,
    #         acc if acc is not None else 0,
    #         str1 if str1 is not None else 0,
    #         str2 if str2 is not None else 0,
    #         str3 if str3 is not None else 0,
    #     )

    # def _get_pos_key(self, trn):
    #     # return self._get_key(trn.period_key, prtfl=trn.acc_pos, acc=trn.acc_pos, str1=trn.str1_pos,
    #     #                                    str2=trn.str3_pos, str3=trn.str3_pos)
    #     is_pos = False
    #     if trn.is_buy or trn.is_sell:
    #         is_pos = True
    #
    #     elif trn.is_cash_inflow or trn.is_cash_outflow:
    #         if trn.case in [0, 1]:
    #             is_pos = True
    #
    #     elif trn.is_instrument_pl:
    #         is_pos = True
    #
    #     elif trn.is_transaction_pl:
    #         if trn.case in [0, 1]:
    #             is_pos = True
    #
    #     elif trn.is_fx_trade:
    #         if trn.case in [0, 1]:
    #             is_pos = True
    #
    #     elif trn.is_transfer:
    #         pass
    #
    #     elif trn.is_fx_transfer:
    #         pass
    #
    #     else:
    #         pass
    #
    #     if is_pos:
    #         return self._get_key(trn.period_key, prtfl=trn.acc_pos, acc=trn.acc_pos,
    #                              str1=trn.str1_pos, str2=trn.str3_pos, str3=trn.str3_pos)
    #     return None
    #
    # def _get_cash_key(self, trn):
    #     is_ret = False
    #     if trn.is_buy or trn.is_sell:
    #         is_ret = True
    #
    #     elif trn.is_cash_inflow or trn.is_cash_outflow:
    #         is_ret = True
    #
    #     elif trn.is_instrument_pl:
    #         is_ret = True
    #
    #     elif trn.is_transaction_pl:
    #         is_ret = True
    #
    #     elif trn.is_fx_trade:
    #         is_ret = True
    #
    #     elif trn.is_transfer:
    #         pass
    #
    #     elif trn.is_fx_transfer:
    #         pass
    #
    #     else:
    #         pass
    #
    #     acc_key = None
    #     acc_interim_key = None
    #     if is_ret:
    #         is_acc = False
    #         is_acc_interim = False
    #         if trn.case == 0:
    #             is_acc = True
    #
    #         elif trn.case == 1:
    #             is_acc_interim = True
    #
    #         elif trn.case == 2:
    #             is_acc = True
    #             is_acc_interim = True
    #
    #         if is_acc:
    #             acc_key = self._get_key(trn.period_key, prtfl=trn.acc_pos, acc=trn.acc_cash,
    #                                     str1=trn.str1_cash, str2=trn.str3_cash, str3=trn.str3_cash)
    #         if is_acc_interim:
    #             acc_interim_key = self._get_key(trn.period_key, prtfl=trn.acc_interim, acc=trn.acc_cash,
    #                                             str1=trn.str1_cash, str2=trn.str3_cash, str3=trn.str3_cash)
    #     return acc_key, acc_interim_key

    # def _get_item(self, trn, is_pos=False, is_cash=False):
    #     period_key = trn.period_key
    #     prtfl = trn.prtfl
    #     if is_cash:
    #         acc = trn.acc_cash
    #         str1 = trn.str1_cash
    #         str2 = trn.str2_cash
    #         str3 = trn.str3_cash
    #     elif is_pos:
    #         acc = trn.acc_pos
    #         str1 = trn.str1_pos
    #         str2 = trn.str2_pos
    #         str3 = trn.str3_pos
    #     else:
    #         raise RuntimeError('bad args')
    #
    #     key = self._get_key(
    #         period_key=period_key,
    #         prtfl=prtfl,
    #         acc=acc,
    #         str1=str1,
    #         str2=str2,
    #         str3=str3
    #     )
    #     try:
    #         item = self._items[key]
    #         return item, False
    #     except KeyError:
    #         item = PerformanceReportItem(
    #             self.instance,
    #             id=key,
    #             period_begin=trn.period_begin,
    #             period_end=trn.period_end,
    #             period_name=trn.period_name,
    #             period_key=trn.period_key,
    #             portfolio=prtfl,
    #             account=acc,
    #             strategy1=str1,
    #             strategy2=str2,
    #             strategy3=str3
    #         )
    #         self._items[key] = item
    #         return item, True
    #
    # def _get_cash_item(self, trn):
    #     return self._get_item(trn=trn, is_cash=True)
    #
    # def _get_pos_item(self, trn):
    #     return self._get_item(trn=trn, is_pos=True)

    def _calc(self):
        _l.debug('> calc')

        periods = OrderedDict()

        _l.debug('find periods')
        for trn in self._transactions:
            if trn.period_key not in periods:
                period = PerformancePeriod(
                    self.instance,
                    period_begin=trn.period_begin,
                    period_end=trn.period_end,
                    period_name=trn.period_name,
                    period_key=trn.period_key
                )
                _l.debug('  %s', period)
                periods[trn.period_key] = period

        periods = list(periods.values())
        _l.debug('periods: %s', periods)

        _l.debug('make periods')
        for trn in self._transactions:
            # period_key = trn.period_key
            _l.debug('  trn: pk=%s, cls=%s, period_key=%s', trn.pk, trn.trn_cls, trn.period_key)

            if trn.is_hidden:
                _l.debug('    skip trn: is_hidden=%s', trn.is_hidden)
                continue

            for period in periods:
                if trn.period_key == period.period_key:
                    period.local_trns.append(trn.clone())
                if trn.period_key <= period.period_key:
                    period.trns.append(trn.clone())

        _l.debug('periods: %s', periods)

        _l.debug('load pricing and first calculations')
        for period in periods:
            _l.debug('  %s', period)
            for trn in period.local_trns:
                trn.perf_pricing()
                trn.perf_calc()

            for trn in period.trns:
                trn.processing_date = period.period_end
                trn.set_case()
                trn.perf_pricing()
                trn.perf_calc()

        _l.debug('calculating')
        for period in periods:
            _l.debug('period: %s', period)

            for trn in period.local_trns:
                period.cash_in_out_add(trn)
                pass

            for trn in period.trns:
                period.nav_add(trn)
                # period.pl_add(trn)
                # period.cash_in_out_add(trn)
                pass

            # # --------
            # _l.debug('items: local_trns=%s', len(period.trns))
            # for trn in period.local_trns:
            #     _l.debug('  pk=%s, cls=%s, period_key=%s', trn.pk, trn.trn_cls, trn.period_key)
            #     cash_item = self._create_cash_item(trn, interim=False)
            #     cash_item.set_as_cash(trn)
            #     period.items.append(cash_item)
            #
            #     pos_item = self._create_pos_item(trn)
            #     pos_item.set_as_pos(trn)
            #     period.items.append(pos_item)

        _l.debug('periods: %s', periods)

        _l.debug('aggregate: perids=%s', len(periods))
        prev_period = None
        for period in periods:
            period.close(prev_period)
            prev_period = period

        _l.debug('periods: %s', periods)

        items = []
        for period in periods:
            items.extend(period.items)

        _l.debug('items: %s', items)
        self.instance.items = items

        _l.debug('< calc')

    # def _add_mkt_val(self, items, trn):
    #     if trn.case == 0:
    #         if not isclose(trn.instr_mkt_val_res, 0):
    #             item = self._create_pos_item(trn, item_type=PerformanceReportItem.TYPE_MKT_VAL)
    #             item.mkt_val_res = trn.instr_mkt_val_res
    #             items.append(item)
    #
    #         if not isclose(trn.cash_mkt_val_res, 0):
    #             item = self._create_cash_item(trn, interim=False, item_type=PerformanceReportItem.TYPE_MKT_VAL)
    #             item.mkt_val_res = trn.cash_mkt_val_res
    #             items.append(item)
    #
    #     elif trn.case == 1:
    #         if not isclose(trn.instr_mkt_val_res, 0):
    #             item = self._create_pos_item(trn, item_type=PerformanceReportItem.TYPE_MKT_VAL)
    #             item.mkt_val_res = trn.instr_mkt_val_res
    #             items.append(item)
    #
    #         if not isclose(trn.cash_mkt_val_res, 0):
    #             item = self._create_cash_item(trn, interim=True, item_type=PerformanceReportItem.TYPE_MKT_VAL)
    #             item.mkt_val_res = trn.cash_mkt_val_res
    #             items.append(item)
    #
    #     elif trn.case == 2:
    #         if not isclose(trn.instr_mkt_val_res, 0):
    #             pass
    #
    #         if not isclose(trn.cash_mkt_val_res, 0):
    #             item = self._create_cash_item(trn, interim=False, item_type=PerformanceReportItem.TYPE_MKT_VAL)
    #             item.mkt_val_res = trn.cash_mkt_val_res
    #             items.append(item)
    #
    #             item = self._create_cash_item(trn, interim=True, item_type=PerformanceReportItem.TYPE_MKT_VAL)
    #             item.mkt_val_res = -trn.cash_mkt_val_res
    #             items.append(item)

    # def _add_pl(self, period, trn):
    #     if trn.case == 0:
    #         item = self._create_pos_item(trn, item_type=PerformanceReportItem.TYPE_PL)
    #         item.acc_date = trn.acc_date
    #         item.processing_date = trn.processing_date
    #         item.cash_res = trn.cash_res
    #         item.principal_res = trn.principal_res
    #         item.carry_res = trn.carry_res
    #         item.overheads_res = trn.overheads_res
    #         item.total_res = trn.total_res
    #         period.items_pls.append(item)
    #
    #     elif trn.case == 1:
    #         item = self._create_pos_item(trn, item_type=PerformanceReportItem.TYPE_PL)
    #         item.acc_date = trn.acc_date
    #         item.processing_date = trn.processing_date
    #         item.cash_res = trn.cash_res
    #         item.principal_res = trn.principal_res
    #         item.carry_res = trn.carry_res
    #         item.overheads_res = trn.overheads_res
    #         item.total_res = trn.total_res
    #         period.items_pls.append(item)
    #
    #     elif trn.case == 2:
    #         pass
    #
    #     else:
    #         raise RuntimeError('Invalid transaction case: %s' % trn.case)

    # def _create_pos_item(self, trn, item_type=None):
    #     return PerformanceReportItem.from_trn(
    #         trn,
    #         item_type=item_type,
    #         portfolio=trn.prtfl,
    #         account=trn.acc_pos,
    #         strategy1=trn.str1_pos,
    #         strategy2=trn.str2_pos,
    #         strategy3=trn.str3_pos
    #     )
    #
    # def _create_cash_item(self, trn, interim=False, item_type=None):
    #     return PerformanceReportItem.from_trn(
    #         trn,
    #         item_type=item_type,
    #         portfolio=trn.prtfl,
    #         account=trn.acc_cash if not interim else trn.acc_interim,
    #         strategy1=trn.str1_cash,
    #         strategy2=trn.str2_cash,
    #         strategy3=trn.str3_cash
    #     )
    #
    # def _simple_aggregate(self, items):
    #     tmp_items = sorted(items, key=lambda x: x.group_key)
    #     res_items = []
    #     for k, g in groupby(tmp_items, key=lambda x: x.group_key):
    #         gitem = None
    #         for item in g:
    #             if gitem is None:
    #                 gitem = PerformanceReportItem.from_item(item)
    #             gitem.add(item)
    #
    #         if gitem:
    #             # gitem.close()
    #             res_items.append(gitem)
    #     return res_items

    # def _calc1(self):
    #     _l.debug('> calc')
    #
    #     periods = sorted({(x.period_begin, x.period_end, x.period_name) for x in self._transactions})
    #
    #     _l.debug('periods: len=%s', len(periods))
    #
    #     trns_per_periods = OrderedDict()
    #     items_per_periods = OrderedDict()
    #
    #     prev_period = None
    #
    #     for period in periods:
    #         period_begin, period_end, period_name = period
    #         period_key = (period_begin, period_end, period_name,)
    #
    #         # _l.debug('period: [%s:%s] %s', period_begin, period_end, period_name)
    #
    #         trns_per_period = []
    #         trns_per_periods[period_key] = trns_per_period
    #
    #         mkt_vals_per_period = OrderedDict()
    #
    #         # already ordered by accounting_date
    #         for trn in self._transactions:
    #             if trn.is_hidden:
    #                 continue
    #
    #             if trn.acc_date > period_end:
    #                 break
    #
    #             trn2 = trn.clone()
    #             trn2.processing_date = period_end
    #             trn2.perf_pricing()
    #             trn2.perf_calc()
    #             trns_per_period.append(trn2)
    #
    #             if trn2.is_buy or trn2.is_sell:
    #                 mkt_val_key = self._get_key(
    #                     pbegin=period_begin,
    #                     pend=period_end,
    #                     pname=period_name,
    #                     prtfl=trn.prtfl,
    #                     acc=trn.acc_pos,
    #                     str1=trn.str1_pos,
    #                     str2=trn.str2_pos,
    #                     str3=trn.str3_pos
    #                 )
    #                 try:
    #                     mkt_val = mkt_vals_per_period[mkt_val_key]
    #                 except KeyError:
    #                     mkt_val = trn2.perf_clone_as_mkt_val()
    #                     mkt_val.perf_calc()
    #                     mkt_vals_per_period[mkt_val_key] = mkt_val
    #
    #                 mkt_val.perf_mkt_val_add(trn2)
    #
    #         trns_per_period.extend(mkt_vals_per_period.values())
    #
    #         # ------
    #
    #         items_per_period = []
    #         items_per_periods[period_key] = items_per_period
    #         for trn in trns_per_period:
    #             if trn.is_mkt_val:
    #                 pass
    #             else:
    #                 pass
    #
    #             cash_item, cash_item_created = self._get_cash_item(trn)
    #             if cash_item_created:
    #                 items_per_period.append(cash_item)
    #             cash_item.cash_add(trn)
    #
    #             pos_item, pos_item_created = self._get_pos_item(trn)
    #             if pos_item_created:
    #                 items_per_period.append(pos_item)
    #             pos_item.pos_add(trn)
    #
    #         if prev_period:
    #             prev_period_begin, prev_period_end, prev_period_name = prev_period
    #         else:
    #             prev_period_begin, prev_period_end, prev_period_name = None, None, None
    #         for item in items_per_period:
    #             if prev_period:
    #                 prev_item_key = self._get_key(
    #                     pbegin=prev_period_begin,
    #                     pend=prev_period_end,
    #                     pname=prev_period_name,
    #                     prtfl=item.portfolio,
    #                     acc=item.account,
    #                     str1=item.strategy1,
    #                     str2=item.strategy2,
    #                     str3=item.strategy3
    #                 )
    #                 try:
    #                     prev_item = self._items[prev_item_key]
    #                 except KeyError:
    #                     prev_item = None
    #                 item.add_prev(prev_item)
    #             item.close()
    #
    #         prev_period = period
    #
    #     # prev_period = None
    #     # prev_items_per_period = None
    #     # for period, items_per_period in items_per_periods.items():
    #     #     period_begin, period_end, period_name = period
    #     #     if prev_period:
    #     #         prev_period_begin, prev_period_end, prev_period_name = prev_period
    #     #     else:
    #     #         prev_period_begin, prev_period_end, prev_period_name = None, None, None
    #     #
    #     #     for item in items_per_period:
    #     #         pass
    #     #
    #     #     prev_period = period
    #     #     prev_items_per_period = items_per_period
    #
    #     _l.debug('items: len=%s', len(self._items))
    #     self.instance.items = list(self._items.values())
    #
    #     _l.debug('< calc')

    def _refresh_from_db(self):
        _l.info('> refresh from db')

        self.instance.portfolios = self._refresh_portfolios(
            master_user=self.instance.master_user,
            items=None,
            attrs=None,
            objects=self.instance.portfolios
        )
        self.instance.accounts = self._refresh_accounts(
            master_user=self.instance.master_user,
            items=None,
            attrs=None,
            objects=self.instance.accounts
        )
        self.instance.accounts_position = self._refresh_accounts(
            master_user=self.instance.master_user,
            items=None,
            attrs=None,
            objects=self.instance.accounts_position
        )
        self.instance.accounts_cash = self._refresh_accounts(
            master_user=self.instance.master_user,
            items=None,
            attrs=None,
            objects=self.instance.accounts_cash
        )
        self.instance.strategies1 = self._refresh_strategies1(
            master_user=self.instance.master_user,
            items=None,
            attrs=None,
            objects=self.instance.strategies1
        )
        self.instance.strategies2 = self._refresh_strategies2(
            master_user=self.instance.master_user,
            items=None,
            attrs=None,
            objects=self.instance.strategies2
        )
        self.instance.strategies3 = self._refresh_strategies3(
            master_user=self.instance.master_user,
            items=None,
            attrs=None,
            objects=self.instance.strategies3
        )

        self.instance.item_portfolios = self._refresh_portfolios(
            master_user=self.instance.master_user,
            items=self.instance.items,
            attrs=['portfolio']
        )
        self.instance.item_accounts = self._refresh_accounts(
            master_user=self.instance.master_user,
            items=self.instance.items,
            attrs=['account']
        )
        self.instance.item_strategies1 = self._refresh_strategies1(
            master_user=self.instance.master_user,
            items=self.instance.items,
            attrs=['strategy1']
        )
        self.instance.item_strategies2 = self._refresh_strategies2(
            master_user=self.instance.master_user,
            items=self.instance.items,
            attrs=['strategy2']
        )
        self.instance.item_strategies3 = self._refresh_strategies3(
            master_user=self.instance.master_user,
            items=self.instance.items,
            attrs=['strategy3']
        )

        _l.info('< refresh from db')
