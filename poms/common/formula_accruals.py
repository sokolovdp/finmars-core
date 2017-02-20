from __future__ import unicode_literals, division

import calendar
from datetime import date, timedelta

from dateutil import relativedelta, rrule


def coupon_accrual_factor(
        accrual_calculation_schedule=None,
        accrual_calculation_model=None, periodicity=None, periodicity_n=None,
        dt1=None, dt2=None, dt3=None, maturity_date=None):
    from poms.instruments.models import AccrualCalculationModel

    # day_convention_code - accrual_calculation_model
    # freq
    # dt1 - first accrual date - берется из AccrualCalculationSchedule
    # dt2 - дата на которую идет расчет accrued interest
    # dt3 - first coupon date - берется из AccrualCalculationSchedule
    # maturity_date - instrument.maturity_date

    if accrual_calculation_schedule:
        accrual_calculation_model = accrual_calculation_schedule.accrual_calculation_model
        periodicity = accrual_calculation_schedule.periodicity
        periodicity_n = accrual_calculation_schedule.periodicity_n
        if maturity_date is None:
            maturity_date = accrual_calculation_schedule.instrument.maturity_date

    # if isinstance(accrual_calculation_model, AccrualCalculationModel):
    #     accrual_calculation_model = accrual_calculation_model.id

    # if isinstance(periodicity, Periodicity):
    #     periodicity = periodicity.id

    if accrual_calculation_model is None or periodicity is None or dt1 is None or dt2 is None or dt3 is None:
        return 0.0

    # k = 0
    # If freq > 0 And freq <= 12 Then
    #     While DateAdd("m", 12 / freq * k, dt3) <= dt2
    #         k = k + 1
    #     Wend
    #     dt3 = DateAdd("m", 12 / freq * k, dt3)
    #     If k > 0 Then dt1 = DateAdd("m", -12 / freq, dt3)
    #     If Not IsNull(MaturityDate) Then If dt3 >= MaturityDate And dt2 < MaturityDate Then dt3 = MaturityDate
    #
    # ElseIf freq >= 12 Then
    #     MsgBox ("Cpn Frequency over '12'. This situation is not handled in the 'CaouponAccrualFactor' code!!!")
    #     CouponAccrualFactor = 0
    #     Exit Function
    # ElseIf freq = 0 Then
    #         freq = 1
    #         dt3 = DateAdd("m", 12, dt1)
    # Else
    #     dt3 = MaturityDate
    # End If

    freq = periodicity.to_freq()

    if 0 < freq <= 12:
        # k = 0
        # while (dt3 + relativedelta.relativedelta(months=12 / freq * k)) <= dt2:
        #     k += 1
        # dt3 += relativedelta.relativedelta(months=12 / freq * k)
        # if k > 0:
        #     dt1 = dt3 + relativedelta.relativedelta(months=-12 / freq)
        # if maturity_date is not None:
        #     if dt3 >= maturity_date > dt2:
        #         dt3 = maturity_date

        k = 0
        while (dt3 + periodicity.to_timedelta(k)) <= dt2:
            k += 1
        dt3 += periodicity.to_timedelta(k)
        if k > 0:
            dt1 = dt3 - periodicity.to_timedelta(1)
        if maturity_date is not None:
            if dt3 >= maturity_date > dt2:
                dt3 = maturity_date

    elif freq >= 12:
        return 0.0
    elif freq == 0:
        freq = 1
        dt3 = dt1 + relativedelta.relativedelta(years=1)
    else:
        dt3 = maturity_date

    if accrual_calculation_model.id == AccrualCalculationModel.NONE:  # 1
        # Case 0  'none
        #     CouponAccrualFactor = 0
        return 0.0
    elif accrual_calculation_model.id == AccrualCalculationModel.ACT_ACT:  # 2
        # Case 1  'ACT/ACT
        #     CouponAccrualFactor = (dt2 - dt1) / (dt3 - dt1) / freq
        return (dt2 - dt1).days / (dt3 - dt1).days / freq
    elif accrual_calculation_model.id == AccrualCalculationModel.ACT_ACT_ISDA:  # 3
        # Case 100  'ACT/ACT  - ISDA
        #     Ndays1 = DateSerial(y1, 1, 1) - DateSerial(y1, 12, 31)
        #     Ndays2 = DateSerial(y2, 1, 1) - DateSerial(y2, 12, 31)
        #     Y1_leap = Month(DateSerial(Year(dt1), 2, 29)) = 2
        #     Y2_leap = Month(DateSerial(Year(dt2), 2, 29)) = 2
        #     If Y1_leap <> Y2_leap Then
        #         CouponAccrualFactor = (DateSerial(y2, 1, 1) - dt1) / Ndays1 + (dt2 - DateSerial(y2, 1, 1)) / Ndays2
        #     Else
        #         CouponAccrualFactor = (dt2 - dt1) / 365
        #     End If
        ndays1 = (date(dt1.year, 1, 1) - date(dt1.year, 12, 31)).days
        ndays2 = (date(dt2.year, 1, 1) - date(dt2.year, 12, 31)).days
        is_leap1 = calendar.isleap(dt1.year)
        is_leap2 = calendar.isleap(dt2.year)
        if is_leap1 != is_leap2:
            return (date(dt2.year, 1, 1) - dt1).days / ndays1 + (dt2 - date(dt2.year, 1, 1)).days / ndays2
        else:
            return (dt2 - dt1).days / 365
    elif accrual_calculation_model.id == AccrualCalculationModel.ACT_360:  # 4
        # Case 2  'ACT/360
        #     CouponAccrualFactor = (dt2 - dt1) / 360
        return (dt2 - dt1).days / 360
    elif accrual_calculation_model.id == AccrualCalculationModel.ACT_365:  # 5
        # Case 3  'ACT/365
        #     CouponAccrualFactor = (dt2 - dt1) / 365
        return (dt2 - dt1).days / 365
    elif accrual_calculation_model.id == AccrualCalculationModel.ACT_365_25:  # 6
        # Case 106  'Act/365.25
        #     CouponAccrualFactor = (dt2 - dt1) / 365.25
        return (dt2 - dt1).days / 365.25
    elif accrual_calculation_model.id == AccrualCalculationModel.ACT_365_366:  # 7
        # Case 107  'Act/365(366)
        #     If y1 < y2 Then
        #         If (Month(DateSerial(y1, 2, 29)) = 2 Or Month(DateSerial(y2, 2, 29)) = 2) And _
        #                 DateSerial(y1, 2, 29) >= dt1 And DateSerial(y1, 2, 29) <= dt2 Then
        #             CouponAccrualFactor = (dt2 - dt1 + 1) / 366
        #         Else
        #             CouponAccrualFactor = (dt2 - dt1 + 1) / 365
        #         End If
        #     End If
        if dt1.year < dt2.year:
            # TODO: verify
            is_leap1 = calendar.isleap(dt1.year)
            is_leap2 = calendar.isleap(dt2.year)
            if (is_leap1 or is_leap2) and dt1 <= (date(dt1.year, 2, 28) + timedelta(days=1)) <= dt2:
                return ((dt2 - dt1).days + 1) / 366
            else:
                return ((dt2 - dt1).days + 1) / 365
        return 0
    elif accrual_calculation_model.id == AccrualCalculationModel.ACT_1_365:  # 8
        # Case 104  'Act+1/365
        #     CouponAccrualFactor = (dt2 - dt1 + 1) / 365
        return ((dt2 - dt1).days + 1) / 365
    elif accrual_calculation_model.id == AccrualCalculationModel.ACT_1_360:  # 9
        # CouponAccrualFactor = (dt2 - dt1 + 1) / 360
        return ((dt2 - dt1).days + 1) / 360
    elif accrual_calculation_model.id == AccrualCalculationModel.C_30_360:  # 11
        # Case 5  '30/360
        #     If d1 = 31 Then d1 = 30
        #     If d2 = 31 And (d1 = 30 Or d1 = 31) Then d2 = 30
        #     CouponAccrualFactor = ((y2 - y1) * 360 + (M2 - M1) * 30 + (d2 - d1)) / 360
        d1 = dt1.day
        d2 = dt2.day
        if d1 == 31:
            d1 = 30
        if d2 == 31 and (d1 == 30 or d1 == 31):
            d2 = 30
        return ((dt2.year - dt1.year) * 360 + (dt2.month - dt1.month) * 30 + (d2 - d1)) / 360
    elif accrual_calculation_model.id == AccrualCalculationModel.C_30_360_NO_EOM:  # 12
        # Case 14  '30/360 (NO EOM)
        #     If d1 = 31 Then d1 = 30
        #     If d2 = 31 And (d1 = 30 Or d1 = 31) Then d2 = 30
        #     CouponAccrualFactor = ((y2 - y1) * 360 + (M2 - M1) * 30 + (d2 - d1)) / 360
        d1 = dt1.day
        d2 = dt2.day
        if d1 == 31:
            d1 = 30
        if d2 == 31 and (d1 == 30 or d1 == 31):
            d2 = 30
        return ((dt2.year - dt1.year) * 360 + (dt2.month - dt1.month) * 30 + (d2 - d1)) / 360
    elif accrual_calculation_model.id == AccrualCalculationModel.C_30E_P_360:  # 24
        # Case 101  '30E+/360
        #     If d1 = 31 Then d1 = 30
        #     If d2 = 31 Then
        #     M2 = M2 + 1
        #     d2 = 1
        #     End If
        #     CouponAccrualFactor = ((y2 - y1) * 360 + (M2 - M1) * 30 + (d2 - d1)) / 360
        d1 = dt1.day
        d2 = dt2.day
        m1 = dt1.month
        m2 = dt1.month
        if d1 == 31:
            d1 = 30
        if d2 == 31:
            m2 += 1
            d2 = 1
        return ((dt2.year - dt1.year) * 360 + (m2 - m1) * 30 + (d2 - d1)) / 360
    elif accrual_calculation_model.id == AccrualCalculationModel.C_30E_P_360_ITL:  # 13
        # Case 102  '30E+/360.ITL
        #     If d1 = 31 Then d1 = 30
        #     If d2 = 31 Then d2 = 30
        #     CouponAccrualFactor = ((y2 - y1) * 360 + (M2 - M1) * 30 + (d2 - d1 + 1)) / 360
        d1 = dt1.day
        d2 = dt2.day
        if d1 == 31:
            d1 = 30
        if d2 == 31:
            d2 = 30
        return ((dt2.year - dt1.year) * 360 + (dt2.month - dt1.month) * 30 + (d2 - d1 + 1)) / 360
    elif accrual_calculation_model.id == AccrualCalculationModel.NL_365:  # 14
        # Case 9  'NL/365
        #     Y1_leap = Month(DateSerial(Year(dt1), 2, 29)) = 2
        #     Y2_leap = Month(DateSerial(Year(dt2), 2, 29)) = 2
        #     k = 0
        #     If Y1_leap And dt1 < DateSerial(Year(dt1), 2, 29) And dt2 >= DateSerial(Year(dt1), 2, 29) Then k = 1
        #     If Y2_leap And dt2 >= DateSerial(Year(dt2), 2, 29) And dt1 < DateSerial(Year(dt2), 2, 29) Then k = 1
        #     CouponAccrualFactor = (dt2 - dt1 - k) / 365
        is_leap1 = calendar.isleap(dt1.year)
        is_leap2 = calendar.isleap(dt2.year)
        k = 0
        if is_leap1 and dt1 < date(dt1.year, 2, 29) <= dt2:
            k = 1
        if is_leap2 and dt2 >= date(dt2.year, 2, 29) > dt1:
            k = 1
        return ((dt2 - dt1).days - k) / 365
    elif accrual_calculation_model.id == AccrualCalculationModel.NL_365_NO_EOM:  # 15
        # Case 18  'NL/365 (NO-EOM)
        #     Y1_leap = Month(DateSerial(Year(dt1), 2, 29)) = 2
        #     Y2_leap = Month(DateSerial(Year(dt2), 2, 29)) = 2
        #     k = 0
        #     If Y1_leap And dt1 < DateSerial(Year(dt1), 2, 29) And dt2 >= DateSerial(Year(dt1), 2, 29) Then k = 1
        #     If Y2_leap And dt2 >= DateSerial(Year(dt2), 2, 29) And dt1 < DateSerial(Year(dt2), 2, 29) Then k = 1
        #     CouponAccrualFactor = (dt2 - dt1 - k) / 365
        is_leap1 = calendar.isleap(dt1.year)
        is_leap2 = calendar.isleap(dt2.year)
        k = 0
        if is_leap1 and dt1 < date(dt1.year, 2, 29) <= dt2:
            k = 1
        if is_leap2 and dt2 >= date(dt2.year, 2, 29) > dt1:
            k = 1
        return ((dt2 - dt1).days - k) / 365
    elif accrual_calculation_model.id == AccrualCalculationModel.ISMA_30_360:  # 16
        # Case 20  'ISMA-30/360 = 30E/360
        #     If d1 = 31 Then d1 = 30
        #     If d2 = 31 Then d2 = 30
        #     CouponAccrualFactor = ((y2 - y1) * 360 + (M2 - M1) * 30 + (d2 - d1)) / 360
        d1 = dt1.day
        d2 = dt2.day
        if d1 == 31:
            d1 = 30
        if d2 == 31:
            d2 = 30
        return ((dt2.year - dt1.year) * 360 + (dt2.month - dt1.month) * 30 + (d2 - d1)) / 360
    elif accrual_calculation_model.id == AccrualCalculationModel.ISMA_30_360_NO_EOM:  # 17
        # Case 23  'ISMA-30/360 (NO EOM)
        #     If d1 = 31 Then d1 = 30
        #     If d2 = 31 Then d2 = 30
        #     CouponAccrualFactor = ((y2 - y1) * 360 + (M2 - M1) * 30 + (d2 - d1)) / 360
        d1 = dt1.day
        d2 = dt2.day
        if d1 == 31:
            d1 = 30
        if d2 == 31:
            d2 = 30
        return ((dt2.year - dt1.year) * 360 + (dt2.month - dt1.month) * 30 + (d2 - d1)) / 360
    elif accrual_calculation_model.id == AccrualCalculationModel.US_MINI_30_360_EOM:  # 18
        # Case 29  'US MUNI-30/360 (EOM)
        #     If d1 = 31 Then d1 = 30
        #     If d2 = 31 And (d1 = 30 Or d1 = 31) Then d2 = 30
        #     lastDay1 = Month(dt1 + 1) = 3 And Day(dt1 + 1) = 1
        #     lastDay2 = Month(dt2 + 1) = 3 And Day(dt2 + 1) = 1
        #     If lastDay1 Then d1 = 30
        #     If lastDay1 And lastDay2 Then d2 = 30
        #     CouponAccrualFactor = ((y2 - y1) * 360 + (M2 - M1) * 30 + (d2 - d1)) / 360
        d1 = dt1.day
        d2 = dt2.day
        last_day1 = (dt1 + timedelta(days=1)).month == 3 and (dt1 + timedelta(days=1)).day == 1
        last_day2 = (dt2 + timedelta(days=1)).month == 3 and (dt2 + timedelta(days=1)).day == 1
        if last_day1:
            d1 = 30
        if last_day1 and last_day2:
            d2 = 30
        return ((dt2.year - dt1.year) * 360 + (dt2.month - dt1.month) * 30 + (d2 - d1)) / 360
    elif accrual_calculation_model.id == AccrualCalculationModel.US_MINI_30_360_NO_EOM:  # 19
        # Case 32  'US MUNI-30/360 (NO EOM)
        #     If d1 = 31 Then d1 = 30
        #     If d2 = 31 And (d1 = 30 Or d1 = 31) Then d2 = 30
        #     CouponAccrualFactor = ((y2 - y1) * 360 + (M2 - M1) * 30 + (d2 - d1)) / 360
        d1 = dt1.day
        d2 = dt2.day
        if d1 == 31:
            d1 = 30
        if d2 == 31 and (d1 == 30 or d1 == 31):
            d2 = 30
        return ((dt2.year - dt1.year) * 360 + (dt2.month - dt1.month) * 30 + (d2 - d1)) / 360
    elif accrual_calculation_model.id == AccrualCalculationModel.BUS_DAYS_252:  # 20
        # Case 33  'BUS DAYS/252
        #     CouponAccrualFactor = (DateDiff("d", dt1, dt2) - DateDiff("ww", dt1, dt2, vbSaturday) - _
        #         DateDiff("ww", dt1, dt2, vbSunday)) / 252
        return ((dt2 - dt1).days - weekday(dt1, dt2, rrule.SA) - weekday(dt1, dt2, rrule.SU)) / 252
    elif accrual_calculation_model.id == AccrualCalculationModel.GERMAN_30_360_EOM:  # 21
        # Case 35  'GERMAN-30/360 (EOM)
        #     If IsNull(MaturityDate) Then
        #         CouponAccrualFactor = 0
        #         Exit Function
        #     End If
        #     lastDay1 = Month(dt1 + 1) = (Month(dt1) + 1)
        #     lastDay2 = Month(dt1 + 1) = (Month(dt1) + 1)
        #     If lastDay1 Then d1 = 30
        #     If lastDay2 And Not ((dt2 = MaturityDate) And Month(dt2) = 2) Then d2 = 30
        #     CouponAccrualFactor = ((y2 - y1) * 360 + (M2 - M1) * 30 + (d2 - d1)) / 360
        if maturity_date is None:
            return 0
        d1 = dt1.day
        d2 = dt2.day
        last_day1 = (dt1 + timedelta(days=1)).month == (dt1.month + 1)
        last_day2 = (dt2 + timedelta(days=1)).month == (dt2.month + 1)
        if last_day1:
            d1 = 30
        if last_day2 and not ((dt2 == maturity_date) and dt2.month == 2):
            d2 = 30
        return ((dt2.year - dt1.year) * 360 + (dt2.month - dt1.month) * 30 + (d2 - d1)) / 360
    elif accrual_calculation_model.id == AccrualCalculationModel.GERMAN_30_360_NO_EOM:  # 22
        # Case 38  'GERMAN-30/360 (NO EOM)
        #     If IsNull(MaturityDate) Then
        #         CouponAccrualFactor = 0
        #         Exit Function
        #     End If
        #     lastDay1 = Month(dt1 + 1) = (Month(dt1) + 1)
        #     lastDay2 = Month(dt1 + 1) = (Month(dt1) + 1)
        #     If lastDay1 Then d1 = 30
        #     If lastDay2 And Not ((dt2 = MaturityDate) And Month(dt2) = 2) Then d2 = 30
        #     CouponAccrualFactor = ((y2 - y1) * 360 + (M2 - M1) * 30 + (d2 - d1)) / 360
        if maturity_date is None:
            return 0
        d1 = dt1.day
        d2 = dt2.day
        last_day1 = (dt1 + timedelta(days=1)).month == (dt1.month + 1)
        last_day2 = (dt2 + timedelta(days=1)).month == (dt2.month + 1)
        if last_day1:
            d1 = 30
        if last_day2 and not ((dt2 == maturity_date) and dt2.month == 2):
            d2 = 30
        return ((dt2.year - dt1.year) * 360 + (dt2.month - dt1.month) * 30 + (d2 - d1)) / 360
    elif accrual_calculation_model.id == AccrualCalculationModel.REVERSED_ACT_365:  # 23
        # Case 1001  'reversed ACT/365
        #     CouponAccrualFactor = (dt3 - dt2) / 365
        return (dt3 - dt2).days / 365
    return 0.0


