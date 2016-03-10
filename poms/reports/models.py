from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import python_2_unicode_compatible

from poms.users.models import MasterUser


# ----------------------------------------------------------------------------------------------------------------------


@python_2_unicode_compatible
class BaseReportItem(object):
    def __init__(self, pk=None, *args, **kwargs):
        self.pk = pk

    def __str__(self):
        return "%s #%s" % (self.__class__.__name__, self.pk,)


@python_2_unicode_compatible
class BaseReport(object):
    def __init__(self, master_user=None, begin_date=None, end_date=None, instruments=None, items=None):
        self.master_user = master_user
        self.begin_date = begin_date
        self.end_date = end_date
        self.instruments = instruments
        self.items = items

    def __str__(self):
        return "%s for %s (%s, %s)" % (self.__class__.__name__, self.master_user, self.begin_date, self.end_date)


# ----------------------------------------------------------------------------------------------------------------------


@python_2_unicode_compatible
class BalanceReportItem(BaseReportItem):
    def __init__(self, instrument=None, currency=None, balance_position=0., *args, **kwargs):
        super(BalanceReportItem, self).__init__(*args, **kwargs)
        self.balance_position = balance_position

        self.currency = currency
        self.currency_history = None  # -> CurrencyHistory

        self.instrument = instrument
        self.price_history = None  # -> PriceHistory
        self.instrument_principal_currency_history = None  # -> CurrencyHistory
        self.instrument_accrued_currency_history = None  # -> CurrencyHistory

    def __str__(self):
        if self.instrument:
            return "%s - %s" % (self.instrument, self.balance_position)
        else:
            return "%s - %s" % (self.currency, self.balance_position)

    @property
    def currency_name(self):
        return getattr(self.currency, 'name', None)
        # return instance.currency.name if instance.currency else None

    @property
    def currency_fx_rate(self):
        if getattr(self.currency, 'is_system', False):
            return 1.
        return getattr(self.currency_history, 'fx_rate', 0.) or 0.

    @property
    def instrument_name(self):
        return getattr(self.instrument, 'name', None)
        # return instance.instrument.name if instance.instrument else None

    @property
    def instrument_principal_pricing_ccy(self):
        c = getattr(self.instrument, 'pricing_currency', None)
        return getattr(c, 'name', None)

    @property
    def instrument_price_multiplier(self):
        return getattr(self.instrument, 'price_multiplier', 1.) or 1.

    @property
    def instrument_accrued_pricing_ccy(self):
        c = getattr(self.instrument, 'accrued_currency', None)
        return getattr(c, 'name', None)

    @property
    def instrument_accrued_multiplier(self):
        return getattr(self.instrument, 'accrued_multiplier', 1.) or 1.

    @property
    def instrument_principal_price(self):
        return getattr(self.price_history, 'principal_price', 0.) or 0.

    @property
    def instrument_accrued_price(self):
        return getattr(self.price_history, 'accrued_price', 0.) or 0.

    @property
    def principal_value_intrument_principal_ccy(self):
        return self.instrument_price_multiplier * self.balance_position * self.instrument_principal_price

    @property
    def accrued_value_intrument_principal_ccy(self):
        return self.instrument_accrued_multiplier * self.balance_position * self.instrument_accrued_price

    @property
    def instrument_principal_fx_rate(self):
        if getattr(self.instrument_principal_currency_history, 'is_system', False):
            return 1.
        return getattr(self.instrument_principal_currency_history, 'fx_rate', 0.) or 0.

    @property
    def instrument_accrued_fx_rate(self):
        if getattr(self.instrument_accrued_currency_history, 'is_system', False):
            return 1.
        return getattr(self.instrument_accrued_currency_history, 'fx_rate', 0.) or 0.

    @property
    def principal_value_instrument_system_ccy(self):
        if self.instrument:
            return self.principal_value_intrument_principal_ccy * self.instrument_principal_fx_rate
        if self.currency:
            return self.balance_position * self.currency_fx_rate
        return 0.

    @property
    def accrued_value_instrument_system_ccy(self):
        if self.instrument:
            return self.accrued_value_intrument_principal_ccy * self.instrument_accrued_fx_rate
        return 0.

    @property
    def market_value_system_ccy(self):
        # if self.instrument:
        #     return self.principal_value_intrument_principal_ccy * self.instrument_principal_fx_rate + \
        #            self.accrued_value_intrument_principal_ccy * self.instrument_accrued_fx_rate
        # if self.currency:
        #     return self.balance_position * self.currency_fx_rate
        # return 0.
        return self.principal_value_instrument_system_ccy + self.accrued_value_instrument_system_ccy


