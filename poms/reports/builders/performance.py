import time
import logging

from django.db import transaction
from django.db.models import Q

from poms.reports.builders.base_builder import BaseReportBuilder
from poms.reports.builders.performance_item import PerformanceReportItem
from poms.transactions.models import Transaction, ComplexTransaction

_l = logging.getLogger('poms.reports')


class PerformanceReportBuilder(BaseReportBuilder):
    def __init__(self, instance):
        self.instance = instance

        self._transactions = []

    def build(self):
        st = time.perf_counter()
        _l.debug('build transaction')

        with transaction.atomic():
            try:
                self._load()

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

                # self.instance.item_portfolios = [self.instance.master_user.portfolio, ]
                # self.instance.item_accounts = [self.instance.master_user.account, ]
                # self.instance.item_strategies1 = [self.instance.master_user.strategy1, ]
                # self.instance.item_strategies2 = [self.instance.master_user.strategy2, ]
                # self.instance.item_strategies3 = [self.instance.master_user.strategy3, ]
            finally:
                transaction.set_rollback(True)

        _l.debug('done: %s', (time.perf_counter() - st))
        return self.instance

    def _trn_qs(self):
        from poms.obj_attrs.utils import get_attributes_prefetch

        qs = Transaction.objects.prefetch_related(
            'complex_transaction',
            'transaction_class',
            'instrument',
            'transaction_currency',
            'settlement_currency',
            'portfolio',
            'account_position',
            'account_cash',
            'account_interim',
            'strategy1_position',
            'strategy1_cash',
            'strategy2_position',
            'strategy2_cash',
            'strategy3_position',
            'strategy3_cash',
            'responsible',
            'counterparty',
            'linked_instrument',
            'allocation_balance',
            'allocation_pl',
            get_attributes_prefetch(),
            get_attributes_prefetch('complex_transaction__attributes'),
            get_attributes_prefetch('instrument__attributes'),
            get_attributes_prefetch('transaction_currency__attributes'),
            get_attributes_prefetch('settlement_currency__attributes'),
            get_attributes_prefetch('portfolio__attributes'),
            get_attributes_prefetch('account_position__attributes'),
            get_attributes_prefetch('account_cash__attributes'),
            get_attributes_prefetch('account_interim__attributes'),
            get_attributes_prefetch('responsible__attributes'),
            get_attributes_prefetch('counterparty__attributes'),
            get_attributes_prefetch('linked_instrument__attributes'),
            get_attributes_prefetch('allocation_balance__attributes'),
            get_attributes_prefetch('allocation_pl__attributes'),
        )

        a_filters = [
            Q(complex_transaction__isnull=True) | Q(complex_transaction__status=ComplexTransaction.PRODUCTION,
                                                    complex_transaction__is_deleted=False)
        ]
        kw_filters = {
            'master_user': self.instance.master_user,
            'is_deleted': False,
        }

        if self.instance.begin_date:
            kw_filters['accounting_date__gte'] = self.instance.begin_date

        if self.instance.end_date:
            kw_filters['accounting_date__lte'] = self.instance.end_date

        if self.instance.portfolios:
            kw_filters['portfolio__in'] = self.instance.portfolios

        if self.instance.accounts:
            kw_filters['account_position__in'] = self.instance.accounts
            kw_filters['account_cash__in'] = self.instance.accounts
            kw_filters['account_interim__in'] = self.instance.accounts

        if self.instance.accounts_position:
            kw_filters['account_position__in'] = self.instance.accounts_position

        if self.instance.accounts_cash:
            kw_filters['account_cash__in'] = self.instance.accounts_cash

        if self.instance.strategies1:
            kw_filters['strategy1_position__in'] = self.instance.strategies1
            kw_filters['strategy1_cash__in'] = self.instance.strategies1

        if self.instance.strategies2:
            kw_filters['strategy2_position__in'] = self.instance.strategies2
            kw_filters['strategy2_cash__in'] = self.instance.strategies2

        if self.instance.strategies3:
            kw_filters['strategy3_position__in'] = self.instance.strategies3
            kw_filters['strategy3_cash__in'] = self.instance.strategies3

        qs = qs.filter(*a_filters, **kw_filters)

        qs = qs.order_by('accounting_date', 'transaction_code')

        from poms.transactions.filters import TransactionObjectPermissionFilter
        qs = TransactionObjectPermissionFilter.filter_qs(qs, self.instance.master_user, self.instance.member)

        return qs

    def _load(self):
        _l.debug('> _load')

        qs = self._trn_qs()
        self._transactions = list(qs)

        _l.debug('< _load: %s', len(self._transactions))

    def _refresh_from_db(self):
        _l.info('> _refresh_from_db')

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