# def weeks_fast(dt1, dt2, byweekday):
#     print(-10, dt1, dt1.strftime('%A'), ' - ', dt2, dt2.strftime('%A'), byweekday)
#
#     td = relativedelta.relativedelta(weekday=byweekday)
#
#     dt1w = dt1 + td
#     dt2w = dt2 + td
#
#     count = int((dt2 - dt1).days / 7)
#
#     if dt2w > dt2:
#         count -= 1
#     if dt2w == dt2:
#         count += 1
#
#     print(-11, count)
#
#     return count


def weekday(dt1, dt2, byweekday):
    # print(-20, dt1, dt1.strftime('%A'), ' - ', dt2, dt2.strftime('%A'), byweekday)
    count = 0
    for d in rrule.rrule(rrule.WEEKLY, dtstart=dt1, until=dt2, byweekday=byweekday):
        # print(-20, d, d.strftime('%A'))
        count += 1
    # print(-21, count)
    return count


def f_xnpv(data, rate):
    '''Equivalent of Excel's XNPV function.
    https://support.office.com/en-us/article/XNPV-function-1b42bbf6-370f-4532-a0eb-d67c16b664b7

    >>> from datetime import date
    >>> dates = [date(2016, 2, 16), date(2016, 3, 10), date(2016, 9, 1), date(2017, 1, 17), ]
    >>> values = [-90, 5, 5, 105, ]
    >>> data = [(d, v) for d, v in zip(dates, values)]
    >>> f_xnpv(0.09, data)
    16.7366702148651
    '''
    # _l.debug('xnpv > rate=%s', rate)

    if rate <= -1.0:
        return float('inf')
    d0, v0 = data[0]  # or min(dates)
    return sum(
        vi / ((1.0 + rate) ** ((di - d0).days / 365.0))
        for di, vi in data
    )


