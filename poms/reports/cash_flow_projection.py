import logging
import random
import sys
import datetime

from django.db import transaction

from poms.accounts.models import Account, AccountType
from poms.counterparties.models import Counterparty, ResponsibleGroup, CounterpartyGroup
from poms.counterparties.models import Responsible
from poms.currencies.models import Currency
from poms.instruments.models import Instrument, InstrumentType
from poms.portfolios.models import Portfolio
from poms.strategies.models import Strategy1, Strategy2, Strategy3, Strategy1Subgroup, Strategy1Group, \
    Strategy2Subgroup, \
    Strategy2Group, Strategy3Subgroup, Strategy3Group
from poms.transactions.models import Transaction, ComplexTransaction, TransactionType, TransactionClass, \
    TransactionTypeGroup

_l = logging.getLogger('poms.reports')


class TransactionReportItem:
    def __init__(self, trn=None, id=None, complex_transaction=None, complex_transaction_order=None,
                 transaction_code=None, transaction_class=None, instrument=None, transaction_currency=None,
                 position_size_with_sign=None, settlement_currency=None, cash_consideration=None,
                 principal_with_sign=None, carry_with_sign=None, overheads_with_sign=None, transaction_date=None,
                 accounting_date=None, cash_date=None, portfolio=None, account_position=None, account_cash=None,
                 account_interim=None, strategy1_position=None, strategy1_cash=None, strategy2_position=None,
                 strategy2_cash=None, strategy3_position=None, strategy3_cash=None, responsible=None, counterparty=None,
                 linked_instrument=None, allocation_balance=None, allocation_pl=None, reference_fx_rate=None,
                 attributes=None):
        self.id = id if id is not None else getattr(trn, 'id', None)
        self.complex_transaction = complex_transaction if complex_transaction is not None else \
            getattr(trn, 'complex_transaction', None)
        self.complex_transaction_order = complex_transaction_order if complex_transaction_order is not None else \
            getattr(trn, 'complex_transaction_order', None)
        self.transaction_code = transaction_code if transaction_code is not None else \
            getattr(trn, 'transaction_code', None)
        self.transaction_class = transaction_class if transaction_class is not None else \
            getattr(trn, 'transaction_class', None)
        self.instrument = instrument if instrument is not None else getattr(trn, 'instrument', None)
        self.transaction_currency = transaction_currency if transaction_currency is not None else \
            getattr(trn, 'transaction_currency', None)
        self.position_size_with_sign = position_size_with_sign if position_size_with_sign is not None else \
            getattr(trn, 'position_size_with_sign', None)
        self.settlement_currency = settlement_currency if settlement_currency is not None else \
            getattr(trn, 'settlement_currency', None)
        self.cash_consideration = cash_consideration if cash_consideration is not None else \
            getattr(trn, 'cash_consideration', None)
        self.principal_with_sign = principal_with_sign if principal_with_sign is not None else \
            getattr(trn, 'principal_with_sign', None)
        self.carry_with_sign = carry_with_sign if carry_with_sign is not None else \
            getattr(trn, 'carry_with_sign', None)
        self.overheads_with_sign = overheads_with_sign if overheads_with_sign is not None else \
            getattr(trn, 'overheads_with_sign', None)
        self.transaction_date = transaction_date if transaction_date is not None else \
            getattr(trn, 'transaction_date', None)
        self.accounting_date = accounting_date if accounting_date is not None else \
            getattr(trn, 'accounting_date', None)
        self.cash_date = cash_date if cash_date is not None else getattr(trn, 'cash_date', None)
        self.portfolio = portfolio if portfolio is not None else getattr(trn, 'portfolio', None)
        self.account_position = account_position if account_position is not None else \
            getattr(trn, 'account_position', None)
        self.account_cash = account_cash if account_cash is not None else getattr(trn, 'account_cash', None)
        self.account_interim = account_interim if account_interim is not None else \
            getattr(trn, 'account_interim', None)
        self.strategy1_position = strategy1_position if strategy1_position is not None else \
            getattr(trn, 'strategy1_position', None)
        self.strategy1_cash = strategy1_cash if strategy1_cash is not None else \
            getattr(trn, 'strategy1_cash', None)
        self.strategy2_position = strategy2_position if strategy2_position is not None else \
            getattr(trn, 'strategy2_position', None)
        self.strategy2_cash = strategy2_cash if strategy2_cash is not None else \
            getattr(trn, 'strategy2_cash', None)
        self.strategy3_position = strategy3_position if strategy3_position is not None else \
            getattr(trn, 'strategy3_position', None)
        self.strategy3_cash = strategy3_cash if strategy3_cash is not None else \
            getattr(trn, 'strategy3_cash', None)
        self.responsible = responsible if responsible is not None else getattr(trn, 'responsible', None)
        self.counterparty = counterparty if counterparty is not None else getattr(trn, 'counterparty', None)
        self.linked_instrument = linked_instrument if linked_instrument is not None else \
            getattr(trn, 'linked_instrument', None)
        self.allocation_balance = allocation_balance if allocation_balance is not None else \
            getattr(trn, 'allocation_balance', None)
        self.allocation_pl = allocation_pl if allocation_pl is not None else getattr(trn, 'allocation_pl', None)
        self.reference_fx_rate = reference_fx_rate if reference_fx_rate is not None else \
            getattr(trn, 'reference_fx_rate', None)
        self.attributes = attributes if attributes is not None else getattr(trn, 'attributes', None).all()


