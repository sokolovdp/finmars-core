from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import python_2_unicode_compatible

from poms.users.models import MasterUser


# ----------------------------------------------------------------------------------------------------------------------


@python_2_unicode_compatible
class BaseReportItem(object):
    def __init__(self, pk=None):
        self.pk = pk

    def __str__(self):
        return "%s #%s" % (self.__class__.__name__, self.pk,)


@python_2_unicode_compatible
class BaseReport(object):
    def __init__(self, master_user=None, begin_date=None, end_date=None, instruments=None, results=None):
        self.master_user = master_user
        self.begin_date = begin_date
        self.end_date = end_date
        self.instruments = instruments
        self.results = results

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
            return "%s - %s" % (self.instrument, self.position_size_with_sign)
        else:
            return "%s - %s" % (self.currency, self.position_size_with_sign)

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
    def market_value_system_ccy(self):
        if self.instrument:
            return self.principal_value_intrument_principal_ccy * self.instrument_principal_fx_rate + \
                   self.accrued_value_intrument_principal_ccy * self.instrument_accrued_fx_rate
        if self.currency:
            return self.balance_position * self.currency_fx_rate
        return 0.


@python_2_unicode_compatible
class BalanceReportSummary(object):
    def __init__(self, invested_value=0., current_value=0., p_and_l=0.):
        self.invested_value = invested_value
        self.current_value = current_value
        self.p_and_l = p_and_l

    def __str__(self):
        return "%s: invested=%s, current=%s, p_and_l=%s" % \
               (self.currency, self.invested_value, self.current_value, self.p_and_l)


# @python_2_unicode_compatible
class BalanceReport(BaseReport):
    def __init__(self, currency=None, summary=None, *args, **kwargs):
        super(BalanceReport, self).__init__(*args, **kwargs)
        self.currency = currency
        self.summary = summary


# ----------------------------------------------------------------------------------------------------------------------


@python_2_unicode_compatible
class PLReportItem(BaseReportItem):
    def __init__(self, *args, **kwargs):
        super(PLReportItem, self).__init__(*args, **kwargs)

    def __str__(self):
        return 'PLReportItem'


# @python_2_unicode_compatible
class PLReport(BaseReport):
    def __init__(self, *args, **kwargs):
        super(PLReport, self).__init__(*args, **kwargs)
