import logging
import random
from collections import Counter
from datetime import timedelta

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


class TransactionReport:
    def __init__(self, id=None, task_id=None, task_status=None, master_user=None, member=None,
                 begin_date=None, end_date=None, report_date=None,
                 transactions=None):
        self.id = id
        self.task_id = task_id
        self.task_status = task_status
        self.master_user = master_user
        self.member = member
        self.begin_date = begin_date
        self.end_date = end_date
        self.report_date = report_date
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


class TransactionReportBuilder:
    def __init__(self, instance=None):
        self.instance = instance

    def _get_transaction_qs(self):
        from poms.transactions.views import get_transaction_queryset
        from poms.obj_attrs.utils import get_attributes_prefetch

        qs = get_transaction_queryset(select_related=False, complex_transaction_transactions=True).prefetch_related(
            'instrument__instrument_type',
            'instrument__pricing_currency',
            'instrument__accrued_currency',
            'instrument__payment_size_detail',
            'instrument__daily_pricing_model',
            'instrument__price_download_scheme',

            'linked_instrument__instrument_type',
            'linked_instrument__pricing_currency',
            'linked_instrument__accrued_currency',
            'linked_instrument__payment_size_detail',
            'linked_instrument__daily_pricing_model',
            'linked_instrument__price_download_scheme',

            'allocation_balance__instrument_type',
            'allocation_balance__pricing_currency',
            'allocation_balance__accrued_currency',
            'allocation_balance__payment_size_detail',
            'allocation_balance__daily_pricing_model',
            'allocation_balance__price_download_scheme',

            'allocation_pl__instrument_type',
            'allocation_pl__pricing_currency',
            'allocation_pl__accrued_currency',
            'allocation_pl__payment_size_detail',
            'allocation_pl__daily_pricing_model',
            'allocation_pl__price_download_scheme',

            'transaction_currency__daily_pricing_model',

            'settlement_currency__daily_pricing_model',

        ).prefetch_related(
            get_attributes_prefetch(path='instrument__attributes'),
            get_attributes_prefetch(path='transaction_currency__attributes'),
            get_attributes_prefetch(path='settlement_currency__attributes'),
            get_attributes_prefetch(path='portfolio__attributes'),
            get_attributes_prefetch(path='account_cash__attributes'),
            get_attributes_prefetch(path='account_position__attributes'),
            get_attributes_prefetch(path='account_interim__attributes'),
            get_attributes_prefetch(path='responsible__attributes'),
            get_attributes_prefetch(path='counterparty__attributes'),
            get_attributes_prefetch(path='linked_instrument__attributes'),
            get_attributes_prefetch(path='allocation_balance__attributes'),
            get_attributes_prefetch(path='allocation_pl__attributes'),
        ).order_by(
            'complex_transaction__date', 'complex_transaction__code', 'transaction_code'
        )
        if self.instance.begin_date:
            qs = qs.filter(complex_transaction__date__gte=self.instance.begin_date)
        if self.instance.end_date:
            qs = qs.filter(complex_transaction__date__lte=self.instance.end_date)
        return qs

    def _load(self):
        from poms.obj_attrs.utils import get_attributes_prefetch
        from poms.obj_perms.utils import get_permissions_prefetch_lookups

        _l.info('> _load')

        transactions = []
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

        def _c(cache, obj, attr):
            attr_pk_name = '%s_id' % attr
            attr_pk = getattr(obj, attr_pk_name, None)
            if attr_pk is not None:
                cache[attr_pk] = None

        qs = Transaction.objects.prefetch_related(
            'complex_transaction',
            get_attributes_prefetch(),
        )
        if self.instance.begin_date:
            qs = qs.filter(complex_transaction__date__gte=self.instance.begin_date)
        if self.instance.end_date:
            qs = qs.filter(complex_transaction__date__lte=self.instance.end_date)

        _l.info('> transactions')
        for t in qs.all():
            transactions.append(t)

            if t.complex_transaction:
                _c(complex_transactions, t, 'complex_transaction')
                _c(transaction_types, t.complex_transaction, 'transaction_type')

            _c(transaction_classes, t, 'transaction_class')
            _c(instruments, t, 'instrument')
            _c(currencies, t, 'transaction_currency')
            _c(currencies, t, 'settlement_currency')
            _c(portfolios, t, 'portfolio')
            _c(accounts, t, 'account_position')
            _c(accounts, t, 'account_cash')
            _c(accounts, t, 'account_interim')
            _c(strategies1, t, 'strategy1_position')
            _c(strategies1, t, 'strategy1_cash')
            _c(strategies2, t, 'strategy2_position')
            _c(strategies2, t, 'strategy2_cash')
            _c(strategies3, t, 'strategy3_position')
            _c(strategies3, t, 'strategy3_cash')
            _c(responsibles, t, 'responsible')
            _c(counterparties, t, 'counterparty')
            _c(instruments, t, 'linked_instrument')
            _c(instruments, t, 'allocation_balance')
            _c(instruments, t, 'allocation_pl')
        _l.info('< transactions: %s', len(transactions))

        _l.info('> transaction_classes')
        if transaction_classes:
            qs = TransactionClass.objects.filter(
                pk__in=transaction_classes.keys()
            )
            for o in qs:
                transaction_classes[o.id] = o
        _l.info('< transaction_classes: %s', len(transaction_classes))

        _l.info('> complex_transactions')
        if complex_transactions:
            qs = ComplexTransaction.objects.filter(
                transaction_type__master_user=self.instance.master_user,
                pk__in=complex_transactions.keys()
            ).prefetch_related(
            )
            for o in qs:
                complex_transactions[o.id] = o
        _l.info('< complex_transactions: %s', len(complex_transactions))

        _l.info('> transaction_types')
        if transaction_types:
            qs = TransactionType.objects.filter(
                master_user=self.instance.master_user,
                pk__in=transaction_types.keys()
            ).prefetch_related(
                'group',
                *get_permissions_prefetch_lookups(
                    (None, TransactionType),
                    ('group', TransactionTypeGroup),
                )
            )
            for o in qs:
                transaction_types[o.id] = o
        _l.info('< transaction_types: %s', len(transactions))

        _l.info('> instruments')
        if instruments:
            qs = Instrument.objects.filter(
                master_user=self.instance.master_user,
                pk__in=instruments.keys()
            ).prefetch_related(
                'instrument_type',
                'instrument_type__instrument_class',
                'pricing_currency',
                'accrued_currency',
                get_attributes_prefetch(),
                *get_permissions_prefetch_lookups(
                    (None, Instrument),
                    ('instrument_type', InstrumentType),
                )
            )
            for o in qs:
                instruments[o.id] = o
        _l.info('< instruments: %s', len(instruments))

        _l.info('> currencies')
        if currencies:
            qs = Currency.objects.filter(
                master_user=self.instance.master_user,
                pk__in=currencies.keys()
            ).prefetch_related(
                get_attributes_prefetch(),
            )
            for o in qs:
                currencies[o.id] = o
        _l.info('< currencies: %s', len(currencies))

        _l.info('> portfolios')
        if portfolios:
            qs = Portfolio.objects.filter(
                master_user=self.instance.master_user,
                pk__in=portfolios.keys()
            ).prefetch_related(
                get_attributes_prefetch(),
                *get_permissions_prefetch_lookups(
                    (None, Portfolio),
                )
            )
            for o in qs:
                portfolios[o.id] = o
        _l.info('< portfolios: %s', len(portfolios))

        _l.info('> accounts')
        if accounts:
            qs = Account.objects.filter(
                master_user=self.instance.master_user,
                pk__in=accounts.keys()
            ).prefetch_related(
                'type',
                get_attributes_prefetch(),
                *get_permissions_prefetch_lookups(
                    (None, Account),
                    ('type', AccountType),
                )
            )
            for o in qs:
                accounts[o.id] = o
        _l.info('< accounts: %s', len(accounts))

        _l.info('> strategies1')
        if strategies1:
            qs = Strategy1.objects.filter(
                master_user=self.instance.master_user,
                pk__in=strategies1.keys()
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
                strategies1[o.id] = o
        _l.info('< strategies1: %s', len(strategies1))

        _l.info('> strategies2')
        if strategies2:
            qs = Strategy2.objects.filter(
                master_user=self.instance.master_user,
                pk__in=strategies2.keys()
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
                strategies2[o.id] = o
        _l.info('< strategies2: %s', len(strategies2))

        _l.info('> strategies3')
        if strategies3:
            qs = Strategy3.objects.filter(
                master_user=self.instance.master_user,
                pk__in=strategies3.keys()
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
                strategies3[o.id] = o
        _l.info('< strategies3: %s', len(strategies3))

        _l.info('> responsibles')
        if responsibles:
            qs = Responsible.objects.filter(
                master_user=self.instance.master_user,
                pk__in=responsibles.keys()
            ).prefetch_related(
                'group',
                get_attributes_prefetch(),
                *get_permissions_prefetch_lookups(
                    (None, Responsible),
                    ('group', ResponsibleGroup),
                )
            )
            for o in qs:
                responsibles[o.id] = o
        _l.info('< responsibles: %s', len(responsibles))

        _l.info('> counterparties')
        if counterparties:
            qs = Counterparty.objects.filter(
                master_user=self.instance.master_user,
                pk__in=counterparties.keys()
            ).prefetch_related(
                'group',
                get_attributes_prefetch(),
                *get_permissions_prefetch_lookups(
                    (None, Counterparty),
                    ('group', CounterpartyGroup),
                )
            )
            for o in qs:
                counterparties[o.id] = o
        _l.info('< counterparties: %s', len(counterparties))

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

        _l.info('> transactions')
        for t in transactions:
            if t.complex_transaction:
                _p(complex_transactions, t, 'complex_transaction')
                _p(transaction_types, t.complex_transaction, 'transaction_type')

                try:
                    t.complex_transaction._fake_transactions.append(t)
                except AttributeError:
                    t.complex_transaction._fake_transactions = [t]

            _p(transaction_classes, t, 'transaction_class')
            _p(instruments, t, 'instrument')
            _p(currencies, t, 'transaction_currency')
            _p(currencies, t, 'settlement_currency')
            _p(portfolios, t, 'portfolio')
            _p(accounts, t, 'account_position')
            _p(accounts, t, 'account_cash')
            _p(accounts, t, 'account_interim')
            _p(strategies1, t, 'strategy1_position')
            _p(strategies1, t, 'strategy1_cash')
            _p(strategies2, t, 'strategy2_position')
            _p(strategies2, t, 'strategy2_cash')
            _p(strategies3, t, 'strategy3_position')
            _p(strategies3, t, 'strategy3_cash')
            _p(responsibles, t, 'responsible')
            _p(counterparties, t, 'counterparty')
            _p(instruments, t, 'linked_instrument')
            _p(instruments, t, 'allocation_balance')
            _p(instruments, t, 'allocation_pl')
        _l.info('< transactions: %s', len(transactions))

        self.instance.transactions = transactions
        self.instance.complex_transactions = list(complex_transactions.values())
        self.instance.transaction_types = list(transaction_types.values())
        self.instance.transaction_classes = list(transaction_classes.values())
        self.instance.instruments = list(instruments.values())
        self.instance.currencies = list(currencies.values())
        self.instance.portfolios = list(portfolios.values())
        self.instance.accounts = list(accounts.values())
        self.instance.strategies1 = list(strategies1.values())
        self.instance.strategies2 = list(strategies2.values())
        self.instance.strategies3 = list(strategies3.values())
        self.instance.responsibles = list(responsibles.values())
        self.instance.counterparties = list(counterparties.values())

        _l.info('< _load')

    def build(self):
        with transaction.atomic():
            _l.info('> _make_transactions')
            # self._make_transactions(10000)
            _l.info('< _make_transactions')

            self._load()

            _l.info('> _process')
            self._process()
            _l.info('< _process')

            _l.info('> pickle')
            import pickle
            data = pickle.dumps(self.instance, protocol=pickle.HIGHEST_PROTOCOL)
            _l.info('< pickle: %s', len(data))

            _l.info('> zlib')
            import zlib
            data1 = zlib.compress(data)
            _l.info('< zlib: %s', len(data1))

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
                instrument=random.choice(instr),
                transaction_currency=random.choice(ccy),
                position_size_with_sign=100,
                settlement_currency=random.choice(ccy),
                cash_consideration=-90,
                principal_with_sign=100,
                carry_with_sign=100,
                overheads_with_sign=100,
                transaction_date=date_now() + timedelta(days=i),
                accounting_date=date_now() + timedelta(days=i),
                cash_date=date_now() + timedelta(days=i),
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