class TransactionReport:
    def __init__(self, id=None, task_id=None, task_status=None, master_user=None, member=None,
                 begin_date=None, end_date=None, items=None):
        self.id = id
        self.task_id = task_id
        self.task_status = task_status
        self.master_user = master_user
        self.member = member
        self.begin_date = begin_date
        self.end_date = end_date
        self.items = items
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


class TransactionReportBuilder:
    def __init__(self, instance=None):
        self.instance = instance
        self._transactions = []
        self._complex_transactions = {}
        self._transaction_types = {}
        self._transaction_classes = {}
        self._instruments = {}
        self._currencies = {}
        self._portfolios = {}
        self._accounts = {}
        self._strategies1 = {}
        self._strategies2 = {}
        self._strategies3 = {}
        self._responsibles = {}
        self._counterparties = {}

    def _load(self):
        from poms.obj_attrs.utils import get_attributes_prefetch
        from poms.obj_perms.utils import get_permissions_prefetch_lookups

        _l.debug('> _load')

        self._transactions = []
        self._complex_transactions = {}
        self._transaction_types = {}
        self._transaction_classes = {}
        self._instruments = {}
        self._currencies = {}
        self._portfolios = {}
        self._accounts = {}
        self._strategies1 = {}
        self._strategies2 = {}
        self._strategies3 = {}
        self._responsibles = {}
        self._counterparties = {}

        def _c(cache, obj, attr):
            attr_pk_name = '%s_id' % attr
            attr_pk = getattr(obj, attr_pk_name, None)
            if attr_pk is not None:
                cache[attr_pk] = None

        _l.debug('> transactions.qs')
        qs = Transaction.objects.prefetch_related(
            'complex_transaction',
            'instrument',
            get_attributes_prefetch(),
        ).order_by(
            'complex_transaction__date', 'complex_transaction__code', 'transaction_code'
        )
        begin_date = getattr(self.instance, 'begin_date', None)
        if begin_date:
            qs = qs.filter(complex_transaction__date__gte=begin_date)
        end_date = getattr(self.instance, 'end_date', None)
        if end_date:
            qs = qs.filter(complex_transaction__date__lte=end_date)
        self._transactions = list(qs)
        _l.debug('< transactions.qs: %s', len(self._transactions))

        _l.debug('> transactions.1')
        for t in self._transactions:
            _c(self._complex_transactions, t, 'complex_transaction')
            if t.complex_transaction:
                _c(self._transaction_types, t.complex_transaction, 'transaction_type')
            _c(self._transaction_classes, t, 'transaction_class')
            _c(self._instruments, t, 'instrument')
            if t.instrument:
                _c(self._currencies, t.instrument, 'pricing_currency')
                _c(self._currencies, t.instrument, 'accrued_currency')
            _c(self._currencies, t, 'transaction_currency')
            _c(self._currencies, t, 'settlement_currency')
            _c(self._portfolios, t, 'portfolio')
            _c(self._accounts, t, 'account_position')
            _c(self._accounts, t, 'account_cash')
            _c(self._accounts, t, 'account_interim')
            _c(self._strategies1, t, 'strategy1_position')
            _c(self._strategies1, t, 'strategy1_cash')
            _c(self._strategies2, t, 'strategy2_position')
            _c(self._strategies2, t, 'strategy2_cash')
            _c(self._strategies3, t, 'strategy3_position')
            _c(self._strategies3, t, 'strategy3_cash')
            _c(self._responsibles, t, 'responsible')
            _c(self._counterparties, t, 'counterparty')
            _c(self._instruments, t, 'linked_instrument')
            _c(self._instruments, t, 'allocation_balance')
            _c(self._instruments, t, 'allocation_pl')
        _l.debug('< transactions.1: %s', len(self._transactions))

        _l.debug('> transaction_classes')
        if self._transaction_classes:
            qs = TransactionClass.objects.filter(
                pk__in=self._transaction_classes.keys()
            )
            for o in qs:
                self._transaction_classes[o.id] = o
        _l.debug('< transaction_classes: %s', len(self._transaction_classes))

        _l.debug('> complex_transactions')
        if self._complex_transactions:
            qs = ComplexTransaction.objects.filter(
                transaction_type__master_user=self.instance.master_user,
                pk__in=self._complex_transactions.keys()
            ).prefetch_related(
            )
            for o in qs:
                o._fake_transactions = []
                self._complex_transactions[o.id] = o
        _l.debug('< complex_transactions: %s', len(self._complex_transactions))

        _l.debug('> transaction_types')
        if self._transaction_types:
            qs = TransactionType.objects.filter(
                master_user=self.instance.master_user,
                pk__in=self._transaction_types.keys()
            ).prefetch_related(
                'group',
                *get_permissions_prefetch_lookups(
                    (None, TransactionType),
                    ('group', TransactionTypeGroup),
                )
            )
            for o in qs:
                self._transaction_types[o.id] = o
        _l.debug('< transaction_types: %s', len(self._transaction_types))

        _l.debug('> instruments')
        if self._instruments:
            qs = Instrument.objects.filter(
                master_user=self.instance.master_user,
                pk__in=self._instruments.keys()
            ).prefetch_related(
                'instrument_type',
                'instrument_type__instrument_class',
                get_attributes_prefetch(),
                *get_permissions_prefetch_lookups(
                    (None, Instrument),
                    ('instrument_type', InstrumentType),
                )
            )
            for o in qs:
                self._instruments[o.id] = o
        _l.debug('< instruments: %s', len(self._instruments))

        _l.debug('> currencies')
        if self._currencies:
            qs = Currency.objects.filter(
                master_user=self.instance.master_user,
                pk__in=self._currencies.keys()
            ).prefetch_related(
                get_attributes_prefetch(),
            )
            for o in qs:
                self._currencies[o.id] = o
        _l.debug('< currencies: %s', len(self._currencies))

        _l.debug('> portfolios')
        if self._portfolios:
            qs = Portfolio.objects.filter(
                master_user=self.instance.master_user,
                pk__in=self._portfolios.keys()
            ).prefetch_related(
                get_attributes_prefetch(),
                *get_permissions_prefetch_lookups(
                    (None, Portfolio),
                )
            )
            for o in qs:
                self._portfolios[o.id] = o
        _l.debug('< portfolios: %s', len(self._portfolios))

        _l.debug('> accounts')
        if self._accounts:
            qs = Account.objects.filter(
                master_user=self.instance.master_user,
                pk__in=self._accounts.keys()
            ).prefetch_related(
                'type',
                get_attributes_prefetch(),
                *get_permissions_prefetch_lookups(
                    (None, Account),
                    ('type', AccountType),
                )
            )
            for o in qs:
                self._accounts[o.id] = o
        _l.debug('< accounts: %s', len(self._accounts))

        _l.debug('> strategies1')
        if self._strategies1:
            qs = Strategy1.objects.filter(
                master_user=self.instance.master_user,
                pk__in=self._strategies1.keys()
            ).prefetch_related(
                'subgroup',
                'subgroup__group',
                *get_permissions_prefetch_lookups(
                    (None, Strategy1),
                    ('subgroup', Strategy1Subgroup),
                    ('subgroup__group', Strategy1Group),
                )
            )
            for o in qs:
                self._strategies1[o.id] = o
        _l.debug('< strategies1: %s', len(self._strategies1))

        _l.debug('> strategies2')
        if self._strategies2:
            qs = Strategy2.objects.filter(
                master_user=self.instance.master_user,
                pk__in=self._strategies2.keys()
            ).prefetch_related(
                'subgroup',
                'subgroup__group',
                *get_permissions_prefetch_lookups(
                    (None, Strategy1),
                    ('subgroup', Strategy2Subgroup),
                    ('subgroup__group', Strategy2Group),
                )
            )
            for o in qs:
                self._strategies2[o.id] = o
        _l.debug('< strategies2: %s', len(self._strategies2))

        _l.debug('> strategies3')
        if self._strategies3:
            qs = Strategy3.objects.filter(
                master_user=self.instance.master_user,
                pk__in=self._strategies3.keys()
            ).prefetch_related(
                'subgroup',
                'subgroup__group',
                *get_permissions_prefetch_lookups(
                    (None, Strategy1),
                    ('subgroup', Strategy3Subgroup),
                    ('subgroup__group', Strategy3Group),
                )
            )
            for o in qs:
                self._strategies3[o.id] = o
        _l.debug('< strategies3: %s', len(self._strategies3))

        _l.debug('> responsibles')
        if self._responsibles:
            qs = Responsible.objects.filter(
                master_user=self.instance.master_user,
                pk__in=self._responsibles.keys()
            ).prefetch_related(
                'group',
                get_attributes_prefetch(),
                *get_permissions_prefetch_lookups(
                    (None, Responsible),
                    ('group', ResponsibleGroup),
                )
            )
            for o in qs:
                self._responsibles[o.id] = o
        _l.debug('< responsibles: %s', len(self._responsibles))

        _l.debug('> counterparties')
        if self._counterparties:
            qs = Counterparty.objects.filter(
                master_user=self.instance.master_user,
                pk__in=self._counterparties.keys()
            ).prefetch_related(
                'group',
                get_attributes_prefetch(),
                *get_permissions_prefetch_lookups(
                    (None, Counterparty),
                    ('group', CounterpartyGroup),
                )
            )
            for o in qs:
                self._counterparties[o.id] = o
        _l.debug('< counterparties: %s', len(self._counterparties))

        def _p(cache, obj, attr):
            attr_pk_name = '%s_id' % attr
            attr_pk = getattr(obj, attr_pk_name, None)
            if attr_pk is not None:
                setattr(obj, attr, cache[attr_pk])
                # obj = getattr(obj, attr, None)
                # if obj:
                #     pk = obj.id
                #     if pk in cache:
                #         setattr(obj, attr, cache[pk])
                #     else:
                #         cache[pk] = obj

        _l.debug('> transactions.2')
        for t in self._transactions:
            _p(self._complex_transactions, t, 'complex_transaction')
            if t.complex_transaction:
                _p(self._transaction_types, t.complex_transaction, 'transaction_type')
                t.complex_transaction._fake_transactions.append(t)
            _p(self._transaction_classes, t, 'transaction_class')
            _p(self._instruments, t, 'instrument')
            if t.instrument:
                _p(self._currencies, t.instrument, 'pricing_currency')
                _p(self._currencies, t.instrument, 'accrued_currency')
            _p(self._currencies, t, 'transaction_currency')
            _p(self._currencies, t, 'settlement_currency')
            _p(self._portfolios, t, 'portfolio')
            _p(self._accounts, t, 'account_position')
            _p(self._accounts, t, 'account_cash')
            _p(self._accounts, t, 'account_interim')
            _p(self._strategies1, t, 'strategy1_position')
            _p(self._strategies1, t, 'strategy1_cash')
            _p(self._strategies2, t, 'strategy2_position')
            _p(self._strategies2, t, 'strategy2_cash')
            _p(self._strategies3, t, 'strategy3_position')
            _p(self._strategies3, t, 'strategy3_cash')
            _p(self._responsibles, t, 'responsible')
            _p(self._counterparties, t, 'counterparty')
            _p(self._instruments, t, 'linked_instrument')
            _p(self._instruments, t, 'allocation_balance')
            _p(self._instruments, t, 'allocation_pl')
        _l.debug('< transactions.2: %s', len(self._transactions))

        _l.debug('< _load')

    def build(self):
        with transaction.atomic():
            _l.debug('> _make_transactions')
            # self._make_transactions(10000)
            _l.debug('< _make_transactions')

            self._load()

            self.instance.items = [TransactionReportItem(trn=t) for t in self._transactions]
            self.instance.complex_transactions = list(self._complex_transactions.values())
            self.instance.transaction_types = list(self._transaction_types.values())
            self.instance.transaction_classes = list(self._transaction_classes.values())
            self.instance.instruments = list(self._instruments.values())
            self.instance.currencies = list(self._currencies.values())
            self.instance.portfolios = list(self._portfolios.values())
            self.instance.accounts = list(self._accounts.values())
            self.instance.strategies1 = list(self._strategies1.values())
            self.instance.strategies2 = list(self._strategies2.values())
            self.instance.strategies3 = list(self._strategies3.values())
            self.instance.responsibles = list(self._responsibles.values())
            self.instance.counterparties = list(self._counterparties.values())

            # _l.debug('> pickle')
            # import pickle
            # data = pickle.dumps(self.instance, protocol=pickle.HIGHEST_PROTOCOL)
            # _l.debug('< pickle: %s', len(data))
            #
            # _l.debug('> zlib')
            # import zlib
            # data1 = zlib.compress(data)
            # _l.debug('< zlib: %s', len(data1))

            # _l.debug('> TransactionReportSerializer.data')
            # from poms.reports.serializers import TransactionReportSerializer
            # s = TransactionReportSerializer(instance=self.instance, context={
            #     'master_user': self.instance.master_user,
            #     'member': self.instance.member,
            # })
            # data_dict = s.data
            # _l.debug('< TransactionReportSerializer.data')
            #
            # _l.debug('> JSONRenderer.render')
            # r = JSONRenderer()
            # data = r.render(data_dict)
            # _l.debug('< JSONRenderer.render: %s', len(data))

            transaction.set_rollback(True)

        return self.instance

    def _make_transactions(self, count=100):
        from poms.common.utils import date_now

        tcls = TransactionClass.objects.get(pk=TransactionClass.BUY)

        tt = list(TransactionType.objects.filter(master_user=self.instance.master_user).all())
        instr = list(Instrument.objects.filter(master_user=self.instance.master_user).all())
        ccy = list(Currency.objects.filter(master_user=self.instance.master_user).all())
        p = list(Portfolio.objects.filter(master_user=self.instance.master_user).all())
        acc = list(Account.objects.filter(master_user=self.instance.master_user).all())
        s1 = list(Strategy1.objects.filter(master_user=self.instance.master_user).all())
        s2 = list(Strategy2.objects.filter(master_user=self.instance.master_user).all())
        s3 = list(Strategy3.objects.filter(master_user=self.instance.master_user).all())
        r = list(Responsible.objects.filter(master_user=self.instance.master_user).all())
        c = list(Counterparty.objects.filter(master_user=self.instance.master_user).all())

        ctrns = []
        trns = []

        for i in range(0, count):
            ct = ComplexTransaction(
                transaction_type=random.choice(tt),
                date=date_now() + datetime.timedelta(days=i),
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
                instrument=random.choice(instr),
                transaction_currency=random.choice(ccy),
                position_size_with_sign=100,
                settlement_currency=random.choice(ccy),
                cash_consideration=-90,
                principal_with_sign=100,
                carry_with_sign=100,
                overheads_with_sign=100,
                transaction_date=date_now() + datetime.timedelta(days=i),
                accounting_date=date_now() + datetime.timedelta(days=i),
                cash_date=date_now() + datetime.timedelta(days=i),
                portfolio=random.choice(p),
                account_position=random.choice(acc),
                account_cash=random.choice(acc),
                account_interim=random.choice(acc),
                strategy1_position=random.choice(s1),
                strategy1_cash=random.choice(s1),
                strategy2_position=random.choice(s2),
                strategy2_cash=random.choice(s2),
                strategy3_position=random.choice(s3),
                strategy3_cash=random.choice(s3),
                responsible=random.choice(r),
                counterparty=random.choice(c),
                linked_instrument=random.choice(instr),
                allocation_balance=random.choice(instr),
                allocation_pl=random.choice(instr),
            )
            trns.append(t)

        ComplexTransaction.objects.bulk_create(ctrns)
        Transaction.objects.bulk_create(trns)


