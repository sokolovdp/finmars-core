import logging
import time
from collections import defaultdict, OrderedDict

from datetime import date, timedelta

from django.db import transaction
from django.db.models import Q
from django.utils.functional import cached_property

from poms.common import formula
from poms.common.utils import date_now
from poms.reports.builders.base_builder import BaseReportBuilder
from poms.reports.builders.performance_item import PerformanceReportItem, PerformanceReport
from poms.reports.builders.pricing import FakeInstrumentPricingProvider, InstrumentPricingProvider, \
    FakeCurrencyFxRateProvider, CurrencyFxRateProvider

_l = logging.getLogger('poms.reports')


# added fields to transaction model:
# _is_cloned
# period_name
# period_begin
# period_end
# report_currency
# report_currency_history
# report_currency_fx_rate
# instrument_price
# instrument_principal_price
# instrument_accrued_price
# instrument_pricing_currency_history
# instrument_pricing_ccy_cur_fx_rate
# instrument_accrued_currency_history
# instrument_accrued_currency_fx_rate
# settlement_currency_history
# settlement_currency_fx_rate
# cash_consideration_sys
# principal_with_sign_sys
# carry_with_sign_sys
# overheads_with_sign_sys

class PerformanceReportBuilder(BaseReportBuilder):
    def __init__(self, instance, pricing_provider=None, fx_rate_provider=None):
        super(PerformanceReportBuilder, self).__init__(instance)

        self._pricing_provider = pricing_provider
        self._fx_rate_provider = fx_rate_provider
        self._transactions = None
        self._periods = []
        self._mkt_values = {}
        self._mkt_values_by_period = defaultdict(list)
        self._items = OrderedDict()

    def build(self):
        st = time.perf_counter()
        _l.debug('build transaction')

        with transaction.atomic():
            try:
                self._load()
                self._clone_transactions_if_need()
                self._process_periods()
                self._calc()

                self.instance.items = [
                    PerformanceReportItem(
                        self.instance,
                        id=x,
                        period_name='P-%s' % (x // 10),
                        period_begin=date_now() + timedelta(days=x // 10),
                        period_end=date_now() + timedelta(days=(x + 1) // 10 - 1),
                        portfolio=self.instance.master_user.portfolio,
                        account=self.instance.master_user.account,
                        strategy1=self.instance.master_user.strategy1,
                        strategy2=self.instance.master_user.strategy2,
                        strategy3=self.instance.master_user.strategy3,
                    )
                    for x in range(0, 200)]
                for i in self.instance.items:
                    i.random()

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
            # first consolidation processing

            if self.instance.portfolio_mode == PerformanceReport.MODE_IGNORE:
                t.portfolio = self.instance.master_user.portfolio

            if self.instance.account_mode == PerformanceReport.MODE_IGNORE:
                t.account_position = self.instance.master_user.account
                t.account_cash = self.instance.master_user.account
                t.account_interim = self.instance.master_user.account

            if self.instance.strategy1_mode == PerformanceReport.MODE_IGNORE:
                t.strategy1_position = self.instance.master_user.strategy1
                t.strategy1_cash = self.instance.master_user.strategy1

            if self.instance.strategy2_mode == PerformanceReport.MODE_IGNORE:
                t.strategy2_position = self.instance.master_user.strategy2
                t.strategy2_cash = self.instance.master_user.strategy2

            if self.instance.strategy3_mode == PerformanceReport.MODE_IGNORE:
                t.strategy3_position = self.instance.master_user.strategy3
                t.strategy3_cash = self.instance.master_user.strategy3

            trns.append(t)

        self._transactions = trns

        _l.debug('< _load: %s', len(self._transactions))

    def _clone_transactions_if_need(self):
        _l.debug('> clone_transactions_if_need')

        res = []
        for trn in self._transactions:
            if trn.is_transfer:
                trns = self._trn_transfer_clone(trn)
                res.extend(trns)

            elif trn.is_fx_transfer:
                trns = self._trn_fx_transfer_clone(trn)
                res.extend(trns)

            elif trn.is_fx_trade:
                trns = self._trn_fx_trade_clone(trn)
                res.extend(trns)

            else:
                res.append(trn)

        self._transactions = res

        _l.debug('< clone_transactions_if_need: %s', len(self._transactions))

    def _trn_transfer_clone(self, trn):
        # split TRANSFER to sell/buy or buy/sell
        if trn.position_size_with_sign >= 0:
            t1_cls = self._trn_cls_sell
            t2_cls = self._trn_cls_buy
            t1_pos_sign = 1.0
            t1_cash_sign = -1.0
        else:
            t1_cls = self._trn_cls_buy
            t2_cls = self._trn_cls_sell
            t1_pos_sign = -1.0
            t1_cash_sign = 1.0

        # t1
        t1 = self._clone(trn)
        t1.transaction_class = t1_cls

        t1.position_size_with_sign = abs(trn.position_size_with_sign) * t1_pos_sign
        t1.cash_consideration = abs(trn.cash_consideration) * t1_cash_sign
        t1.principal_with_sign = abs(trn.principal_with_sign) * t1_cash_sign
        t1.carry_with_sign = abs(trn.carry_with_sign) * t1_cash_sign
        t1.overheads_with_sign = abs(trn.overheads_with_sign) * t1_cash_sign

        t1.account_position = trn.account_cash
        t1.account_cash = trn.account_cash
        t1.strategy1_position = trn.strategy1_cash
        t1.strategy1_cash = trn.strategy1_cash
        t1.strategy2_position = trn.strategy2_cash
        t1.strategy2_cash = trn.strategy2_cash
        t1.strategy3_position = trn.strategy3_cash
        t1.strategy3_cash = trn.strategy3_cash

        # t2
        t2 = self._clone(trn)
        t2.transaction_class = t2_cls

        t2.position_size_with_sign = -t1.position_size_with_sign
        t2.cash_consideration = -t1.cash_consideration
        t2.principal_with_sign = -t1.principal_with_sign
        t2.carry_with_sign = -t1.carry_with_sign
        t2.overheads_with_sign = -t1.overheads_with_sign

        t2.account_position = trn.account_position
        t2.account_cash = trn.account_position
        t2.strategy1_position = trn.strategy1_position
        t2.strategy1_cash = trn.strategy1_position
        t2.strategy2_position = trn.strategy2_position
        t2.strategy2_cash = trn.strategy2_position
        t2.strategy3_position = trn.strategy3_position
        t2.strategy3_cash = trn.strategy3_position

        return t1, t2

    def _trn_fx_transfer_clone(self, trn):
        # t1
        t1 = self._clone(trn)
        t1.transaction_class = self._trn_cls_cash_out

        t1.position_size_with_sign = -trn.position_size_with_sign
        t1.cash_consideration = -trn.cash_consideration
        t1.principal_with_sign = -trn.principal_with_sign
        t1.carry_with_sign = -trn.carry_with_sign
        t1.overheads_with_sign = -trn.overheads_with_sign

        t1.account_position = trn.account_cash
        t1.account_cash = trn.account_cash
        t1.strategy1_position = trn.strategy1_cash
        t1.strategy1_cash = trn.strategy1_cash
        t1.strategy2_position = trn.strategy2_cash
        t1.strategy2_cash = trn.strategy2_cash
        t1.strategy3_position = trn.strategy3_cash
        t1.strategy3_cash = trn.strategy3_cash

        # t2
        t2 = self._clone(trn)
        t2.transaction_class = self._trn_cls_cash_in

        t2.position_size_with_sign = -trn.position_size_with_sign
        t2.cash_consideration = trn.cash_consideration
        t2.principal_with_sign = trn.principal_with_sign
        t2.carry_with_sign = trn.carry_with_sign
        t2.overheads_with_sign = trn.overheads_with_sign

        t2.account_position = trn.account_position
        t2.account_cash = trn.account_position
        t2.strategy1_position = trn.strategy1_position
        t2.strategy1_cash = trn.strategy1_position
        t2.strategy2_position = trn.strategy2_position
        t2.strategy2_cash = trn.strategy2_position
        t2.strategy3_position = trn.strategy3_position
        t2.strategy3_cash = trn.strategy3_position

        return t1, t2

    def _trn_fx_trade_clone(self, trn):
        # always used *_cash for groupping!
        # t1
        t1 = self._clone(trn)
        t1.transaction_currency = trn.transaction_currency
        t1.settlement_currency = trn.transaction_currency
        t1.cash_consideration = trn.position_size_with_sign
        t1.principal_with_sign = trn.position_size_with_sign
        t1.carry_with_sign = 0.0
        t1.overheads_with_sign = 0.0
        t1.reference_fx_rate = 1.0
        t1.account_cash = trn.account_position
        t1.strategy1_cash = trn.strategy1_position
        t1.strategy2_cash = trn.strategy2_position
        t1.strategy3_cash = trn.strategy3_position

        # t2
        t2 = self._clone(trn)
        t2.transaction_currency = trn.transaction_currency
        t2.settlement_currency = trn.settlement_currency
        t2.position_size_with_sign = trn.principal_with_sign
        try:
            t2.reference_fx_rate = abs(trn.position_size_with_sign / trn.principal_with_sign)
        except ArithmeticError:
            t2.reference_fx_rate = 0.0

        return t1, t2

    def _process_periods(self):
        _l.debug('> process periods')

        context = self.instance.context.copy()
        context['date_group_with_dates'] = True

        for trn in self._transactions:
            try:
                period = formula.safe_eval(self.instance.periods, names={'transaction': trn}, context=context)
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
            # _l.debug('period: %s -> %s', trn, (name, begin, end))

            if name is None:
                name = ''
            if begin is None:
                begin = date.min
            if end is None:
                end = date.min

            trn.period_name = name
            trn.period_begin = begin
            trn.period_end = end

        _l.debug('< process periods')

    @cached_property
    def _instruments(self):
        assert self._transactions is not None
        # return [t.instrument for t in self._transactions]
        # instruments = {t.instrument_id: t.instrument for t in self._transactions if t.instrument is not None}
        instruments = {}
        for trn in self._transactions:
            if trn.instrument:
                instruments[trn.instrument.id] = trn.instrument
        return list(instruments.values())

    @cached_property
    def _currencies(self):
        assert self._transactions is not None
        # return [t.settlement_currency for t in self._transactions]
        # currencies = {t.settlement_currency_id: t.settlement_currency for t in self._transactions}
        # currencies[self.instance.report_currency.id] = self.instance.report_currency
        currencies = {self.instance.report_currency.id: self.instance.report_currency}
        for trn in self._transactions:
            if trn.transaction_currency:
                currencies[trn.transaction_currency.id] = trn.transaction_currency
            currencies[trn.settlement_currency.id] = trn.settlement_currency
        return list(currencies.values())

    @cached_property
    def _dates(self):
        assert self._transactions is not None
        # return [t.period_end for t in self._transactions if t.period_end != date.min]
        dates = {t.period_end for t in self._transactions if t.period_end != date.min}
        return dates

    @property
    def pricing_provider(self):
        if self._pricing_provider is None:
            if self.instance.pricing_policy is None:
                p = FakeInstrumentPricingProvider(self.instance.master_user, None, None)
            else:
                p = InstrumentPricingProvider(self.instance.master_user, self.instance.pricing_policy, None)
                p.fill_using_instruments_and_dates(instruments=self._instruments, dates=self._dates)
            self._pricing_provider = p
        return self._pricing_provider

    @property
    def fx_rate_provider(self):
        if self._fx_rate_provider is None:
            if self.instance.pricing_policy is None:
                p = FakeCurrencyFxRateProvider(self.instance.master_user, None, None)
            else:
                p = CurrencyFxRateProvider(self.instance.master_user, self.instance.pricing_policy, None)
                p.fill_using_currencies_and_dates(currencies=self._currencies, dates=self._dates)
            self._fx_rate_provider = p
        return self._fx_rate_provider

    # def _fill_prices(self):
    #     _l.debug('> fill prices')
    #
    #     for trn in self._transactions:
    #         trn.report_currency = self.instance.report_currency
    #         trn.report_currency_history = self.fx_rate_provider[trn.report_currency, trn.period_end]
    #         trn.report_currency_fx_rate = trn.report_currency_history.fx_rate
    #
    #         if trn.instrument:
    #             trn.instrument_price = self.pricing_provider[trn.instrument, trn.period_end]
    #             trn.instrument_principal_price = trn.instrument_price.principal_price
    #             trn.instrument_accrued_price = trn.instrument_price.accrued_price
    #
    #             trn.instrument_pricing_currency_history = self.fx_rate_provider[
    #                 trn.instrument.pricing_currency, trn.period_end]
    #             trn.instrument_pricing_ccy_cur_fx_rate = trn.instrument_pricing_currency_history.fx_rate
    #
    #             trn.instrument_accrued_currency_history = self.fx_rate_provider[
    #                 trn.instrument.accrued_currency, trn.period_end]
    #             trn.instrument_accrued_currency_fx_rate = trn.instrument_accrued_currency_history.fx_rate
    #         else:
    #             trn.instrument_price = None
    #             trn.instrument_principal_price = 0
    #             trn.instrument_accrued_price = 0
    #
    #             trn.instrument_pricing_currency_history = None
    #             trn.instrument_pricing_ccy_cur_fx_rate = 0
    #
    #             trn.instrument_accrued_currency_history = None
    #             trn.instrument_accrued_currency_fx_rate = 0
    #
    #         trn.settlement_currency_history = self.fx_rate_provider[trn.settlement_currency, trn.period_end]
    #         trn.settlement_currency_fx_rate = trn.settlement_currency_history.fx_rate
    #
    #     _l.debug('< fill prices')

    def _get_key(self, period_begin=None, period_end=None, period_name=None,
                 portfolio=None, account=None, strategy1=None, strategy2=None, strategy3=None):
        if self.instance.portfolio_mode == PerformanceReport.MODE_IGNORE:
            portfolio = getattr(portfolio, 'id', None)
        elif self.instance.portfolio_mode == PerformanceReport.MODE_INDEPENDENT:
            pass
        elif self.instance.portfolio_mode == PerformanceReport.MODE_INTERDEPENDENT:
            pass

        if self.instance.account_mode == PerformanceReport.MODE_IGNORE:
            account = getattr(account, 'id', None)
        elif self.instance.account_mode == PerformanceReport.MODE_INDEPENDENT:
            pass
        elif self.instance.account_mode == PerformanceReport.MODE_INTERDEPENDENT:
            pass

        if self.instance.strategy1_mode == PerformanceReport.MODE_IGNORE:
            strategy1 = getattr(strategy1, 'id', None)
        elif self.instance.strategy1_mode == PerformanceReport.MODE_INDEPENDENT:
            pass
        elif self.instance.strategy1_mode == PerformanceReport.MODE_INTERDEPENDENT:
            pass

        if self.instance.strategy2_mode == PerformanceReport.MODE_IGNORE:
            strategy2 = getattr(strategy2, 'id', None)
        elif self.instance.strategy2_mode == PerformanceReport.MODE_INDEPENDENT:
            pass
        elif self.instance.strategy2_mode == PerformanceReport.MODE_INTERDEPENDENT:
            pass

        if self.instance.strategy3_mode == PerformanceReport.MODE_IGNORE:
            strategy3 = getattr(strategy3, 'id', None)
        elif self.instance.strategy3_mode == PerformanceReport.MODE_INDEPENDENT:
            pass
        elif self.instance.strategy3_mode == PerformanceReport.MODE_INTERDEPENDENT:
            pass

        return (
            period_begin if period_begin is not None else date.min,
            period_end if period_end is not None else date.min,
            period_name if period_name is not None else '',
            portfolio if portfolio is not None else 0,
            account if portfolio is not None else 0,
            strategy1 if portfolio is not None else 0,
            strategy2 if portfolio is not None else 0,
            strategy3 if portfolio is not None else 0,
        )

    def _get_item(self, period_begin=None, period_end=None, period_name=None,
                  portfolio=None, account=None, strategy1=None, strategy2=None, strategy3=None):
        key = self._get_key(
            period_begin=period_begin,
            period_end=period_end,
            period_name=period_name,
            portfolio=portfolio,
            account=account,
            strategy1=strategy1,
            strategy2=strategy2,
            strategy3=strategy3
        )
        try:
            item = self._items[key]
            return item, False
        except KeyError:
            item = PerformanceReportItem(
                self.instance,
                id=key,
                period_begin=period_begin,
                period_end=period_end,
                period_name=period_name,
                portfolio=portfolio,
                account=account,
                strategy1=strategy1,
                strategy2=strategy2,
                strategy3=strategy3
            )
            self._items[key] = item
            return item, True

    def _get_mkt_value_item(self, period_begin=None, period_end=None, period_name=None,
                            portfolio=None, account=None, strategy1=None, strategy2=None, strategy3=None):
        key = self._get_key(
            period_begin=period_begin,
            period_end=period_end,
            period_name=period_name,
            portfolio=portfolio,
            account=account,
            strategy1=strategy1,
            strategy2=strategy2,
            strategy3=strategy3
        )
        try:
            item = self._mkt_values[key]
            return item, False
        except KeyError:
            item = PerformanceReportItem(
                self.instance,
                id=key,
                period_begin=period_begin,
                period_end=period_end,
                period_name=period_name,
                portfolio=portfolio,
                account=account,
                strategy1=strategy1,
                strategy2=strategy2,
                strategy3=strategy3
            )
            self._mkt_values[key] = item

            period_key = (
                period_begin,
                period_end,
                period_name,
            )
            self._mkt_values_by_period[period_key].add(item)

            return item, True

    def _calc(self):
        _l.debug('> calc')

        periods = sorted({(x.period_begin, x.period_end, x.period_name) for x in self._transactions})

        prev_period_begin, prev_period_end, prev_period_name = None, None, None
        for period in periods:
            period_begin, period_end, period_name = period
            period_key = (period_begin, period_end, period_name,)

            self._periods.append(period_key)
            items_mkt_val = []

            for trn in self._transactions:
                # already ordered by accounting_date
                if trn.accounting_date > period_end:
                    break

                # load pricing and fx-rates

                report_currency = self.instance.report_currency
                report_currency_history = self.fx_rate_provider[report_currency, period_end]
                report_currency_fx_rate = report_currency_history.fx_rate

                try:
                    sys_to_rep_rate = 1.0 / report_currency_fx_rate
                except ArithmeticError:
                    sys_to_rep_rate = 0.0

                if trn.instrument:
                    instrument_price = self.pricing_provider[trn.instrument, period_end]
                    instrument_principal_price = instrument_price.principal_price
                    instrument_accrued_price = instrument_price.accrued_price

                    instrument_pricing_currency_history = self.fx_rate_provider[
                        trn.instrument.pricing_currency, period_end]
                    instrument_pricing_ccy_cur_fx_rate = instrument_pricing_currency_history.fx_rate

                    instrument_accrued_currency_history = self.fx_rate_provider[
                        trn.instrument.accrued_currency, period_end]
                    instrument_accrued_currency_fx_rate = instrument_accrued_currency_history.fx_rate
                else:
                    instrument_price = None
                    instrument_principal_price = 0
                    instrument_accrued_price = 0

                    instrument_pricing_currency_history = None
                    instrument_pricing_ccy_cur_fx_rate = 0

                    instrument_accrued_currency_history = None
                    instrument_accrued_currency_fx_rate = 0

                settlement_currency_history = self.fx_rate_provider[trn.settlement_currency, period_end]
                settlement_currency_fx_rate = settlement_currency_history.fx_rate

                # -------------------------------------

                cash_consideration_sys = trn.cash_consideration * settlement_currency_fx_rate
                principal_with_sign_sys = trn.principal_with_sign * settlement_currency_fx_rate
                carry_with_sign_sys = trn.carry_with_sign * settlement_currency_fx_rate
                overheads_with_sign_sys = trn.overheads_with_sign * settlement_currency_fx_rate

                instrument_principal_sys = 0
                instrument_accrued_sys = 0
                # market_value_sys = 0

                if trn.is_buy or trn.is_sell or trn.is_instrument_pl:
                    instrument_principal_sys = trn.position_size_with_sign * trn.instrument.price_multiplier * instrument_principal_price * instrument_pricing_ccy_cur_fx_rate
                    instrument_accrued_sys = trn.position_size_with_sign * trn.instrument.accrued_multiplier * instrument_accrued_price * instrument_accrued_currency_fx_rate

                    # market_value_sys = instrument_principal_sys + instrument_accrued_sys

                elif trn.is_fx_trade:
                    # market_value_sys = trn.position_size_with_sign * settlement_currency_fx_rate
                    pass

                elif trn.is_transaction_pl:
                    # market_value_sys = cash_consideration_sys
                    pass

                elif trn.is_cash_inflow or trn.is_cash_outflow:
                    # market_value_sys = cash_consideration_sys
                    pass

                else:
                    _l.warn('Unknown transaction class: id=%s, transaction_class=%s', trn.id, trn.transaction_class)
                    continue

                # cash_consideration_res = cash_consideration_sys * sys_to_rep_rate
                principal_with_sign_res = principal_with_sign_sys * sys_to_rep_rate
                carry_with_sign_res = carry_with_sign_sys * sys_to_rep_rate
                overheads_with_sign_res = overheads_with_sign_sys * sys_to_rep_rate

                total_with_sign_sys = principal_with_sign_sys + carry_with_sign_sys + overheads_with_sign_sys
                total_with_sign_res = principal_with_sign_res + carry_with_sign_res + overheads_with_sign_res

                instrument_principal_res = instrument_principal_sys * sys_to_rep_rate
                instrument_accrued_res = instrument_accrued_sys * sys_to_rep_rate

                # market_value_res = market_value_sys * sys_to_rep_rate

                global_time_weight = (self.instance.end_date - trn.accounting_date).days / \
                                     (self.instance.end_date - self.instance.begin_date).days
                period_time_weight = (period_end - trn.accounting_date).days / \
                                     (period_end - period_begin).days

                cash_flow_cash_sys = total_with_sign_sys
                cash_flow_pos_sys = -total_with_sign_sys

                cash_flow_cash_res = total_with_sign_res
                cash_flow_pos_res = -total_with_sign_res

                time_weight_cash_flow_cash_sys = cash_flow_cash_sys * period_time_weight
                time_weight_cash_flow_pos_sys = cash_flow_pos_sys * period_time_weight

                time_weight_cash_flow_cash_res = cash_flow_cash_res * period_time_weight
                time_weight_cash_flow_pos_res = cash_flow_pos_res * period_time_weight

                # mkt_val
                item_mkt_val, item_mkt_val_created = self._get_mkt_value_item(
                    period_begin=period_begin,
                    period_end=period_end,
                    period_name=period_name,
                    portfolio=trn.portfolio,
                    account=trn.account_pos,
                    strategy1=trn.strategy1_pos,
                    strategy2=trn.strategy2_pos,
                    strategy3=trn.strategy3_pos
                )
                item_mkt_val.principal_res += principal_with_sign_res + instrument_principal_res
                item_mkt_val.carry_res += carry_with_sign_res + instrument_accrued_res
                item_mkt_val.overheads_res += overheads_with_sign_res
                item_mkt_val.total_res += (principal_with_sign_res + instrument_principal_res) + \
                                          (carry_with_sign_res + instrument_accrued_res) + \
                                          overheads_with_sign_res
                if item_mkt_val_created:
                    items_mkt_val.append(item_mkt_val)

                # 1
                item_cash, item_cash_created = self._get_item(
                    period_begin=period_begin,
                    period_end=period_end,
                    period_name=period_name,
                    portfolio=trn.portfolio,
                    account=trn.account_cash,
                    strategy1=trn.strategy1_cash,
                    strategy2=trn.strategy2_cash,
                    strategy3=trn.strategy3_cash
                )
                item_cash.cash_inflows += cash_flow_cash_res
                item_cash.cash_outflows += 0
                item_cash.time_weighted_cash_inflows += time_weight_cash_flow_cash_res
                item_cash.time_weighted_cash_outflows += 0

                # 2
                item_pos, item_pos_created = self._get_item(
                    period_begin=period_begin,
                    period_end=period_end,
                    period_name=period_name,
                    portfolio=trn.portfolio,
                    account=trn.account_position,
                    strategy1=trn.strategy1_position,
                    strategy2=trn.strategy2_position,
                    strategy3=trn.strategy3_position
                )
                item_pos.cash_inflows += cash_flow_pos_res
                item_pos.cash_outflows += 0
                item_pos.time_weighted_cash_inflows += time_weight_cash_flow_pos_res
                item_pos.time_weighted_cash_outflows += 0

            # process market value rows
            for item_mkt_val in items_mkt_val:
                global_time_weight = (self.instance.end_date - item_mkt_val.period_end).days / \
                                     (self.instance.end_date - self.instance.begin_date).days

            prev_period_begin, prev_period_end, prev_period_name = period_begin, period_end, period_name

        _l.debug('< calc')

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
