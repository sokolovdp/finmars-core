from __future__ import unicode_literals

from django.utils.functional import cached_property

from poms.transactions.models import Transaction, TransactionClass


class BaseReportBuilder(object):
    def __init__(self, instance=None, queryset=None):
        self.instance = instance
        self.queryset = queryset

    @cached_property
    def transactions(self):
        if self.queryset is None:
            queryset = Transaction.objects
        else:
            queryset = self.queryset
        queryset = queryset.prefetch_related('transaction_class', 'instrument')
        if self.instance:
            queryset = queryset.filter(master_user=self.instance.master_user)
            if self.instance.begin_date:
                queryset = queryset.filter(transaction_date__gte=self.instance.begin_date)
            if self.instance.end_date:
                queryset = queryset.filter(transaction_date__lte=self.instance.end_date)
            if self.instance.instruments:
                queryset = queryset.filter(instrument__in=self.instance.instruments)
        queryset = queryset.order_by('transaction_date', 'id')
        return list(queryset.all())
        # return Transaction.objects.none()

    def build(self):
        raise NotImplementedError('subclasses of BaseReportBuilder must provide an build() method')

    def annotate_avco_multiplier(self):
        in_stock = {}
        for_sale = {}
        rolling_position = 0.

        for transaction in self.transactions:
            if transaction.transaction_class.code not in [TransactionClass.BUY, TransactionClass.SELL]:
                transaction.avco_multiplier = None
                transaction.fifo_multiplier = None
                transaction.rolling_position = None
                continue
            instrument = transaction.instrument
            position_size_with_sign = transaction.position_size_with_sign
            transaction.avco_multiplier = 0.
            if position_size_with_sign > 0.:  # покупка
                instrument_for_sale = for_sale.get(instrument, [])
                if instrument_for_sale:  # есть прошлые продажи, которые надо закрыть
                    if position_size_with_sign + rolling_position >= 0.:  # все есть
                        transaction.avco_multiplier = abs(rolling_position / position_size_with_sign)
                        for t in instrument_for_sale:
                            t.avco_multiplier = 1.
                        in_stock[instrument] = in_stock.get(instrument, []) + [transaction]
                    else:  # только частично
                        transaction.avco_multiplier = 1.
                        for t in instrument_for_sale:
                            t.avco_multiplier += abs((1. - t.avco_multiplier) * position_size_with_sign / rolling_position)
                    for_sale[instrument] = [t for t in instrument_for_sale if t.avco_multiplier < 1.]
                else:  # новая "чистая" покупка
                    transaction.avco_multiplier = 0.
                    in_stock[instrument] = in_stock.get(instrument, []) + [transaction]
            else:  # продажа
                instrument_in_stock = in_stock.get(instrument, [])
                if instrument_in_stock:  # есть что продавать
                    if position_size_with_sign + rolling_position >= 0.:  # все есть
                        transaction.avco_multiplier = 1.
                        for t in instrument_in_stock:
                            t.avco_multiplier += abs((1. - t.avco_multiplier) * position_size_with_sign / rolling_position)
                    else:  # только частично
                        transaction.avco_multiplier = abs(rolling_position / position_size_with_sign)
                        for t in instrument_in_stock:
                            t.avco_multiplier = 1.
                        for_sale[instrument] = for_sale.get(instrument, []) + [transaction]
                    in_stock[instrument] = [t for t in instrument_in_stock if t.avco_multiplier < 1.]
                else:  # нечего продавать
                    transaction.avco_multiplier = 0.
                    for_sale[instrument] = for_sale.get(instrument, []) + [transaction]
            rolling_position += position_size_with_sign
            transaction.rolling_position = rolling_position

    def annotate_fifo_multiplier(self):
        in_stock = {}
        for_sale = {}
        rolling_position = 0.

        for transaction in self.transactions:
            if transaction.transaction_class.code not in [TransactionClass.BUY, TransactionClass.SELL]:
                transaction.avco_multiplier = None
                transaction.fifo_multiplier = None
                transaction.rolling_position = None
                continue
            instrument = transaction.instrument
            position_size_with_sign = transaction.position_size_with_sign
            transaction.fifo_multiplier = 0.
            if position_size_with_sign > 0.:  # покупка
                instrument_for_sale = for_sale.get(instrument, [])
                balance = position_size_with_sign
                if instrument_for_sale:
                    for t in instrument_for_sale:
                        sale = t.not_closed
                        if balance + sale > 0.:  # есть все
                            balance -= abs(sale)
                            t.fifo_multiplier = 1.
                            t.not_closed = t.not_closed - abs(t.position_size_with_sign)
                        else:
                            t.not_closed = t.not_closed + balance
                            t.fifo_multiplier = 1. - abs(t.not_closed / t.position_size_with_sign)
                            balance = 0.
                        # sale = (1 - t.fifo_multiplier) * t.position_size_with_sign
                        # if balance + sale > 0.:  # есть все
                        #     balance -= abs(sale)
                        #     t.fifo_multiplier = 1.
                        # else:
                        #     t.fifo_multiplier = 1 - abs((abs(sale) - balance) / t.position_size_with_sign)
                        #     balance = 0.
                        if balance <= 0.:
                            break
                    for_sale[instrument] = [t for t in instrument_for_sale if t.fifo_multiplier < 1.]
                transaction.balance = balance
                transaction.fifo_multiplier = abs((position_size_with_sign - balance) / position_size_with_sign)
                if transaction.fifo_multiplier < 1.:
                    in_stock[instrument] = in_stock.get(instrument, []) + [transaction]
            else:  # продажа
                instrument_in_stock = in_stock.get(instrument, [])
                sale = position_size_with_sign
                if instrument_in_stock:
                    for t in instrument_in_stock:
                        balance = t.balance
                        if sale + balance > 0.:  # есть все
                            t.balance = balance - abs(sale)
                            t.fifo_multiplier = abs(
                                (t.position_size_with_sign - t.balance) / t.position_size_with_sign)
                            # print(t.position_size_with_sign)
                            # print(t.balance)
                            # print(t.position_size_with_sign - t.balance)
                            sale = 0.
                        else:
                            t.balance = 0.
                            t.fifo_multiplier = 1.
                            sale += abs(balance)
                        # balance = (1 - t.fifo_multiplier) * t.position_size_with_sign
                        # if sale + balance > 0.:  # есть все
                        #     t.fifo_multiplier = abs((balance - abs(sale)) / t.position_size_with_sign)
                        #     sale = 0.
                        # else:
                        #     t.fifo_multiplier = 1.
                        #     sale += abs(balance)
                        if sale >= 0.:
                            break
                    in_stock[instrument] = [t for t in instrument_in_stock if t.fifo_multiplier < 1.]
                transaction.not_closed = sale
                transaction.fifo_multiplier = abs((position_size_with_sign - sale) / position_size_with_sign)
                if transaction.fifo_multiplier < 1.:
                    for_sale[instrument] = for_sale.get(instrument, []) + [transaction]

            rolling_position += position_size_with_sign
            transaction.rolling_position = rolling_position
