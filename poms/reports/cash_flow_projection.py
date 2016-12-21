import copy
import datetime
import logging
import random
import sys
from collections import defaultdict

from django.conf import settings
from django.db import transaction
from django.db.models import Q

from poms.accounts.models import Account, AccountType
from poms.common.utils import isclose
from poms.counterparties.models import Counterparty, ResponsibleGroup, CounterpartyGroup
from poms.counterparties.models import Responsible
from poms.currencies.models import Currency
from poms.instruments.handlers import GeneratedEventProcess
from poms.instruments.models import Instrument, InstrumentType, GeneratedEvent
from poms.obj_attrs.models import GenericAttributeType
from poms.portfolios.models import Portfolio
from poms.strategies.models import Strategy1, Strategy2, Strategy3, Strategy1Subgroup, Strategy1Group, \
    Strategy2Subgroup, Strategy2Group, Strategy3Subgroup, Strategy3Group
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
        self.instrument = instrument if instrument is not None else \
            getattr(trn, 'instrument', None)
        self.transaction_currency = transaction_currency if transaction_currency is not None else \
            getattr(trn, 'transaction_currency', None)
        self.position_size_with_sign = position_size_with_sign if position_size_with_sign is not None else \
            getattr(trn, 'position_size_with_sign', 0.0)
        self.settlement_currency = settlement_currency if settlement_currency is not None else \
            getattr(trn, 'settlement_currency', None)
        self.cash_consideration = cash_consideration if cash_consideration is not None else \
            getattr(trn, 'cash_consideration', 0.0)
        self.principal_with_sign = principal_with_sign if principal_with_sign is not None else \
            getattr(trn, 'principal_with_sign', 0.0)
        self.carry_with_sign = carry_with_sign if carry_with_sign is not None else \
            getattr(trn, 'carry_with_sign', 0.0)
        self.overheads_with_sign = overheads_with_sign if overheads_with_sign is not None else \
            getattr(trn, 'overheads_with_sign', 0.0)
        self.transaction_date = transaction_date if transaction_date is not None else \
            getattr(trn, 'transaction_date', datetime.date.min)
        self.accounting_date = accounting_date if accounting_date is not None else \
            getattr(trn, 'accounting_date', datetime.date.min)
        self.cash_date = cash_date if cash_date is not None else \
            getattr(trn, 'cash_date', datetime.date.min)
        self.portfolio = portfolio if portfolio is not None else \
            getattr(trn, 'portfolio', None)
        self.account_position = account_position if account_position is not None else \
            getattr(trn, 'account_position', None)
        self.account_cash = account_cash if account_cash is not None else \
            getattr(trn, 'account_cash', None)
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
        self.responsible = responsible if responsible is not None else \
            getattr(trn, 'responsible', None)
        self.counterparty = counterparty if counterparty is not None else \
            getattr(trn, 'counterparty', None)
        self.linked_instrument = linked_instrument if linked_instrument is not None else \
            getattr(trn, 'linked_instrument', None)
        self.allocation_balance = allocation_balance if allocation_balance is not None else \
            getattr(trn, 'allocation_balance', None)
        self.allocation_pl = allocation_pl if allocation_pl is not None else \
            getattr(trn, 'allocation_pl', None)
        self.reference_fx_rate = reference_fx_rate if reference_fx_rate is not None else \
            getattr(trn, 'reference_fx_rate', None)
        self.attributes = attributes if attributes is not None else \
            getattr(trn, 'attributes', None).all()

    def __str__(self):
        return 'TransactionReportItem:%s' % self.id


class TransactionReport:
    def __init__(self, id=None, task_id=None, task_status=None, master_user=None, member=None,
                 begin_date=None, end_date=None, items=None):
        self.has_errors = False
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

        self.transaction_attribute_types = []
        self.instrument_attribute_types = []
        self.currency_attribute_types = []
        self.portfolio_attribute_types = []
        self.account_attribute_types = []
        self.responsible_attribute_types = []
        self.counterparty_attribute_types = []

    def __str__(self):
        return 'TransactionReport:%s' % self.id


