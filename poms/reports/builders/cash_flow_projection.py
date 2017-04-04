import datetime
import logging
import sys
import time
from collections import defaultdict
from itertools import groupby

from django.db import transaction

from poms.common.utils import isclose
from poms.instruments.handlers import GeneratedEventProcess
from poms.instruments.models import GeneratedEvent
from poms.reports.builders.cash_flow_projection_item import CashFlowProjectionReportItem
from poms.reports.builders.transaction import TransactionReportBuilder
from poms.reports.builders.utils import empty, check_int_min, check_date_min
from poms.transactions.models import ComplexTransaction, TransactionType, TransactionClass

_l = logging.getLogger('poms.reports')


class CashFlowProjectionReportBuilder(TransactionReportBuilder):
    def __init__(self, instance):
        super(CashFlowProjectionReportBuilder, self).__init__(instance)

        self._transactions_by_date = None

        self._balance_items = {}
        self._rolling_items = {}
        # self._generated_transactions = []

        # self._instrument_event_cache = {}

        self._id_seq = 0
        self._transaction_order_seq = 0

    def build(self):
        st = time.perf_counter()
        _l.debug('build cash flow projection')

        with transaction.atomic():
            self._load()
            self._set_trns_refs(self._transactions)
            self._step1()
            self._step2()
            self._step3()
            self._refresh_from_db()
            self._set_items_refs(self._items)
            self._update_instance()
            self.instance.close()
            transaction.set_rollback(True)

        _l.debug('done: %s', (time.perf_counter() - st))
        return self.instance

    def _fake_id_gen(self):
        self._id_seq -= 1
        return self._id_seq

    def _trn_order_gen(self):
        self._transaction_order_seq += 1
        return self._transaction_order_seq

    def _trn_key(self, trn, acc=empty):
        if acc is empty:
            acc = trn.account_cash
        return (
            check_int_min(getattr(trn.settlement_currency, 'id', None)),
            check_int_min(getattr(trn.portfolio, 'id', None)),
            check_int_min(getattr(acc, 'id', None)),
            # getattr(trn.instrument, 'id', -1),
        )

    def _item(self, cache, trn, key, itype=CashFlowProjectionReportItem.DEFAULT):
        if key is None:
            key = self._trn_key(trn)
        item = cache.get(key, None)
        if item is None:
            # override by '-'
            if itype in [CashFlowProjectionReportItem.BALANCE, CashFlowProjectionReportItem.ROLLING]:
                ctrn = ComplexTransaction(
                    # id=self._fake_id_gen(),
                    date=self.instance.balance_date,
                    status=ComplexTransaction.PRODUCTION,
                    code=-sys.maxsize,
                )
                ctrn._fake_transactions = []
                item = CashFlowProjectionReportItem(
                    self.instance,
                    type=itype,
                    # id=self._fake_id_gen(),
                    complex_transaction=ctrn,
                    complex_transaction_order=0,
                    transaction_code=-sys.maxsize,
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
                    attributes=[],
                    transaction_class=None,
                    position_size_with_sign=0.0,
                    cash_consideration=0.0,
                    principal_with_sign=0.0,
                    carry_with_sign=0.0,
                    overheads_with_sign=0.0,
                    transaction_date=self.instance.balance_date,
                    accounting_date=self.instance.balance_date,
                    cash_date=self.instance.balance_date,
                    reference_fx_rate=1.0,
                )
                if itype == CashFlowProjectionReportItem.BALANCE:
                    item.instrument = None
                elif itype == CashFlowProjectionReportItem.ROLLING:
                    item.complex_transaction.date = datetime.date.max
                    # item.complex_transaction.code = sys.maxsize
                    # item.transaction_code = sys.maxsize
                    item.transaction_date = datetime.date.max
                    item.accounting_date = datetime.date.max
                    item.cash_date = datetime.date.max
            else:
                item = CashFlowProjectionReportItem(self.instance, type=itype, trn=trn)
            cache[key] = item
        return item

    def _balance(self, trn, key=None):
        return self._item(self._balance_items, trn, key, itype=CashFlowProjectionReportItem.BALANCE)

    def _rolling(self, trn, key=None):
        return self._item(self._rolling_items, trn, key, itype=CashFlowProjectionReportItem.ROLLING)

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
                key = self._trn_key(t)
                bitem = self._balance(t, key)
                bitem.add_balance(t)

                if t.transaction_class_id in [TransactionClass.BUY, TransactionClass.SELL]:
                    key = self._trn_key(t)
                    ritem = self._rolling(t, key)
                    ritem.add_balance(t)
                elif t.transaction_class_id in [TransactionClass.TRANSFER]:
                    raise RuntimeError('implement me please')

        for k, bitem in self._balance_items.items():
            self._items.append(bitem)

            # if settings.DEBUG:
            #     for k, ritem in self._rolling_items.items():
            #         self._items.append(ritem)

    def _step2(self):
        # eval future events
        now = self.instance.balance_date
        td1 = datetime.timedelta(days=1)
        while now < self.instance.report_date:
            now += td1
            _l.debug('\tnow=%s', now.isoformat())

            # check events
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

                        if e.is_apply_default_on_date(now):
                            a = e.get_default_action()
                            if a:
                                self._set_ref(a, 'transaction_type', clazz=TransactionType)

                                _l.debug('\t\t\tevent_schedule=%s, action=%s, confirmed', es.id, a.id)
                                gep = GeneratedEventProcess(
                                    generated_event=e,
                                    action=a,
                                    fake_id_gen=self._fake_id_gen,
                                    transaction_order_gen=self._trn_order_gen,
                                    now=now
                                )
                                gep.process()
                                if gep.has_errors:
                                    self.instance.has_errors = True
                                else:
                                    # for i2 in gep.instruments:
                                    #     if i2.id < 0 and i2.id not in self._instruments:
                                    #         self._instruments[i2.id] = i2
                                    # gep.complex_transaction._fake_transactions = list(gep.transactions)
                                    # self._prefetch(gep.transactions)
                                    self._set_trns_refs(gep.transactions)
                                    for t2 in gep.transactions:
                                        _l.debug('\t\t\t+trn=%s', t2.id)
                                        d = getattr(t2.complex_transaction, 'date', datetime.date.max)
                                        self._transactions_by_date[d].append(t2)

            # process transactions
            if now in self._transactions_by_date:
                for t in self._transactions_by_date[now]:
                    _l.debug('\t\t\ttrn=%s', t.id)
                    key = self._trn_key(t)
                    item = CashFlowProjectionReportItem(self.instance, trn=t)
                    self._items.append(item)

                    ritem = None
                    if t.transaction_class_id in [TransactionClass.BUY, TransactionClass.SELL]:
                        ritem = self._rolling(t, key)
                        ritem.add_balance(t)
                    elif t.transaction_class_id in [TransactionClass.TRANSFER]:
                        raise RuntimeError('implement me please')

                    if ritem and isclose(ritem.position_size_with_sign, 0.0):
                        del self._rolling_items[key]

    def _step3(self):
        # aggregate some rolling values
        # sort result

        def _sort_key(i):
            if i.type == CashFlowProjectionReportItem.BALANCE:
                type_sort_val = 0
            elif i.type == CashFlowProjectionReportItem.DEFAULT:
                type_sort_val = 1
            else:
                type_sort_val = 2
            return (
                check_int_min(getattr(i.settlement_currency, 'id', None)),
                check_int_min(getattr(i.portfolio, 'id', None)),
                check_int_min(getattr(i.account_cash, 'id', None)),
                # getattr(trn.instrument, 'id', -1),
                type_sort_val,
                check_date_min(getattr(i.complex_transaction, 'date', None)),
                check_int_min(getattr(i.complex_transaction, 'code', None)),
                check_int_min(i.complex_transaction_order),
                check_int_min(i.transaction_code),
            )

        def _group_key(i):
            return (
                # _check_date_min(getattr(i.complex_transaction, 'date', None)),
                # _check_int_min(getattr(i.complex_transaction, 'code', None)),
                # _check_int_min(i.complex_transaction_order),
                # _check_int_min(i.transaction_code),
                check_int_min(getattr(i.settlement_currency, 'id', None)),
                check_int_min(getattr(i.portfolio, 'id', None)),
                check_int_min(getattr(i.account_cash, 'id', None)),
            )

        items = sorted(self._items, key=_sort_key)
        for k, g in groupby(items, key=_group_key):
            rolling_cash_consideration = 0.0
            for i in g:
                if i.type == CashFlowProjectionReportItem.BALANCE:
                    rolling_cash_consideration = i.cash_consideration
                    i.cash_consideration_before = 0.0
                    i.cash_consideration_after = rolling_cash_consideration
                else:
                    i.cash_consideration_before = rolling_cash_consideration
                    i.cash_consideration_after = i.cash_consideration_before + i.cash_consideration
                    rolling_cash_consideration = i.cash_consideration_after

        def _resp_sort_key(i):
            # if i.type == CashFlowProjectionReportItem.BALANCE:
            #     type_sort_val = 0
            # elif i.type == CashFlowProjectionReportItem.DEFAULT:
            #     type_sort_val = 1
            # else:
            #     type_sort_val = 2
            return (
                check_date_min(getattr(i.complex_transaction, 'date', None)),
                # type_sort_val,
                check_int_min(getattr(i.complex_transaction, 'code', None)),
                check_int_min(i.complex_transaction_order),
                check_int_min(i.transaction_code),
            )

        self._items = sorted(self._items, key=_resp_sort_key)
