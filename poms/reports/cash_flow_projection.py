import logging
from collections import Counter
from datetime import timedelta

from django.db import transaction
from rest_framework.renderers import JSONRenderer

from poms.accounts.models import Account
from poms.counterparties.models import Counterparty
from poms.counterparties.models import Responsible
from poms.currencies.models import Currency
from poms.instruments.models import Instrument
from poms.portfolios.models import Portfolio
from poms.strategies.models import Strategy1, Strategy2, Strategy3
from poms.transactions.models import Transaction, ComplexTransaction, TransactionType, TransactionClass

_l = logging.getLogger('poms.reports')


class TransactionReport:
    def __init__(self, id=None, task_id=None, task_status=None, master_user=None, member=None, transactions=None):
        self.id = id
        self.task_id = task_id
        self.task_status = task_status
        self.master_user = master_user
        self.member = member
        self.transactions = transactions

        self.complex_transactions = []
        self.transaction_types = []
        self.transaction_classes = []
        self.instruments = []
        self.currencies = []
        self.portfolios = []
        self.accounts = []
        self.strategies1 = []
        self.strategies2 = []
        self.strategies3 = []
        self.responsibles = []
        self.counterparties = []

    def __str__(self):
        return ''

    def build(self):
        complex_transactions = {}
        transaction_types = {}
        transaction_classes = {}
        instruments = {}
        currencies = {}
        portfolios = {}
        accounts = {}
        strategies1 = {}
        strategies2 = {}
        strategies3 = {}
        responsibles = {}
        counterparties = {}

        for t in self.transactions:
            if t.complex_transaction:
                complex_transactions[t.complex_transaction.id] = t.complex_transaction

                if t.complex_transaction.transaction_type:
                    transaction_types[
                        t.complex_transaction.transaction_type.id] = t.complex_transaction.transaction_type

            if t.transaction_class:
                transaction_classes[t.transaction_class.id] = t.transaction_class

            if t.instrument:
                instruments[t.instrument.id] = t.instrument

            if t.transaction_currency:
                currencies[t.transaction_currency.id] = t.transaction_currency

            if t.settlement_currency:
                currencies[t.settlement_currency.id] = t.settlement_currency

            if t.portfolio:
                portfolios[t.portfolio.id] = t.portfolio

            if t.account_position:
                accounts[t.account_position.id] = t.account_position

            if t.account_cash:
                accounts[t.account_cash.id] = t.account_cash

            if t.strategy1_position:
                strategies1[t.strategy1_position.id] = t.strategy1_position

            if t.strategy1_cash:
                strategies1[t.strategy1_cash.id] = t.strategy1_cash

            if t.strategy2_position:
                strategies2[t.strategy2_position.id] = t.strategy2_position

            if t.strategy2_cash:
                strategies2[t.strategy2_cash.id] = t.strategy2_cash

            if t.strategy3_position:
                strategies3[t.strategy3_position.id] = t.strategy3_position

            if t.strategy3_cash:
                strategies3[t.strategy3_cash.id] = t.strategy3_cash

            if t.responsible:
                responsibles[t.responsible.id] = t.responsible

            if t.counterparty:
                counterparties[t.counterparty.id] = t.counterparty

            if t.linked_instrument:
                instruments[t.linked_instrument.id] = t.linked_instrument

            if t.allocation_balance:
                instruments[t.allocation_balance.id] = t.allocation_balance

            if t.allocation_pl:
                instruments[t.allocation_pl.id] = t.allocation_pl

        self.complex_transactions = list(complex_transactions.values())
        self.transaction_types = list(transaction_types.values())
        self.transaction_classes = list(transaction_classes.values())
        self.instruments = list(instruments.values())
        self.currencies = list(currencies.values())
        self.portfolios = list(portfolios.values())
        self.accounts = list(accounts.values())
        self.strategies1 = list(strategies1.values())
        self.strategies2 = list(strategies2.values())
        self.strategies3 = list(strategies3.values())
        self.responsibles = list(responsibles.values())
        self.counterparties = list(counterparties.values())