class CashFlowProjectionReportItem:
    DEFAULT = 1
    BALANCE = 2
    TYPE_CHOICE = (
        (DEFAULT, 'Default'),
        (BALANCE, 'Balance'),
    )

    def __init__(self, type=DEFAULT, trn=None, date=None, portfolio=None, account=None, instrument=None,
                 currency=None, position_size_with_sign=0.0, position_size_with_sign_before=0.0,
                 position_size_with_sign_after=0.0, cash_consideration=0.0, cash_consideration_before=0.0,
                 cash_consideration_after=0.0):
        self.type = type
        self.date = date if date is not None else getattr(trn.complex_transaction, 'date', datetime.date.min)
        self.portfolio = portfolio if portfolio is not None else getattr(trn, 'portfolio', None)
        self.account = account if portfolio is not None else getattr(trn, 'account_position', None)
        self.instrument = instrument if portfolio is not None else getattr(trn, 'instrument', None)
        self.currency = currency if portfolio is not None else getattr(trn, 'settlement_currency', None)
        self.position_size_with_sign = position_size_with_sign
        self.position_size_with_sign_before = position_size_with_sign_before
        self.position_size_with_sign_after = position_size_with_sign_after
        self.cash_consideration = cash_consideration
        self.cash_consideration_before = cash_consideration_before
        self.cash_consideration_after = cash_consideration_after

    def add_balance(self, trn):
        self.position_size_with_sign += trn.position_size_with_sign
        self.cash_consideration += trn.cash_consideration


