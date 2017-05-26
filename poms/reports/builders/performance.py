import logging
import time

from django.db import transaction
from django.db.models import Q

from poms.accounts.models import Account
from poms.accounts.models import AccountType
from poms.counterparties.models import Responsible, ResponsibleGroup, Counterparty, CounterpartyGroup
from poms.instruments.models import Instrument, InstrumentType
from poms.obj_perms.utils import get_permissions_prefetch_lookups
from poms.portfolios.models import Portfolio
from poms.reports.builders.base_builder import BaseReportBuilder
from poms.reports.builders.performance_item import PerformanceReportItem
from poms.strategies.models import Strategy1, Strategy1Subgroup, Strategy1Group, Strategy2, Strategy2Subgroup, \
    Strategy2Group, Strategy3, Strategy3Subgroup, Strategy3Group
from poms.transactions.models import Transaction, ComplexTransaction, TransactionType

_l = logging.getLogger('poms.reports')


class PerformanceReportBuilder(BaseReportBuilder):
    def __init__(self, instance):
        super(PerformanceReportBuilder, self).__init__(instance)

        self._transactions = []

    def build(self):
        st = time.perf_counter()
        _l.debug('build transaction')

        with transaction.atomic():
            try:
                self._load()

                self._clone_transactions_if_need()

                self.instance.items = [
                    PerformanceReportItem(
                        self.instance,
                        portfolio=self.instance.master_user.portfolio,
                        account=self.instance.master_user.account,
                        strategy1=self.instance.master_user.strategy1,
                        strategy2=self.instance.master_user.strategy2,
                        strategy3=self.instance.master_user.strategy3,
                    )
                ]

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

        qs = self._trn_qs()
        self._transactions = list(qs)

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
        t2.trn_cls = self._trn_cls_cash_in

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

    def _refresh_from_db(self):
        _l.info('> _refresh_from_db')

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

        _l.info('< _refresh_from_db')
