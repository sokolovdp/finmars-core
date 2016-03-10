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
    def __init__(self, instrument=None, currency=None, position_size_with_sign=0., *args, **kwargs):
        super(BalanceReportItem, self).__init__(*args, **kwargs)
        self.instrument = instrument
        self.currency = currency
        self.position_size_with_sign = position_size_with_sign  # -> position

        # [09.03.16, 17:26:30] Instrument - name
        # [09.03.16, 17:27:03] Position
        # [09.03.16, 17:27:28] Inst Ccy - name
        # [09.03.16, 17:27:40] Inst Price Multiplier
        # [09.03.16, 17:29:19] Price (Price hist + date)
        # [09.03.16, 17:29:36] Acctrued Multiplier (price hist + date)
        # [09.03.16, 17:31:18] Principal, loc ccy
        # [09.03.16, 17:32:06] Accrue, loc ccy
        # [09.03.16, 17:32:51] FX rate (instrm ccy + fx hist + date)
        # [09.03.16, 17:35:38] Principal, $
        # [09.03.16, 17:35:49] Accrued, $
        # [09.03.16, 17:36:15] Mkt Value, $ = Principla + Accrued
        # [09.03.16, 17:36:27] SUM (Mkt Value, $)

    def __str__(self):
        if self.instrument:
            return "%s - %s" % (self.instrument, self.position_size_with_sign)
        else:
            return "%s - %s" % (self.currency, self.position_size_with_sign)


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