def f_xirr(data, x0=0.0, tol=0.0001, maxiter=None, a=-1.0, b=1e10, xtol=0.0001, rtol=0.0001, method=None):
    '''Equivalent of Excel's XIRR function.
    https://support.office.com/en-us/article/XIRR-function-de1242ec-6477-445b-b11b-a303ad9adc9d

    >>> from datetime import date
    >>> dates = [date(2016, 2, 16), date(2016, 3, 10), date(2016, 9, 1), date(2017, 1, 17), ]
    >>> values = [-90, 5, 5, 105, ]
    >>> data = [(d, v) for d, v in zip(dates, values)]
    >>> f_xirr(values, dates)
    0.3291520343150294
    '''

    from scipy.optimize import newton, brentq

    # return newton(lambda r: xnpv(r, values, dates), 0.0), \
    #        brentq(lambda r: xnpv(r, values, dates), -1.0, 1e10)
    # return newton(lambda r: xnpv(r, values, dates), 0.0)
    # return brentq(lambda r: xnpv(r, values, dates), -1.0, 1e10)
    if method == 'newton':
        try:
            kw = {}
            if tol is not None:
                kw['tol'] = tol
            if maxiter is not None:
                kw['maxiter'] = maxiter
            return newton(func=lambda r: f_xnpv(data, r), x0=x0, **kw)
        except RuntimeError:  # Failed to converge?
            pass
    kw = {}
    if xtol is not None:
        kw['xtol'] = xtol
    if rtol is not None:
        kw['rtol'] = rtol
    if maxiter is not None:
        kw['maxiter'] = maxiter
    return brentq(f=lambda r: f_xnpv(data, r), a=a, b=b, **kw)


