import logging
import time
from collections import defaultdict

from django.db import transaction
from django.db.models import Q

from poms.obj_attrs.models import GenericAttributeType
from poms.reports.builders.base_builder import BaseReportBuilder
from poms.reports.builders.transaction_item import TransactionReportItem
from poms.transactions.models import Transaction, ComplexTransaction

_l = logging.getLogger('poms.reports')


class TransactionReportBuilder(BaseReportBuilder):
    def __init__(self, instance):
        self.instance = instance
        self._transactions = []
        self._items = []

        self._similar_cache = defaultdict(dict)

        # self._complex_transactions = {}
        # self._transaction_types = {}
        # self._transaction_classes = {}
        # self._instruments = {}
        # self._currencies = {}
        # self._portfolios ={}
        # self._accounts = {}
        # self._strategies1 = {}
        # self._strategies2 = {}
        # self._strategies3 = {}
        # self._responsibles = {}
        # self._counterparties = {}
        # self._attribute_types = {}

    def build(self):
        st = time.perf_counter()
        _l.debug('build transaction')

        with transaction.atomic():
            # if settings.DEBUG:
            #     _l.debug('> _make_transactions')
            #     self._make_transactions(10000)
            #     _l.debug('< _make_transactions')

            self._load()
            # self._set_trns_refs(self._transactions)
            self._items = [TransactionReportItem(self.instance, trn=t) for t in self._transactions]
            self.instance.items = self._items
            self._refresh_from_db()
            # self._set_items_refs(self._items)
            # self._update_instance()
            self.instance.close()

            # if settings.DEBUG:
            #     _l.debug('> pickle')
            #     import pickle
            #     data = pickle.dumps(self.instance, protocol=pickle.HIGHEST_PROTOCOL)
            #     _l.debug('< pickle: %s', len(data))
            #     _l.debug('> pickle.zlib')
            #     import zlib
            #     data1 = zlib.compress(data)
            #     _l.debug('< pickle.zlib: %s', len(data1))
            #
            #     _l.debug('> json')
            #     from poms.reports.serializers import TransactionReportSerializer
            #     from rest_framework.renderers import JSONRenderer
            #     s = TransactionReportSerializer(instance=self.instance, context={
            #         'master_user': self.instance.master_user,
            #         'member': self.instance.member,
            #     })
            #     data_dict = s.data
            #     r = JSONRenderer()
            #     data = r.render(data_dict)
            #     _l.debug('< json: %s', len(data))
            #     _l.debug('> json.zlib')
            #     import zlib
            #     data1 = zlib.compress(data)
            #     _l.debug('< json.zlib: %s', len(data1))

            transaction.set_rollback(True)

        _l.debug('done: %s', (time.perf_counter() - st))
        return self.instance

    def _get_ref(self, clazz, pk, obj=None):
        tc = self._similar_cache[clazz]
        try:
            return tc[pk]
        except KeyError:
            if obj is not None:
                tc[pk] = obj
                return obj
        return None

    def _set_ref(self, obj, attr, attr_id=None, clazz=None):
        if attr_id is None:
            attr_id = '%s_id' % attr
        pk = getattr(obj, attr_id, None)
        if pk is None:
            return
        if clazz is None:
            obj = getattr(obj, attr, None)
            if obj is None:
                return
            clazz = type(obj)
        tc = self._similar_cache[clazz]
        if pk in tc:
            val = tc[pk]
            setattr(obj, attr, val)
        else:
            val = getattr(obj, attr)
            tc[pk] = val
        return val

    def _set_attrs(self, obj):
        if obj:
            for a in obj.attributes.all():
                self._set_ref(a, 'attribute_type', clazz=GenericAttributeType)

    def _trn_qs(self):
        from poms.obj_attrs.utils import get_attributes_prefetch

        qs = Transaction.objects.filter(
            master_user=self.instance.master_user,
            is_deleted=False,
        ).filter(
            Q(complex_transaction__isnull=True) | Q(complex_transaction__status=ComplexTransaction.PRODUCTION,
                                                    complex_transaction__is_deleted=False)
        ).prefetch_related(
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
        ).order_by(
            'complex_transaction__date', 'complex_transaction__code', 'transaction_code'
        )
        # if settings.DEBUG:
        #     qs = qs.filter(id__gt=1000)
        begin_date = getattr(self.instance, 'begin_date', None)
        if begin_date:
            qs = qs.filter(complex_transaction__date__gte=begin_date)
        end_date = getattr(self.instance, 'end_date', None)
        if end_date:
            qs = qs.filter(complex_transaction__date__lte=end_date)

        from poms.transactions.filters import TransactionObjectPermissionFilter
        qs = TransactionObjectPermissionFilter.filter_qs(qs, self.instance.master_user, self.instance.member)

        return qs

    def _load(self):

        _l.debug('> _load')

        # qs = Transaction.objects.filter(
        #     master_user=self.instance.master_user,
        #     is_deleted=False,
        # ).filter(
        #     Q(complex_transaction__isnull=True) | Q(complex_transaction__status=ComplexTransaction.PRODUCTION,
        #                                             complex_transaction__is_deleted=False)
        # ).prefetch_related(
        #     'complex_transaction',
        #     'transaction_class',
        #     'instrument',
        #     'instrument__event_schedules',
        #     'instrument__event_schedules__actions',
        #     'transaction_currency',
        #     'settlement_currency',
        #     'portfolio',
        #     'account_position',
        #     'account_cash',
        #     'account_interim',
        #     'strategy1_position',
        #     'strategy1_cash',
        #     'strategy2_position',
        #     'strategy2_cash',
        #     'strategy3_position',
        #     'strategy3_cash',
        #     'responsible',
        #     'counterparty',
        #     'linked_instrument',
        #     'allocation_balance',
        #     'allocation_pl',
        #     get_attributes_prefetch(),
        #     get_attributes_prefetch('complex_transaction__attributes'),
        #     get_attributes_prefetch('instrument__attributes'),
        #     get_attributes_prefetch('transaction_currency__attributes'),
        #     get_attributes_prefetch('settlement_currency__attributes'),
        #     get_attributes_prefetch('portfolio__attributes'),
        #     get_attributes_prefetch('account_position__attributes'),
        #     get_attributes_prefetch('account_cash__attributes'),
        #     get_attributes_prefetch('account_interim__attributes'),
        #     get_attributes_prefetch('responsible__attributes'),
        #     get_attributes_prefetch('counterparty__attributes'),
        #     get_attributes_prefetch('linked_instrument__attributes'),
        #     get_attributes_prefetch('allocation_balance__attributes'),
        #     get_attributes_prefetch('allocation_pl__attributes'),
        # ).order_by(
        #     'complex_transaction__date', 'complex_transaction__code', 'transaction_code'
        # )
        # # if settings.DEBUG:
        # #     qs = qs.filter(id__gt=1000)
        # begin_date = getattr(self.instance, 'begin_date', None)
        # if begin_date:
        #     qs = qs.filter(complex_transaction__date__gte=begin_date)
        # end_date = getattr(self.instance, 'end_date', None)
        # if end_date:
        #     qs = qs.filter(complex_transaction__date__lte=end_date)
        #
        # from poms.transactions.filters import TransactionObjectPermissionFilter
        # qs = TransactionObjectPermissionFilter.filter_qs(qs, self.instance.master_user, self.instance.member)

        qs = self._trn_qs()

        self._transactions = list(qs)

        _l.debug('< _load %s', len(self._transactions))

    # def _set_trns_refs(self, transactions):
    #     # make all refs to single object
    #     # _l.debug('> _set_trns_refs')
    #     for t in transactions:
    #         self._set_ref(t, 'complex_transaction', clazz=ComplexTransaction)
    #         if t.complex_transaction:
    #             self._set_ref(t.complex_transaction, 'transaction_type', clazz=TransactionType)
    #             # for a in t.complex_transaction.attributes.all():
    #             #     self._set_ref(a, 'attribute_type', clazz=GenericAttributeType)
    #             self._set_attrs(t.complex_transaction)
    #
    #         self._set_ref(t, 'transaction_class', clazz=TransactionClass)
    #         self._set_ref(t, 'instrument', clazz=Instrument)
    #         self._set_attrs(t.instrument)
    #         if t.instrument:
    #             self._set_ref(t.instrument, 'pricing_currency', clazz=Currency)
    #             self._set_ref(t.instrument, 'accrued_currency', clazz=Currency)
    #         self._set_ref(t, 'transaction_currency', clazz=Currency)
    #         self._set_attrs(t.transaction_currency)
    #         self._set_ref(t, 'settlement_currency', clazz=Currency)
    #         self._set_attrs(t.settlement_currency)
    #         self._set_ref(t, 'portfolio', clazz=Portfolio)
    #         self._set_attrs(t.portfolio)
    #         self._set_ref(t, 'account_position', clazz=Account)
    #         self._set_attrs(t.account_position)
    #         self._set_ref(t, 'account_cash', clazz=Account)
    #         self._set_attrs(t.account_cash)
    #         self._set_ref(t, 'account_interim', clazz=Account)
    #         self._set_attrs(t.account_interim)
    #         self._set_ref(t, 'strategy1_position', clazz=Strategy1)
    #         self._set_ref(t, 'strategy1_cash', clazz=Strategy1)
    #         self._set_ref(t, 'strategy2_position', clazz=Strategy2)
    #         self._set_ref(t, 'strategy2_cash', clazz=Strategy2)
    #         self._set_ref(t, 'strategy3_position', clazz=Strategy3)
    #         self._set_ref(t, 'strategy3_cash', clazz=Strategy3)
    #         self._set_ref(t, 'responsible', clazz=Responsible)
    #         self._set_attrs(t.responsible)
    #         self._set_ref(t, 'counterparty', clazz=Counterparty)
    #         self._set_attrs(t.counterparty)
    #         self._set_ref(t, 'linked_instrument', clazz=Instrument)
    #         if t.linked_instrument:
    #             self._set_ref(t.linked_instrument, 'pricing_currency', clazz=Currency)
    #             self._set_ref(t.linked_instrument, 'accrued_currency', clazz=Currency)
    #         self._set_attrs(t.linked_instrument)
    #         self._set_ref(t, 'allocation_balance', clazz=Instrument)
    #         if t.allocation_balance:
    #             self._set_ref(t.allocation_balance, 'pricing_currency', clazz=Currency)
    #             self._set_ref(t.allocation_balance, 'accrued_currency', clazz=Currency)
    #         self._set_attrs(t.allocation_balance)
    #         self._set_ref(t, 'allocation_pl', clazz=Instrument)
    #         if t.allocation_pl:
    #             self._set_ref(t.allocation_pl, 'pricing_currency', clazz=Currency)
    #             self._set_ref(t.allocation_pl, 'accrued_currency', clazz=Currency)
    #         self._set_attrs(t.allocation_pl)
    #
    #         # if t.id > 0:
    #         #     for a in t.attributes.all():
    #         #         self._set_ref(a, 'attribute_type', clazz=GenericAttributeType)
    #         #         # _l.debug('< _set_trns_refs')
    #         self._set_attrs(t)

    # def _set_items_refs(self, items):
    #     for t in items:
    #         self._set_ref(t, 'complex_transaction', clazz=ComplexTransaction)
    #         if t.complex_transaction:
    #             self._set_ref(t.complex_transaction, 'transaction_type', clazz=TransactionType)
    #         self._set_ref(t, 'transaction_class', clazz=TransactionClass)
    #         self._set_ref(t, 'instrument', clazz=Instrument)
    #         if t.instrument:
    #             self._set_ref(t.instrument, 'pricing_currency', clazz=Currency)
    #             self._set_ref(t.instrument, 'accrued_currency', clazz=Currency)
    #         self._set_ref(t, 'transaction_currency', clazz=Currency)
    #         self._set_ref(t, 'settlement_currency', clazz=Currency)
    #         self._set_ref(t, 'portfolio', clazz=Portfolio)
    #         self._set_ref(t, 'account_position', clazz=Account)
    #         self._set_ref(t, 'account_cash', clazz=Account)
    #         self._set_ref(t, 'account_interim', clazz=Account)
    #         self._set_ref(t, 'strategy1_position', clazz=Strategy1)
    #         self._set_ref(t, 'strategy1_cash', clazz=Strategy1)
    #         self._set_ref(t, 'strategy2_position', clazz=Strategy2)
    #         self._set_ref(t, 'strategy2_cash', clazz=Strategy2)
    #         self._set_ref(t, 'strategy3_position', clazz=Strategy3)
    #         self._set_ref(t, 'strategy3_cash', clazz=Strategy3)
    #         self._set_ref(t, 'responsible', clazz=Responsible)
    #         self._set_ref(t, 'counterparty', clazz=Counterparty)
    #         self._set_ref(t, 'linked_instrument', clazz=Instrument)
    #         if t.linked_instrument:
    #             self._set_ref(t.linked_instrument, 'pricing_currency', clazz=Currency)
    #             self._set_ref(t.linked_instrument, 'accrued_currency', clazz=Currency)
    #         self._set_ref(t, 'allocation_balance', clazz=Instrument)
    #         if t.allocation_balance:
    #             self._set_ref(t.allocation_balance, 'pricing_currency', clazz=Currency)
    #             self._set_ref(t.allocation_balance, 'accrued_currency', clazz=Currency)
    #         self._set_ref(t, 'allocation_pl', clazz=Instrument)
    #         if t.allocation_pl:
    #             self._set_ref(t.allocation_pl, 'pricing_currency', clazz=Currency)
    #             self._set_ref(t.allocation_pl, 'accrued_currency', clazz=Currency)

    def _refresh_from_db(self):
        _l.info('> _refresh_from_db')

        self.instance.complex_transactions = self._refresh_complex_transactions(
            master_user=self.instance.master_user,
            items=self.instance.items,
            attrs=['complex_transaction']
        )
        # self.instance.complex_transactions = self._refresh_item_instrument_accruals(
        #     master_user=self.instance.master_user,
        #     items=self.instance.items,
        #     attrs=['complex_transaction']
        # )

        self.instance.transaction_classes = self._refresh_transaction_classes(
            master_user=self.instance.master_user,
            items=self.instance.items,
            attrs=['transaction_class']
        )

        self.instance.instruments = self._refresh_instruments(
            master_user=self.instance.master_user,
            items=self.instance.items,
            attrs=['instrument', 'linked_instrument', 'allocation_balance', 'allocation_pl']
        )

        self.instance.currencies = self._refresh_currencies(
            master_user=self.instance.master_user,
            items=self.instance.items,
            attrs=['transaction_currency', 'settlement_currency']
        )

        self.instance.portfolios = self._refresh_portfolios(
            master_user=self.instance.master_user,
            items=self.instance.items,
            attrs=['portfolio']
        )

        self.instance.accounts = self._refresh_accounts(
            master_user=self.instance.master_user,
            items=self.instance.items,
            attrs=['account_position', 'account_cash', 'account_interim']
        )

        self.instance.strategies1 = self._refresh_strategies1(
            master_user=self.instance.master_user,
            items=self.instance.items,
            attrs=['strategy1_position', 'strategy1_cash']
        )

        self.instance.strategies2 = self._refresh_strategies2(
            master_user=self.instance.master_user,
            items=self.instance.items,
            attrs=['strategy2_position', 'strategy2_cash']
        )

        self.instance.strategies3 = self._refresh_strategies3(
            master_user=self.instance.master_user,
            items=self.instance.items,
            attrs=['strategy2_position', 'strategy3_cash']
        )

        self.instance.counterparties = self._refresh_counterparties(
            master_user=self.instance.master_user,
            items=self.instance.items,
            attrs=['counterparty']
        )
        self.instance.responsibles = self._refresh_responsibles(
            master_user=self.instance.master_user,
            items=self.instance.items,
            attrs=['responsible']
        )

        # complex_transactions = self._similar_cache[ComplexTransaction]
        # if complex_transactions:
        #     qs = ComplexTransaction.objects.filter(
        #         transaction_type__master_user=self.instance.master_user,
        #     ).prefetch_related(
        #         get_attributes_prefetch(),
        #     )
        #     complex_transactions.update(qs.in_bulk(id_list=complex_transactions.keys()))
        #
        # transaction_types = self._similar_cache[TransactionType]
        # if transaction_types:
        #     qs = TransactionType.objects.filter(
        #         master_user=self.instance.master_user,
        #     ).prefetch_related(
        #         'group',
        #         *get_permissions_prefetch_lookups(
        #             (None, TransactionType),
        #             ('group', TransactionTypeGroup),
        #         )
        #     )
        #     transaction_types.update(qs.in_bulk(id_list=transaction_types.keys()))
        #
        # instruments = self._similar_cache[Instrument]
        # if instruments:
        #     qs = Instrument.objects.filter(
        #         master_user=self.instance.master_user,
        #     ).prefetch_related(
        #         'instrument_type',
        #         'instrument_type__instrument_class',
        #         'pricing_currency',
        #         'accrued_currency',
        #         get_attributes_prefetch(),
        #         *get_permissions_prefetch_lookups(
        #             (None, Instrument),
        #             ('instrument_type', InstrumentType),
        #         )
        #     )
        #     instruments.update(qs.in_bulk(id_list=[pk for pk in instruments.keys() if pk > 0]))
        #
        #     for i in instruments.values():
        #         self._set_ref(i, 'pricing_currency', clazz=Currency)
        #         self._set_ref(i, 'accrued_currency', clazz=Currency)
        #
        # currencies = self._similar_cache[Currency]
        # if currencies:
        #     qs = Currency.objects.filter(
        #         master_user=self.instance.master_user,
        #     ).prefetch_related(
        #         get_attributes_prefetch(),
        #     )
        #     currencies.update(qs.in_bulk(id_list=currencies.keys()))
        #
        #     for i in instruments.values():
        #         self._set_ref(i, 'pricing_currency', clazz=Currency)
        #         self._set_ref(i, 'accrued_currency', clazz=Currency)
        #
        # portfolios = self._similar_cache[Portfolio]
        # if portfolios:
        #     qs = Portfolio.objects.filter(
        #         master_user=self.instance.master_user,
        #     ).prefetch_related(
        #         get_attributes_prefetch(),
        #         *get_permissions_prefetch_lookups(
        #             (None, Portfolio),
        #         )
        #     )
        #     portfolios.update(qs.in_bulk(id_list=portfolios.keys()))
        #
        # accounts = self._similar_cache[Account]
        # if accounts:
        #     qs = Account.objects.filter(
        #         master_user=self.instance.master_user,
        #     ).prefetch_related(
        #         'type',
        #         get_attributes_prefetch(),
        #         *get_permissions_prefetch_lookups(
        #             (None, Account),
        #             ('type', AccountType),
        #         )
        #     )
        #     accounts.update(qs.in_bulk(id_list=accounts.keys()))
        #
        # strategies1 = self._similar_cache[Strategy1]
        # if strategies1:
        #     qs = Strategy1.objects.filter(
        #         master_user=self.instance.master_user,
        #     ).prefetch_related(
        #         'subgroup',
        #         'subgroup__group',
        #         *get_permissions_prefetch_lookups(
        #             (None, Strategy1),
        #             ('subgroup', Strategy1Subgroup),
        #             ('subgroup__group', Strategy1Group),
        #         )
        #     )
        #     strategies1.update(qs.in_bulk(id_list=strategies1.keys()))
        #
        # strategies2 = self._similar_cache[Strategy2]
        # if strategies2:
        #     qs = Strategy2.objects.filter(
        #         master_user=self.instance.master_user,
        #     ).prefetch_related(
        #         'subgroup',
        #         'subgroup__group',
        #         *get_permissions_prefetch_lookups(
        #             (None, Strategy2),
        #             ('subgroup', Strategy2Subgroup),
        #             ('subgroup__group', Strategy2Group),
        #         )
        #     )
        #     strategies2.update(qs.in_bulk(id_list=strategies2.keys()))
        #
        # strategies3 = self._similar_cache[Strategy3]
        # if strategies3:
        #     qs = Strategy3.objects.filter(
        #         master_user=self.instance.master_user,
        #     ).prefetch_related(
        #         'subgroup',
        #         'subgroup__group',
        #         *get_permissions_prefetch_lookups(
        #             (None, Strategy3),
        #             ('subgroup', Strategy3Subgroup),
        #             ('subgroup__group', Strategy3Group),
        #         )
        #     )
        #     strategies3.update(qs.in_bulk(id_list=strategies3.keys()))
        #
        # responsibles = self._similar_cache[Responsible]
        # if responsibles:
        #     qs = Responsible.objects.filter(
        #         master_user=self.instance.master_user,
        #     ).prefetch_related(
        #         'group',
        #         get_attributes_prefetch(),
        #         *get_permissions_prefetch_lookups(
        #             (None, Responsible),
        #             ('group', ResponsibleGroup),
        #         )
        #     )
        #     responsibles.update(qs.in_bulk(id_list=responsibles.keys()))
        #
        # counterparties = self._similar_cache[Counterparty]
        # if counterparties:
        #     qs = Counterparty.objects.filter(
        #         master_user=self.instance.master_user,
        #     ).prefetch_related(
        #         'group',
        #         get_attributes_prefetch(),
        #         *get_permissions_prefetch_lookups(
        #             (None, Counterparty),
        #             ('group', CounterpartyGroup),
        #         )
        #     )
        #     counterparties.update(qs.in_bulk(id_list=counterparties.keys()))

        # attribute_types = self._similar_cache[GenericAttributeType]
        # if attribute_types:
        #     qs = GenericAttributeType.objects.filter(
        #         master_user=self.instance.master_user,
        #     ).prefetch_related(
        #         'content_type',
        #         'options',
        #         'classifiers',
        #         *get_permissions_prefetch_lookups(
        #             (None, GenericAttributeType),
        #         )
        #     )
        #     attribute_types.update(qs.in_bulk(id_list=attribute_types.keys()))

        _l.info('< _refresh_from_db')

        # def _update_instance(self):
        #     self.instance.items = self._items
        #
        #     for clazz, objects in self._similar_cache.items():
        #
        #         if clazz is ComplexTransaction:
        #             self.instance.complex_transactions = list(objects.values())
        #
        #         elif clazz is TransactionType:
        #             self.instance.transaction_types = list(objects.values())
        #
        #         elif clazz is TransactionClass:
        #             self.instance.transaction_classes = list(objects.values())
        #
        #         elif clazz is Instrument:
        #             self.instance.instruments = list(objects.values())
        #
        #         elif clazz is Currency:
        #             self.instance.currencies = list(objects.values())
        #
        #         elif clazz is Portfolio:
        #             self.instance.portfolios = list(objects.values())
        #
        #         elif clazz is Account:
        #             self.instance.accounts = list(objects.values())
        #
        #         elif clazz is Strategy1:
        #             self.instance.strategies1 = list(objects.values())
        #
        #         elif clazz is Strategy2:
        #             self.instance.strategies2 = list(objects.values())
        #
        #         elif clazz is Strategy3:
        #             self.instance.strategies3 = list(objects.values())
        #
        #         elif clazz is Responsible:
        #             self.instance.responsibles = list(objects.values())
        #
        #         elif clazz is Counterparty:
        #             self.instance.counterparties = list(objects.values())
        #
        #         # elif clazz is GenericAttributeType:
        #         #     self.instance.complex_transaction_attribute_types = []
        #         #     self.instance.transaction_attribute_types = []
        #         #     self.instance.instrument_attribute_types = []
        #         #     self.instance.currency_attribute_types = []
        #         #     self.instance.portfolio_attribute_types = []
        #         #     self.instance.account_attribute_types = []
        #         #     self.instance.responsible_attribute_types = []
        #         #     self.instance.counterparty_attribute_types = []
        #         #
        #         #     for at in objects.values():
        #         #         model_class = at.content_type.model_class()
        #         #
        #         #         if issubclass(model_class, ComplexTransaction):
        #         #             self.instance.complex_transaction_attribute_types.append(at)
        #         #
        #         #         elif issubclass(model_class, Transaction):
        #         #             self.instance.transaction_attribute_types.append(at)
        #         #
        #         #         elif issubclass(model_class, Instrument):
        #         #             self.instance.instrument_attribute_types.append(at)
        #         #
        #         #         elif issubclass(model_class, Currency):
        #         #             self.instance.currency_attribute_types.append(at)
        #         #
        #         #         elif issubclass(model_class, Portfolio):
        #         #             self.instance.portfolio_attribute_types.append(at)
        #         #
        #         #         elif issubclass(model_class, Account):
        #         #             self.instance.account_attribute_types.append(at)
        #         #
        #         #         elif issubclass(model_class, Responsible):
        #         #             self.instance.responsible_attribute_types.append(at)
        #         #
        #         #         elif issubclass(model_class, Counterparty):
        #         #             self.instance.counterparty_attribute_types.append(at)

        # def _make_transactions(self, count=100):
        #     from poms.common.utils import date_now
        #
        #     tcls = TransactionClass.objects.get(pk=TransactionClass.BUY)
        #
        #     tt = list(TransactionType.objects.filter(master_user=self.instance.master_user).all())
        #     instr = list(Instrument.objects.filter(master_user=self.instance.master_user).all())
        #     ccy = list(Currency.objects.filter(master_user=self.instance.master_user).all())
        #     p = list(Portfolio.objects.filter(master_user=self.instance.master_user).all())
        #     acc = list(Account.objects.filter(master_user=self.instance.master_user).all())
        #     s1 = list(Strategy1.objects.filter(master_user=self.instance.master_user).all())
        #     s2 = list(Strategy2.objects.filter(master_user=self.instance.master_user).all())
        #     s3 = list(Strategy3.objects.filter(master_user=self.instance.master_user).all())
        #     r = list(Responsible.objects.filter(master_user=self.instance.master_user).all())
        #     c = list(Counterparty.objects.filter(master_user=self.instance.master_user).all())
        #
        #     ctrns = []
        #     trns = []
        #
        #     for i in range(0, count):
        #         ct = ComplexTransaction(
        #             transaction_type=random.choice(tt),
        #             date=date_now() + datetime.timedelta(days=i),
        #             status=ComplexTransaction.PRODUCTION,
        #             code=i
        #         )
        #         ctrns.append(ct)
        #         t = Transaction(
        #             master_user=self.instance.master_user,
        #             complex_transaction=ct,
        #             complex_transaction_order=1,
        #             transaction_code=1,
        #             transaction_class=tcls,
        #             instrument=random.choice(instr),
        #             transaction_currency=random.choice(ccy),
        #             position_size_with_sign=100,
        #             settlement_currency=random.choice(ccy),
        #             cash_consideration=-90,
        #             principal_with_sign=100,
        #             carry_with_sign=100,
        #             overheads_with_sign=100,
        #             transaction_date=date_now() + datetime.timedelta(days=i),
        #             accounting_date=date_now() + datetime.timedelta(days=i),
        #             cash_date=date_now() + datetime.timedelta(days=i),
        #             portfolio=random.choice(p),
        #             account_position=random.choice(acc),
        #             account_cash=random.choice(acc),
        #             account_interim=random.choice(acc),
        #             strategy1_position=random.choice(s1),
        #             strategy1_cash=random.choice(s1),
        #             strategy2_position=random.choice(s2),
        #             strategy2_cash=random.choice(s2),
        #             strategy3_position=random.choice(s3),
        #             strategy3_cash=random.choice(s3),
        #             responsible=random.choice(r),
        #             counterparty=random.choice(c),
        #             linked_instrument=random.choice(instr),
        #             allocation_balance=random.choice(instr),
        #             allocation_pl=random.choice(instr),
        #         )
        #         trns.append(t)
        #
        #     ComplexTransaction.objects.bulk_create(ctrns)
        #     Transaction.objects.bulk_create(trns)
