import logging
import time

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

    def build(self):
        st = time.perf_counter()
        _l.debug('build transaction')

        with transaction.atomic():
            try:
                self._load()
                self._clone_transactions_if_need()
                self._process_periods()
                self._fill_prices()
                self._calc()

                self.instance.items = [
                    PerformanceReportItem(
                        self.instance,
                        id=x,
                        period_name='P%s' % (x // 10),
                        period_begin=date_now() + timedelta(days=x // 10),
                        period_end=date_now() + timedelta(days=(x + 1) // 10 - 1),
                        portfolio=self.instance.master_user.portfolio,
                        account=self.instance.master_user.account,
                        strategy1=self.instance.master_user.strategy1,
                        strategy2=self.instance.master_user.strategy2,
                        strategy3=self.instance.master_user.strategy3,
                    )
                    for x in range(0, 200)]

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
            trn.period_key = name, begin, end

        self._transactions.sort(key=lambda x: x.period_key)

        _l.debug('< process periods')

    @cached_property
    def _instruments(self):
        assert self._transactions is not None
        # return [t.instrument for t in self._transactions]
        instruments = {t.instrument_id: t.instrument for t in self._transactions if t.instrument is not None}
        return list(instruments.values())

    @cached_property
    def _currencies(self):
        assert self._transactions is not None
        # return [t.settlement_currency for t in self._transactions]
        currencies = {t.settlement_currency_id: t.settlement_currency for t in self._transactions}
        currencies[self.instance.report_currency.id] = self.instance.report_currency
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

    def _fill_prices(self):
        _l.debug('> fill prices')

        for t in self._transactions:
            t.report_currency = self.instance.report_currency
            t.report_currency_history = self.fx_rate_provider[t.report_currency, t.period_end]
            t.report_currency_fx_rate = t.report_currency_history.fx_rate

            if t.instrument:
                t.instrument_price = self.pricing_provider[t.instrument, t.period_end]
                t.instrument_principal_price = t.instrument_price.principal_price
                t.instrument_accrued_price = t.instrument_price.accrued_price

                t.instrument_pricing_currency_history = self.fx_rate_provider[
                    t.instrument.pricing_currency, t.period_end]
                t.instrument_pricing_ccy_cur_fx_rate = t.instrument_pricing_currency_history.fx_rate

                t.instrument_accrued_currency_history = self.fx_rate_provider[
                    t.instrument.accrued_currency, t.period_end]
                t.instrument_accrued_currency_fx_rate = t.instrument_accrued_currency_history.fx_rate
            else:
                t.instrument_price = None
                t.instrument_principal_price = 0
                t.instrument_accrued_price = 0

                t.instrument_pricing_currency_history = None
                t.instrument_pricing_ccy_cur_fx_rate = 0

                t.instrument_accrued_currency_history = None
                t.instrument_accrued_currency_fx_rate = 0

            t.settlement_currency_history = self.fx_rate_provider[t.settlement_currency, t.period_end]
            t.settlement_currency_fx_rate = t.settlement_currency_history.fx_rate

        _l.debug('< fill prices')

    def _calc(self):
        _l.debug('> calc')

        for t in self._transactions:
            t.cash_consideration_sys = t.cash_consideration * t.settlement_currency_fx_rate

            t.principal_with_sign_sys = t.principal_with_sign * t.settlement_currency_fx_rate
            t.carry_with_sign_sys = t.carry_with_sign * t.settlement_currency_fx_rate
            t.overheads_with_sign_sys = t.overheads_with_sign * t.settlement_currency_fx_rate

            if t.is_buy or t.is_sell or t.is_instrument_pl:
                pass

            elif t.is_fx_trade:
                pass

            elif t.is_transaction_pl:
                pass

            elif t.is_cash_inflow or t.is_cash_outflow:
                pass

            else:
                raise RuntimeError('code bug')

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