class CashFlowProjectionReport:
    def __init__(self, id=None, task_id=None, task_status=None, master_user=None, member=None,
                 balance_date=None, report_date=None, items=None):
        self.id = id
        self.task_id = task_id
        self.task_status = task_status
        self.master_user = master_user
        self.member = member
        self.balance_date = balance_date
        self.report_date = report_date
        self.items = items
        self.instruments = []
        self.currencies = []
        self.portfolios = []
        self.accounts = []

    def __str__(self):
        return 'CashFlowProjectionReport:%s' % self.id


class CashFlowProjectionReportBuilder(TransactionReportBuilder):
    def __init__(self, instance=None):
        super(CashFlowProjectionReportBuilder, self).__init__(instance)

        self._balance_items = {}

    def build(self):
        with transaction.atomic():
            self._load()
            # self._process()

            self._balance()

            # [CashFlowProjectionReportItem(transaction=t) for t in self._transactions]

            self.instance.items = list(self._balance_items.values())
            self.instance.instruments = list(self._instruments.values())
            self.instance.currencies = list(self._currencies.values())
            self.instance.portfolios = list(self._portfolios.values())
            self.instance.accounts = list(self._accounts.values())

            transaction.set_rollback(True)
        return self.instance

    def _balance(self):
        self._balance_items = {}

        def _key(t):
            return (
                getattr(t.complex_transaction, 'date', datetime.date.min),
                getattr(t.complex_transaction, 'code', -sys.maxsize),
                getattr(t, 'transaction_code', -sys.maxsize),
                getattr(t.instrument, 'id', -1),
                getattr(t.settlement_currency, 'id', -1),
                getattr(t.portfolio, 'id', -1),
                getattr(t.account_position, 'id', -1),
            )

        for t in self._transactions:
            if t.transaction_class_id in [TransactionClass.BUY, TransactionClass.SELL, TransactionClass.TRANSFER]:
                key = _key(t)

                item = self._balance_items.get(key, None)
                if item is None:
                    item = CashFlowProjectionReportItem(type=CashFlowProjectionReportItem.BALANCE, trn=t)
                    self._balance_items[key] = item

                item.add_balance(t)

    def _check_events(self, t):
        pass