class TransactionReportBuilder:
    def __init__(self, instance=None):
        self.instance = instance

    def _get_queryset(self):
        from poms.transactions.views import get_transaction_queryset
        qs = get_transaction_queryset(select_related=False, complex_transaction_transactions=True).order_by(
            'complex_transaction__date', 'complex_transaction__code', 'transaction_code'
        )
        return qs

    def _get_transactions(self):
        transactions = [t for t in self._get_queryset()]

        # def _transaction_key(item):
        #     return (
        #         getattr(item.complex_transaction, 'date', date.min),
        #         getattr(item.complex_transaction, 'code', -1),
        #         item.transaction_code,
        #     )
        #
        # return sorted(transactions, key=_transaction_key)

        return transactions

    def build(self):
        with transaction.atomic():
            _l.info('> _make_transactions')
            # self._make_transactions(1000)
            _l.info('< _make_transactions')

            _l.info('> _get_transactions')
            self.instance.transactions = self._get_transactions()
            _l.info('< _get_transactions: %s', len(self.instance.transactions))

            _l.info('> _process')
            self._process()
            _l.info('< _process')

            _l.info('> instance.build')
            self.instance.build()
            _l.info('< instance.build')

            # _l.info('3' * 79)
            # import pickle
            # data = pickle.dumps(self.instance, protocol=pickle.HIGHEST_PROTOCOL)
            # print(len(data))
            #
            # _l.info('3' * 79)
            # import zlib
            # data1 = zlib.compress(data)
            # print(len(data1))

            # _l.info('> TransactionReportSerializer.data')
            # from poms.reports.serializers import TransactionReportSerializer
            # s = TransactionReportSerializer(instance=self.instance, context={
            #     'master_user': self.instance.master_user,
            #     'member': self.instance.member,
            # })
            # data_dict = s.data
            # _l.info('< TransactionReportSerializer.data')
            #
            # _l.info('> JSONRenderer.render')
            # r = JSONRenderer()
            # data = r.render(data_dict)
            # _l.info('< JSONRenderer.render: %s', len(data))

            transaction.set_rollback(True)

        return self.instance

    def _process(self):
        pass

    def _make_transactions(self, count=100):
        from poms.common.utils import date_now

        tt = TransactionType.objects.filter(master_user=self.instance.master_user).first()
        tcls = TransactionClass.objects.get(pk=TransactionClass.BUY)
        instr1 = Instrument.objects.filter(master_user=self.instance.master_user).first()
        instr2 = Instrument.objects.filter(master_user=self.instance.master_user).last()
        ccy1 = Currency.objects.filter(master_user=self.instance.master_user).first()
        ccy2 = Currency.objects.filter(master_user=self.instance.master_user).last()
        p = Portfolio.objects.filter(master_user=self.instance.master_user).last()
        acc1 = Account.objects.filter(master_user=self.instance.master_user).first()
        acc2 = Account.objects.filter(master_user=self.instance.master_user).last()
        s11 = Strategy1.objects.filter(master_user=self.instance.master_user).last()
        s12 = Strategy1.objects.filter(master_user=self.instance.master_user).last()
        s21 = Strategy2.objects.filter(master_user=self.instance.master_user).last()
        s22 = Strategy2.objects.filter(master_user=self.instance.master_user).last()
        s31 = Strategy3.objects.filter(master_user=self.instance.master_user).last()
        s32 = Strategy3.objects.filter(master_user=self.instance.master_user).last()
        r = Responsible.objects.filter(master_user=self.instance.master_user).last()
        c = Counterparty.objects.filter(master_user=self.instance.master_user).last()

        ctrns = []
        trns = []

        for i in range(0, count):
            ct = ComplexTransaction(
                transaction_type=tt,
                date=date_now() + timedelta(days=i),
                status=ComplexTransaction.PRODUCTION,
                code=i
            )
            ctrns.append(ct)
            t = Transaction(
                master_user=self.instance.master_user,
                complex_transaction=ct,
                complex_transaction_order=1,
                transaction_code=1,
                transaction_class=tcls,
                instrument=instr1,
                transaction_currency=ccy1,
                position_size_with_sign=100,
                settlement_currency=ccy2,
                cash_consideration=-90,
                principal_with_sign=100,
                carry_with_sign=100,
                overheads_with_sign=100,
                transaction_date=date_now() + timedelta(days=i),
                accounting_date=date_now() + timedelta(days=i),
                cash_date=date_now() + timedelta(days=i),
                portfolio=p,
                account_position=acc1,
                account_cash=acc2,
                account_interim=acc2,
                strategy1_position=s11,
                strategy1_cash=s12,
                strategy2_position=s21,
                strategy2_cash=s22,
                strategy3_position=s31,
                strategy3_cash=s32,
                responsible=r,
                counterparty=c,
                linked_instrument=instr2,
                allocation_balance=instr1,
                allocation_pl=instr2,
            )
            trns.append(t)
        ComplexTransaction.objects.bulk_create(ctrns)
        Transaction.objects.bulk_create(trns)


class CashFlowProjectionReportBuilder(TransactionReportBuilder):
    def __init__(self, instance=None):
        super(CashFlowProjectionReportBuilder, self).__init__(instance)

    def build(self):
        return super(CashFlowProjectionReportBuilder, self).build()

    def _process(self):
        trns = self.instance.transactions

        instrs_pos = Counter()

        def _instr_pos_key(t):
            return (
                getattr(t.instrument, 'id', -1),
            )

        for t in trns:
            if t.instrument:
                pos_key = _instr_pos_key(t)

                before_pos = instrs_pos[pos_key]
                after_pos = before_pos + t.position_size_with_sign
                instrs_pos[pos_key] += after_pos

                if after_pos > 0:
                    self._check_events(t)

    def _check_events(self, t):
        pass