def f_duration(data, ytm=None):
    # _l.debug('duration >')
    '''Equivalent of Excel's XIRR function.
    https://support.office.com/en-us/article/XIRR-function-de1242ec-6477-445b-b11b-a303ad9adc9d

    >>> from datetime import date
    >>> dates = [date(2016, 2, 16), date(2016, 3, 10), date(2016, 9, 1), date(2017, 1, 17), ]
    >>> values = [-90, 5, 5, 105, ]
    >>> data = [(d, v) for d, v in zip(dates, values)]
    >>> f_xirr(data)
    0.6438341602180792
    '''

    if ytm is None:
        ytm = f_xirr(data)
    d0, v0 = data[0]
    v0 = -v0

    # if _l.isEnabledFor(logging.DEBUG):
    #     discounted_cf = [(vi / ((1 + ytm) ** ((di - d0).days / 365.0)))
    #                      for i, (vi, di) in enumerate(zip(values, dates))
    #                      if i != 0]
    #     dur1 = [((di - d0).days / 365.0) * (vi / ((1 + ytm) ** ((di - d0).days / 365.0)))
    #             for i, (vi, di) in enumerate(zip(values, dates))
    #             if i != 0]
    #     _l.debug('values: %s', values)
    #     _l.debug('dates: %s', dates)
    #     _l.debug('discounted_cf: %s', discounted_cf)
    #     _l.debug('dur1: %s', dur1)

    return sum(
        ((di - d0).days / 365.0) * (vi / ((1 + ytm) ** ((di - d0).days / 365.0)))
        for di, vi in data
    ) / v0 / (1 + ytm)


