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
        self.currency_name = None
        self.currency_fx_rate = 0.

        self.instrument = instrument
        self.price_history = None  # -> PriceHistory
        self.instrument_principal_currency_history = None  # -> CurrencyHistory
        self.instrument_accrued_currency_history = None  # -> CurrencyHistory
        self.instrument_name = None
        self.instrument_principal_pricing_ccy = None
        self.instrument_price_multiplier = None
        self.instrument_accrued_pricing_ccy = None
        self.instrument_accrued_multiplier = None
        self.instrument_principal_price = None
        self.instrument_accrued_price = None
        self.principal_value_instrument_principal_ccy = None
        self.accrued_value_intsrument_principal_ccy = None
        self.instrument_principal_fx_rate = None
        self.instrument_accrued_fx_rate = None

        self.principal_value_instrument_system_ccy = None
        self.accrued_value_instrument_system_ccy = None
        self.market_value_system_ccy = None

    def __str__(self):
        if self.instrument:
            return "%s - %s" % (self.instrument, self.balance_position)
        else:
            return "%s - %s" % (self.currency, self.balance_position)


@python_2_unicode_compatible
class BalanceReportSummary(object):
    def __init__(self, report):
        self.report = report
        self.invested_value_system_ccy = 0.
        self.current_value_system_ccy = 0.
        self.p_l_system_ccy = 0.

    def __str__(self):
        return "invested_value_system_ccy=%s, current_value_system_ccy=%s, p_l_system_ccy=%s" % \
               (self.invested_value_system_ccy, self.current_value_system_ccy, self.p_l_system_ccy)


# @python_2_unicode_compatible
class BalanceReport(BaseReport):
    def __init__(self, currency=None, summary=None, *args, **kwargs):
        super(BalanceReport, self).__init__(*args, **kwargs)
        self.summary = BalanceReportSummary(self)
        self.invested_items = None


# ----------------------------------------------------------------------------------------------------------------------


@python_2_unicode_compatible
class PLReportInstrument(BaseReportItem):
    def __init__(self, instrument=None, *args, **kwargs):
        super(PLReportInstrument, self).__init__(pk=getattr(instrument, 'pk', None), *args, **kwargs)
        self.instrument = instrument
        self.principal_with_sign_system_ccy = 0.
        self.carry_with_sign_system_ccy = 0.
        self.overheads_with_sign_system_ccy = 0.
        self.total_system_ccy = 0.

    def __str__(self):
        return 'PLReportItem'

    # @property
    # def instrument_name(self):
    #     return getattr(self.instrument, 'name', None)

    # def total_system_ccy(self):
    #     return self.principal_with_sign_system_ccy + self.carry_with_sign_system_ccy + self.overheads_with_sign_system_ccy


class PLReportSummary(object):
    def __init__(self, *args, **kwargs):
        self.principal_with_sign_system_ccy = 0.
        self.carry_with_sign_system_ccy = 0.
        self.overheads_with_sign_system_ccy = 0.
        self.total_system_ccy = 0.

    # @property
    # def total_system_ccy(self):
    #     return self.principal_with_sign_system_ccy + self.carry_with_sign_system_ccy + self.overheads_with_sign_system_ccy


# @python_2_unicode_compatible
class PLReport(BaseReport):
    def __init__(self, *args, **kwargs):
        super(PLReport, self).__init__(*args, **kwargs)
        self.transactions = []
        self.items = []
        self.summary = PLReportSummary()


# ----------------------------------------------------------------------------------------------------------------------


class CostReportInstrument(BaseReportItem):
    def __init__(self, instrument=None, *args, **kwargs):
        super(CostReportInstrument, self).__init__(pk=getattr(instrument, 'pk', None), *args, **kwargs)
        self.instrument = instrument
        self.position = 0.
        self.cost_system_ccy = 0.
        self.cost_instrument_ccy = 0.
        self.cost_price_adjusted = 0.


# @python_2_unicode_compatible
class CostReport(BaseReport):
    def __init__(self, multiplier_class=None, *args, **kwargs):
        super(CostReport, self).__init__(*args, **kwargs)
        self.multiplier_class = multiplier_class
        self.transactions = []

