from __future__ import unicode_literals

from django.conf import settings
from django.utils import timezone
from django.utils.functional import cached_property

from poms.currencies.models import CurrencyHistory, Currency
from poms.instruments.models import PriceHistory
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

    @cached_property
    def system_currency(self):
        return Currency.objects.get(master_user__isnull=True, user_code=settings.CURRENCY_CODE)

    def find_currency_history(self, currency, date=None):
        if currency is None:
            return None
        if currency.is_system:
            return CurrencyHistory(currency=currency, date=date, fx_rate=1.)
        if not date:
            date = self.instance.end_date or timezone.now().date()
        p = CurrencyHistory.objects.filter(currency=currency, date__lte=date).order_by('date').last()
        if p is None:
            return CurrencyHistory(currency=currency, date=date, fx_rate=0.)
        return p

    def find_price_history(self, instrument, date=None):
        if not date:
            date = self.instance.end_date or timezone.now().date()
        p = PriceHistory.objects.filter(instrument=instrument, date__lte=date).order_by('date').last()
        if p is None:
            return PriceHistory(instrument=instrument, date=date, principal_price=0., accrued_price=0., factor=0.)
        return p

    def annotate_fx_rates_and_prices(self):
        for t in self.transactions:
            if t.transaction_currency:
                t.transaction_currency_history = self.find_currency_history(t.transaction_currency)
                t.transaction_currency_fx_rate = getattr(t.transaction_currency_history, 'fx_rate', 0.) or 0.

            if t.settlement_currency:
                t.settlement_currency_history = self.find_currency_history(t.settlement_currency)
                t.settlement_currency_fx_rate = getattr(t.settlement_currency_history, 'fx_rate', 0.) or 0.

            # if t.transaction_class.code == TransactionClass.CASH_INFLOW:
            #     t.currency = t.transaction_currency
            #     t.transaction_currency_fx_rate = self.find_currency_history(t.transaction_currency, self.instance.end_date)
            # elif t.transaction_class.code in [TransactionClass.BUY, TransactionClass.SELL]:
            #     t.currency = t.settlement_currency
            #     t.currency_history = self.find_currency_history(t.settlement_currency, self.instance.end_date)
            # elif t.transaction_class.code == TransactionClass.INSTRUMENT_PL:
            #     t.currency = t.settlement_currency
            #     t.currency_history = self.find_currency_history(t.settlement_currency, self.instance.end_date)

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
                            t.avco_multiplier += abs(
                                (1. - t.avco_multiplier) * position_size_with_sign / rolling_position)
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
                            t.avco_multiplier += abs(
                                (1. - t.avco_multiplier) * position_size_with_sign / rolling_position)
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
                            t.fifo_multiplier = abs((t.position_size_with_sign - t.balance) / t.position_size_with_sign)
                            sale = 0.
                        else:
                            t.balance = 0.
                            t.fifo_multiplier = 1.
                            sale += abs(balance)
                        if sale >= 0.:
                            break
                    in_stock[instrument] = [t for t in instrument_in_stock if t.fifo_multiplier < 1.]
                transaction.not_closed = sale
                transaction.fifo_multiplier = abs((position_size_with_sign - sale) / position_size_with_sign)
                if transaction.fifo_multiplier < 1.:
                    for_sale[instrument] = for_sale.get(instrument, []) + [transaction]

            rolling_position += position_size_with_sign
            transaction.rolling_position = rolling_position
