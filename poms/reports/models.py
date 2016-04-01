from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import python_2_unicode_compatible

from poms.users.models import MasterUser

MULTIPLIER_AVCO = 1
MULTIPLIER_FIFO = 2
# MULTIPLIER_LIFO = 3
MULTIPLIERS = (
    (MULTIPLIER_AVCO, 'avco'),
    (MULTIPLIER_FIFO, 'fifo'),
    # (LIFO, 'lifo'),
)


# ----------------------------------------------------------------------------------------------------------------------


@python_2_unicode_compatible
class BaseReportItem(object):
    def __init__(self, pk=None, portfolio=None, account=None, strategies=None, instrument=None, name=None):
        self.pk = pk
        self.portfolio = portfolio  # -> Portfolio
        self.account = account  # -> Account
        self.strategies = strategies  # -> sorted strategy list
        self.instrument = instrument  # -> Instrument
        self.name = name

    def __str__(self):
        return "%s #%s" % (self.__class__.__name__, self.pk,)


@python_2_unicode_compatible
class BaseReport(object):
    def __init__(self, master_user=None, begin_date=None, end_date=None, use_portfolio=None, use_account=None,
                 use_strategy=False, multiplier_class=None, items=None, instruments=None, transaction_currencies=None):
        self.master_user = master_user
        self.begin_date = begin_date
        self.end_date = end_date
        self.use_portfolio = use_portfolio
        self.use_account = use_account
        self.use_strategy = use_strategy
        self.multiplier_class = multiplier_class
        self.items = items
        self.transaction_currencies = transaction_currencies
        self.instruments = instruments
        self.transactions = []

    def __str__(self):
        return "%s for %s (%s, %s)" % (self.__class__.__name__, self.master_user, self.begin_date, self.end_date)


# ----------------------------------------------------------------------------------------------------------------------


@python_2_unicode_compatible
class BalanceReportItem(BaseReportItem):
    def __init__(self, currency=None, balance_position=0., market_value_system_ccy=0., transaction=None, *args,
                 **kwargs):
        super(BalanceReportItem, self).__init__(*args, **kwargs)
        self.balance_position = balance_position

        self.currency = currency
        self.currency_history = None  # -> CurrencyHistory
        self.currency_name = None
        self.currency_fx_rate = 0.

        self.price_history = None  # -> PriceHistory
        self.instrument_principal_currency_history = None  # -> CurrencyHistory
        self.instrument_accrued_currency_history = None  # -> CurrencyHistory
        # self.instrument_name = None
        self.instrument_principal_pricing_ccy = 0.
        self.instrument_price_multiplier = 0.
        self.instrument_accrued_pricing_ccy = 0.
        self.instrument_accrued_multiplier = 0.
        self.instrument_principal_price = 0.
        self.instrument_accrued_price = 0.
        self.principal_value_instrument_principal_ccy = None
        self.accrued_value_instrument_accrued_ccy = None
        self.instrument_principal_fx_rate = 0.
        self.instrument_accrued_fx_rate = 0.

        self.principal_value_system_ccy = 0.
        self.accrued_value_system_ccy = 0.
        self.market_value_system_ccy = market_value_system_ccy

        self.transaction = transaction  # -> Transaction for case 1 and case 2

    def __str__(self):
        if self.instrument:
            return "%s - %s" % (self.instrument, self.balance_position)
        else:
            return "%s - %s" % (self.currency, self.balance_position)


@python_2_unicode_compatible
class BalanceReportSummary(object):
    def __init__(self, invested_value_system_ccy=0., current_value_system_ccy=0., p_l_system_ccy=0.):
        self.invested_value_system_ccy = invested_value_system_ccy
        self.current_value_system_ccy = current_value_system_ccy
        self.p_l_system_ccy = p_l_system_ccy

    def __str__(self):
        return "invested_value_system_ccy=%s, current_value_system_ccy=%s, p_l_system_ccy=%s" % \
               (self.invested_value_system_ccy, self.current_value_system_ccy, self.p_l_system_ccy)


# @python_2_unicode_compatible
class BalanceReport(BaseReport):
    def __init__(self, show_transaction_details=True, items=None, summary=None, *args, **kwargs):
        super(BalanceReport, self).__init__(items=items, *args, **kwargs)
        self.show_transaction_details = show_transaction_details
        self.invested_items = []
        self.summary = summary or BalanceReportSummary()


# ----------------------------------------------------------------------------------------------------------------------


@python_2_unicode_compatible
class PLReportItem(BaseReportItem):
    def __init__(self, principal_with_sign_system_ccy=0, carry_with_sign_system_ccy=0.,
                 overheads_with_sign_system_ccy=0., total_system_ccy=0., *args, **kwargs):
        super(PLReportItem, self).__init__(*args, **kwargs)
        self.principal_with_sign_system_ccy = principal_with_sign_system_ccy
        self.carry_with_sign_system_ccy = carry_with_sign_system_ccy
        self.overheads_with_sign_system_ccy = overheads_with_sign_system_ccy
        self.total_system_ccy = total_system_ccy

    def __str__(self):
        return 'PLReportItem'


class PLReportSummary(object):
    def __init__(self, principal_with_sign_system_ccy=0., carry_with_sign_system_ccy=0.,
                 overheads_with_sign_system_ccy=0., total_system_ccy=0.):
        self.principal_with_sign_system_ccy = principal_with_sign_system_ccy
        self.carry_with_sign_system_ccy = carry_with_sign_system_ccy
        self.overheads_with_sign_system_ccy = overheads_with_sign_system_ccy
        self.total_system_ccy = total_system_ccy


# @python_2_unicode_compatible
class PLReport(BaseReport):
    def __init__(self, summary=None, *args, **kwargs):
        super(PLReport, self).__init__(*args, **kwargs)
        self.summary = summary or PLReportSummary()


# ----------------------------------------------------------------------------------------------------------------------


class CostReportItem(BaseReportItem):
    def __init__(self, position=0., cost_price=0., cost_price_adjusted=0., cost_system_ccy=0., cost_instrument_ccy=0.,
                 *args, **kwargs):
        super(CostReportItem, self).__init__(*args, **kwargs)
        self.position = position
        self.cost_price = cost_price,
        self.cost_price_adjusted = cost_price_adjusted
        self.cost_instrument_ccy = cost_instrument_ccy
        self.cost_system_ccy = cost_system_ccy


# @python_2_unicode_compatible
class CostReport(BaseReport):
    def __init__(self, *args, **kwargs):
        super(CostReport, self).__init__(*args, **kwargs)


# ----------------------------------------------------------------------------------------------------------------------


class YTMReportItem(BaseReportItem):
    def __init__(self, position=0., ytm=0., time_invested=0., *args, **kwargs):
        super(YTMReportItem, self).__init__(*args, **kwargs)
        self.position = position
        self.ytm = ytm
        self.time_invested = time_invested


# @python_2_unicode_compatible
class YTMReport(BaseReport):
    def __init__(self, *args, **kwargs):
        super(YTMReport, self).__init__(*args, **kwargs)