if __name__ == "__main__":

    # noinspection PyUnresolvedReferences
    import env_ai
    import django

    django.setup()

    from poms.instruments.models import AccrualCalculationModel, Periodicity

    # print('1 -> ', coupon_accrual_factor(
    #     accrual_calculation_model=AccrualCalculationModel.NONE,
    #     freq=12,
    #     dt1=date(2016, 1, 1),
    #     dt2=date(2016, 1, 15),
    #     dt3=date(2016, 2, 1),
    #     maturity_date=date(2016, 12, 31)
    # ))

    d0 = date(2016, 2, 29)
    d1 = date(2016, 1, 31)
    d2 = date(2016, 2, 11)
    d3 = date(2016, 3, 3)
    for d in [d0, d1, d2, d3]:
        print(d, d.strftime('%A'))

    print('-' * 10)
    for periodicity in Periodicity.objects.all():
        d = d0
        td0 = periodicity.to_timedelta(n=0, i=1, same_date=d)
        td1 = periodicity.to_timedelta(n=1, i=1, same_date=d)
        td2 = periodicity.to_timedelta(n=2, i=1, same_date=d)
        print(0, periodicity.id, periodicity.system_code, td0, td1, td2)
        print('\t', d + td0, d + td1, d + td2)

    print('-' * 10)
    print(101, 'd2 - d1', d2 - d1)
    print(102, 'd2 - d1', relativedelta.relativedelta(d2, d1))
    print(103, 'd3 - d1', relativedelta.relativedelta(d3, d1))
    print(104, relativedelta.relativedelta(date(2016, 1, 1), date(2016, 1, 12)))

    print('-' * 10)
    print(200, d1 + relativedelta.relativedelta(days=5))
    print(201, d1 + relativedelta.relativedelta(days=5, weekday=relativedelta.MO))
    print(202, d1 + relativedelta.relativedelta(days=20, weekday=relativedelta.MO))
    print(203, d1 + relativedelta.relativedelta(days=5, weekday=relativedelta.MO) +
          relativedelta.relativedelta(days=5, weekday=relativedelta.MO) +
          relativedelta.relativedelta(days=5, weekday=relativedelta.MO) +
          relativedelta.relativedelta(days=5, weekday=relativedelta.MO))
    print(204, d1 + relativedelta.relativedelta(day=31))
    print(205, d1 + relativedelta.relativedelta(months=1, day=31))

    print('-' * 10)
    print(300, [d.date().isoformat() for d in rrule.rrule(dtstart=d1, count=4, freq=rrule.WEEKLY)])
    print(300, [d.date().isoformat() for d in rrule.rrule(dtstart=d1, count=4, freq=rrule.WEEKLY,
                                                          byweekday=[rrule.FR])])

    print(301, [d.date().isoformat() for d in rrule.rrule(dtstart=d1, count=4, freq=rrule.MONTHLY)])

    print(302, [d.date().isoformat() for d in rrule.rrule(dtstart=d1, count=7, freq=rrule.DAILY)])
    print(303, [d.date().isoformat() for d in rrule.rrule(dtstart=d1, count=7, freq=rrule.DAILY,
                                                          byweekday=[rrule.FR])])
    print(304, [d.date().isoformat() for d in rrule.rrule(dtstart=d1, count=7, freq=rrule.DAILY,
                                                          byweekday=[rrule.MO, rrule.TU, rrule.WE, rrule.TH,
                                                                     rrule.FR])])
    print(305, [d.date().isoformat() for d in rrule.rrule(dtstart=d1, count=4, freq=rrule.MONTHLY,
                                                          bymonthday=[31], bysetpos=-1)])

    print('-' * 10)
    print(401, weekday(date(2016, 1, 31), date(2016, 2, 14), rrule.SU))
    print(402, weekday(date(2016, 1, 31), date(2016, 2, 13), rrule.SU))
    print(403, weekday(date(2016, 2, 1), date(2016, 2, 14), rrule.SU))
    print(404, weekday(date(2016, 2, 1), date(2016, 2, 13), rrule.SU))

    print(411, weekday(date(2016, 1, 31), date(2016, 2, 14), rrule.SA))
    print(412, weekday(date(2016, 1, 31), date(2016, 2, 13), rrule.SA))
    print(413, weekday(date(2016, 2, 1), date(2016, 2, 14), rrule.SA))
    print(414, weekday(date(2016, 2, 1), date(2016, 2, 13), rrule.SA))

    print('-' * 10)
    print(500, coupon_accrual_factor(
        accrual_calculation_model=AccrualCalculationModel.objects.get(pk=AccrualCalculationModel.ACT_ACT),
        periodicity=Periodicity.objects.get(pk=Periodicity.MONTHLY),
        dt1=date(2016, 1, 1),
        dt2=date(2016, 3, 31),
        dt3=date(2016, 2, 1),
        maturity_date=date.max
    ))

    # s = datetime.utcnow()
    # count = 0
    # for d in rrule.rrule(dtstart=date.min, until=date.max, freq=rrule.MONTHLY):
    #     count += 1
    # print(400, date.min, date.max, count, datetime.utcnow() - s)

    # s = datetime.utcnow()
    # sd = date.min
    # count = 0
    # while True:
    #     try:
    #         d = sd + relativedelta.relativedelta(days=count)
    #     except ValueError:
    #         break
    #     count += 1
    #     if d >= date.max:
    #         break
    # print(401, date.min, date.max, count, datetime.utcnow() - s)