@python_2_unicode_compatible
class BalanceReportSummary(object):
    def __init__(self, report):
        self.report = report
        # self.invested_value_system_ccy = 0.
        # self.current_value_system_ccy = -1132

    def __str__(self):
        return "invested_value_system_ccy=%s, current_value_system_ccy=%s, p_l_system_ccy=%s" % \
               (self.invested_value_system_ccy, self.current_value_system_ccy, self.p_l_system_ccy)

    @property
    def invested_value_system_ccy(self):
        v = 0.
        if self.report.invested_items:
            for i in self.report.invested_items:
                v += i.market_value_system_ccy
        return v

    @property
    def current_value_system_ccy(self):
        v = 0.
        if self.report.items:
            for i in self.report.items:
                v += i.market_value_system_ccy
        return v

    @property
    def p_l_system_ccy(self):
        return self.current_value_system_ccy - self.invested_value_system_ccy


# @python_2_unicode_compatible
class BalanceReport(BaseReport):
    def __init__(self, currency=None, summary=None, *args, **kwargs):
        super(BalanceReport, self).__init__(*args, **kwargs)
        self.summary = BalanceReportSummary(self)
        self.invested_items = None


# ----------------------------------------------------------------------------------------------------------------------


@python_2_unicode_compatible
class PLReportTransaction(BaseReportItem):
    def __init__(self, transaction, *args, **kwargs):
        super(PLReportTransaction, self).__init__(*args, **kwargs)
        self._transaction = transaction
        self.pk = transaction.id
        self.currency = None
        self.currency_history = None

    def __str__(self):
        return 'transaction=%s' % self.transaction.id

    @property
    def transaction_class(self):
        return getattr(self._transaction, 'transaction_class', None)

    @property
    def transaction_class_code(self):
        return getattr(self.transaction_class, 'code', None)

    @property
    def instrument(self):
        return getattr(self._transaction, 'instrument', None)

    @property
    def instrument_name(self):
        return getattr(self.instrument, 'name', None)

    @property
    def transaction_currency(self):
        return getattr(self._transaction, 'transaction_currency', None)

    @property
    def transaction_currency_name(self):
        return getattr(self.transaction_currency, 'name', None)

    @property
    def position_size_with_sign(self):
        return getattr(self._transaction, 'position_size_with_sign', 0.)

    @property
    def cash_consideration(self):
        return getattr(self._transaction, 'cash_consideration', 0.)

    @property
    def principal_with_sign(self):
        return getattr(self._transaction, 'principal_with_sign', 0.)

    @property
    def carry_with_sign(self):
        return getattr(self._transaction, 'carry_with_sign', 0.)

    @property
    def overheads_with_sign(self):
        return getattr(self._transaction, 'overheads_with_sign', 0.)

    @property
    def currency_name(self):
        return getattr(self.currency, 'name', None)

    @property
    def currency_fx_rate(self):
        if getattr(self.currency, 'is_system', False):
            return 1.
        return getattr(self.currency_history, 'fx_rate', 0.) or 0.

    @property
    def principal_with_sign_system_ccy(self):
        return self.principal_with_sign * self.currency_fx_rate

    @property
    def carry_with_sign_system_ccy(self):
        return self.carry_with_sign * self.currency_fx_rate

    @property
    def overheads_with_sign_system_ccy(self):
        return self.overheads_with_sign * self.currency_fx_rate


@python_2_unicode_compatible
class PLReportInstrument(BaseReportItem):
    def __init__(self, instrument=None, *args, **kwargs):
        super(PLReportInstrument, self).__init__(pk=getattr(instrument, 'pk', None), *args, **kwargs)
        self.instrument = instrument
        self.principal_with_sign_system_ccy = 0.
        self.carry_with_sign_system_ccy = 0.
        self.overheads_with_sign_system_ccy = 0.

    def __str__(self):
        return 'PLReportItem'

    @property
    def instrument_name(self):
        return getattr(self.instrument, 'name', None)

    def total_system_ccy(self):
        return self.principal_with_sign_system_ccy + self.carry_with_sign_system_ccy + self.overheads_with_sign_system_ccy


class PLReportSummary(object):
    def __init__(self, *args, **kwargs):
        self.principal_with_sign_system_ccy = 0.
        self.carry_with_sign_system_ccy = 0.
        self.overheads_with_sign_system_ccy = 0.

    @property
    def total_system_ccy(self):
        return self.principal_with_sign_system_ccy + self.carry_with_sign_system_ccy + self.overheads_with_sign_system_ccy


# @python_2_unicode_compatible
class PLReport(BaseReport):
    def __init__(self, *args, **kwargs):
        super(PLReport, self).__init__(*args, **kwargs)
        self.transactions = []
        self.items = []
        self.summary = PLReportSummary()