class TransactionReportBuilder:
    def __init__(self, instance=None):
        self.instance = instance
        self._transactions = []
        self._items = []
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
        self._attribute_types = {}

    def _load(self):
        from poms.obj_attrs.utils import get_attributes_prefetch

        _l.debug('> _load')

        qs = Transaction.objects.filter(
            master_user=self.instance.master_user,
            is_canceled=False,
            id__gt=10000
        ).filter(
            Q(complex_transaction__status=ComplexTransaction.PRODUCTION) | Q(complex_transaction__isnull=True)
        ).prefetch_related(
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

        _l.debug('< _load %s', len(self._transactions))

    def _prefetch(self):
        from poms.obj_attrs.utils import get_attributes_prefetch
        from poms.obj_perms.utils import get_permissions_prefetch_lookups

        _l.debug('> _prefetch')

        self._complex_transactions = {}
        self._transaction_types = {}
        self._transaction_classes = {}
        # force full prefetch for "-"
        self._instruments = {self.instance.master_user.instrument_id: None}
        self._currencies = {self.instance.master_user.currency_id: None}
        self._portfolios = {self.instance.master_user.portfolio_id: None}
        self._accounts = {self.instance.master_user.account_id: None}
        self._strategies1 = {self.instance.master_user.strategy1_id: None}
        self._strategies2 = {self.instance.master_user.strategy2_id: None}
        self._strategies3 = {self.instance.master_user.strategy3_id: None}
        self._responsibles = {self.instance.master_user.responsible_id: None}
        self._counterparties = {self.instance.master_user.counterparty_id: None}
        self._attribute_types = {}

        def _c(cache, obj, attr):
            attr_pk_name = '%s_id' % attr
            attr_pk = getattr(obj, attr_pk_name, None)
            if attr_pk is not None:
                cache[attr_pk] = None

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
            for a in t.attributes.all():
                self._attribute_types[a.attribute_type_id] = None
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
                for a in o.attributes.all():
                    self._attribute_types[a.attribute_type_id] = None
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
                for a in o.attributes.all():
                    self._attribute_types[a.attribute_type_id] = None
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
                for a in o.attributes.all():
                    self._attribute_types[a.attribute_type_id] = None
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
                for a in o.attributes.all():
                    self._attribute_types[a.attribute_type_id] = None
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
                for a in o.attributes.all():
                    self._attribute_types[a.attribute_type_id] = None
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
                for a in o.attributes.all():
                    self._attribute_types[a.attribute_type_id] = None
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

        if self._attribute_types:
            qs = GenericAttributeType.objects.filter(
                master_user=self.instance.master_user,
            ).prefetch_related(
                'content_type',
                'options',
                'classifiers',
                *get_permissions_prefetch_lookups(
                    (None, GenericAttributeType),
                )
            )
            for at in qs:
                self._attribute_types[at.id] = at

        _l.debug('< _prefetch')

    def _update_instance(self):
        self.instance.items = self._items

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

        self.instance.transaction_attribute_types = []
        self.instance.instrument_attribute_types = []
        self.instance.currency_attribute_types = []
        self.instance.portfolio_attribute_types = []
        self.instance.account_attribute_types = []
        self.instance.responsible_attribute_types = []
        self.instance.counterparty_attribute_types = []
        for at in self._attribute_types.values():
            model_class = at.content_type.model_class()
            if issubclass(model_class, Transaction):
                self.instance.transaction_attribute_types.append(at)
            elif issubclass(model_class, Instrument):
                self.instance.instrument_attribute_types.append(at)
            elif issubclass(model_class, Currency):
                self.instance.currency_attribute_types.append(at)
            elif issubclass(model_class, Portfolio):
                self.instance.portfolio_attribute_types.append(at)
            elif issubclass(model_class, Account):
                self.instance.account_attribute_types.append(at)
            elif issubclass(model_class, Responsible):
                self.instance.responsible_attribute_types.append(at)
            elif issubclass(model_class, Counterparty):
                self.instance.counterparty_attribute_types.append(at)

    def build(self):
        with transaction.atomic():
            # _l.debug('> _make_transactions')
            # self._make_transactions(10000)
            # _l.debug('< _make_transactions')

            self._load()
            self._prefetch()
            self._items = [TransactionReportItem(trn=t) for t in self._transactions]
            self._update_instance()

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


class CashFlowProjectionReportItem(TransactionReportItem):
    DEFAULT = 1
    BALANCE = 100
    ROLLING = 101
    TYPE_CHOICE = (
        (DEFAULT, 'Default'),
        (BALANCE, 'Balance'),
    )

    def __init__(self, type=DEFAULT, trn=None, position_size_with_sign_before=0.0,
                 position_size_with_sign_after=0.0, cash_consideration_before=0.0,
                 cash_consideration_after=0.0, **kwargs):
        super(CashFlowProjectionReportItem, self).__init__(trn, **kwargs)
        self.type = type
        self.position_size_with_sign_before = position_size_with_sign_before
        self.position_size_with_sign_after = position_size_with_sign_after
        self.cash_consideration_before = cash_consideration_before
        self.cash_consideration_after = cash_consideration_after

    def add_balance(self, trn_or_item):
        self.position_size_with_sign += trn_or_item.position_size_with_sign
        self.cash_consideration += trn_or_item.cash_consideration
        self.principal_with_sign += trn_or_item.principal_with_sign
        self.carry_with_sign += trn_or_item.carry_with_sign
        self.overheads_with_sign += trn_or_item.overheads_with_sign

    def __str__(self):
        return 'CashFlowProjectionReportItem:%s' % self.id


class CashFlowProjectionReport(TransactionReport):
    def __init__(self, balance_date=None, report_date=None, **kwargs):
        super(CashFlowProjectionReport, self).__init__(**kwargs)
        self.balance_date = balance_date
        self.report_date = report_date

    def __str__(self):
        return 'CashFlowProjectionReport:%s' % self.id


class CashFlowProjectionReportBuilder(TransactionReportBuilder):
    def __init__(self, instance=None):
        super(CashFlowProjectionReportBuilder, self).__init__(instance)

        self._transactions_by_date = None

        self._balance_items = {}
        self._rolling_items = {}
        # self._generated_transactions = []

        # self._instrument_event_cache = {}

        self._id_seq = 0
        self._transaction_order_seq = 0

    def _fake_id_gen(self):
        self._id_seq -= 1
        return self._id_seq

    def _trn_order_gen(self):
        self._transaction_order_seq += 1
        return self._transaction_order_seq

    def _trn_key(self, trn):
        return (
            # getattr(trn.complex_transaction, 'date', datetime.date.min),
            # getattr(trn.complex_transaction, 'code', float('-inf')),
            # getattr(trn, 'transaction_code', float('-inf')),
            getattr(trn.instrument, 'id', -1),
            getattr(trn.settlement_currency, 'id', -1),
            getattr(trn.portfolio, 'id', -1),
            getattr(trn.account_position, 'id', -1),
        )

    def _get_or_create(self, cache, key, trn, itype=CashFlowProjectionReportItem.DEFAULT):
        item = cache.get(key, None)
        if item is None:
            # override by '-'
            if itype == CashFlowProjectionReportItem.BALANCE:
                complex_transaction = ComplexTransaction(
                    date=self.instance.balance_date,
                    status=ComplexTransaction.PRODUCTION,
                    code=0,
                )
                item = CashFlowProjectionReportItem(
                    type=itype,
                    complex_transaction=complex_transaction,
                    complex_transaction_order=0,
                    transaction_code=0,
                    trn=trn,
                    transaction_currency=trn.settlement_currency,
                    account_cash=self.instance.master_user.account,
                    account_interim=self.instance.master_user.account,
                    strategy1_position=self.instance.master_user.strategy1,
                    strategy1_cash=self.instance.master_user.strategy1,
                    strategy2_position=self.instance.master_user.strategy2,
                    strategy2_cash=self.instance.master_user.strategy2,
                    strategy3_position=self.instance.master_user.strategy3,
                    strategy3_cash=self.instance.master_user.strategy3,
                    responsible=self.instance.master_user.responsible,
                    counterparty=self.instance.master_user.counterparty,
                    linked_instrument=self.instance.master_user.instrument,
                    allocation_balance=self.instance.master_user.instrument,
                    allocation_pl=self.instance.master_user.instrument,
                    attributes=None,
                    transaction_class=None,
                    position_size_with_sign=0.0,
                    cash_consideration=0.0,
                    principal_with_sign=0.0,
                    carry_with_sign=0.0,
                    overheads_with_sign=0.0,
                    transaction_date=self.instance.balance_date,
                    accounting_date=self.instance.balance_date,
                    cash_date=self.instance.balance_date,
                    reference_fx_rate=0.0,
                )
            else:
                item = CashFlowProjectionReportItem(type=itype, trn=trn)
            cache[key] = item
        return item

    def build(self):
        with transaction.atomic():
            self._load()

            self._step1()
            self._step2()
            self._update_instance()

            # self.instance.items = list(self._balance_items.values())
            # self.instance.items = list(self._balance_items.values()) + [
            #     CashFlowProjectionReportItem(type=CashFlowProjectionReportItem.DEFAULT, trn=t)
            #     for t in self._generated_transactions]

            transaction.set_rollback(True)
        return self.instance

    def _update_instance(self):
        self.instance.items = self._items

    def _step1(self):
        self._transactions_by_date = defaultdict(list)
        self._items = []
        self._balance_items = {}
        self._rolling_items = {}

        for t in self._transactions:
            self._transaction_order_seq = max(self._transaction_order_seq, int(t.transaction_code))

            d = getattr(t.complex_transaction, 'date', datetime.date.min)
            self._transactions_by_date[d].append(t)

            if d <= self.instance.balance_date:
                if t.transaction_class_id in [TransactionClass.BUY, TransactionClass.SELL]:
                    key = self._trn_key(t)
                    bitem = self._get_or_create(self._balance_items, key, t, itype=CashFlowProjectionReportItem.BALANCE)
                    bitem.add_balance(t)
                elif t.transaction_class_id in [TransactionClass.TRANSFER]:
                    pass

        for k, bitem in self._balance_items.items():
            self._items.append(bitem)

            ritem = copy.copy(bitem)
            ritem.complex_transaction = copy.copy(ritem.complex_transaction)
            ritem.complex_transaction.date = datetime.date.max
            ritem.complex_transaction.code = sys.maxsize
            ritem.transaction_code = sys.maxsize
            ritem.transaction_date = self.instance.balance_date
            ritem.accounting_date = self.instance.balance_date
            ritem.cash_date = self.instance.balance_date

            self._rolling_items[k] = ritem

            if settings.DEBUG:
                ritem.type = CashFlowProjectionReportItem.ROLLING
                self._items.append(ritem)

    def _step2(self):
        now = self.instance.balance_date
        t1 = datetime.timedelta(days=1)

        while now < self.instance.report_date:
            now += t1
            _l.debug('\tnow=%s', now.isoformat())

            for key, ritem in self._rolling_items.items():
                instr = ritem.instrument
                if instr is None:
                    raise RuntimeError('code bug (instrument is None)')

                for es in instr.event_schedules.all():
                    is_complies, edate, ndate = es.check_date(now)
                    if is_complies:
                        e = GeneratedEvent()
                        e.master_user = self.instance.master_user
                        e.event_schedule = es
                        e.status = GeneratedEvent.NEW
                        e.effective_date = edate
                        e.notification_date = ndate
                        e.instrument = ritem.instrument
                        e.portfolio = ritem.portfolio
                        e.account = ritem.account_position
                        e.strategy1 = ritem.strategy1_position
                        e.strategy2 = ritem.strategy2_position
                        e.strategy3 = ritem.strategy3_position
                        e.position = ritem.position_size_with_sign

                        if e.is_apply_default_on_effective_date(now) or e.is_apply_default_on_notification_date(now):
                            a = None
                            for a0 in e.event_schedule.actions.all():
                                if a0.is_book_automatic:
                                    a = a0
                            if a:
                                _l.debug('\t\t\tevent_schedule=%s, action=%s, confirmed', es.id, a.id)
                                gep = GeneratedEventProcess(
                                    generated_event=e,
                                    action=a,
                                    calculate=True,
                                    store=False,
                                    complex_transaction_date=now,
                                    fake_id_gen=self._fake_id_gen,
                                    transaction_order_gen=self._trn_order_gen,
                                )
                                gep.process()
                                if gep.has_errors:
                                    self.instance.has_errors = True
                                else:
                                    for i2 in gep.instruments:
                                        if i2.id not in self._instruments:
                                            self._instruments[i2.id] = i2
                                    for t2 in gep.transactions:
                                        _l.debug('\t\t\t+trn=%s', t2.id)
                                        d = getattr(t2.complex_transaction, 'date', datetime.date.max)
                                        self._transactions_by_date[d].append(t2)

            if now in self._transactions_by_date:
                for t in self._transactions_by_date[now]:
                    _l.debug('\t\t\ttrn=%s', t.id)
                    key = self._trn_key(t)
                    item = CashFlowProjectionReportItem(trn=t)
                    self._items.append(item)

                    ritem = None
                    if t.transaction_class_id in [TransactionClass.BUY, TransactionClass.SELL]:
                        ritem = self._get_or_create(self._rolling_items, key, t,
                                                    itype=CashFlowProjectionReportItem.BALANCE)
                        ritem.add_balance(t)
                    elif t.transaction_class_id in [TransactionClass.TRANSFER]:
                        raise RuntimeError('implement me please')

                    if ritem and isclose(ritem.position_size_with_sign, 0.0):
                        del self._rolling_items[key]
