from __future__ import unicode_literals, division

from poms.instruments.models import AccrualCalculationModel


def _is_leap(year):
    # year -> 1 if leap year, else 0.
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def coupon_accrual_factor(accrual, freq, dt1, dt2, dt3, maturity_date):
    # day_convention_code - accrual calculation model
    # freq
    # dt1
    # dt2
    # dt3
    # maturity_date - instrument.matutity_date

    # CouponAccrualFactor:
    # day_convention_code As Integer -> accrual_calculation_model
    # freq As Integer -> periodicity with periodicity_N
    # ByVal dt1 As Date -> ?
    # ByVal dt2 As Date -> ?
    # ByVal dt3 As Date -> ?
    # MaturityDate As Date -> instrument.maturity_date

    if accrual is None or freq is None or dt1 is None or dt2 is None or dt3 is None:
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

    d1 = dt1.day
    M1 = dt1.month
    y1 = dt1.year
    d2 = dt2.day
    M2 = dt2.month
    y2 = dt2.year
    d3 = dt3.day
    M3 = dt3.month
    y3 = dt3.year

    if accrual == AccrualCalculationModel.NONE:  # 1
        # Case 0  'none
        #     CouponAccrualFactor = 0
        return 0.0
    elif accrual == AccrualCalculationModel.ACT_ACT:  # 2
        # Case 1  'ACT/ACT
        #     CouponAccrualFactor = (dt2 - dt1) / (dt3 - dt1) / freq
        return 0
    elif accrual == AccrualCalculationModel.ACT_ACT_ISDA:  # 3
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
        return 0
    elif accrual == AccrualCalculationModel.ACT_360:  # 4
        # Case 2  'ACT/360
        #     CouponAccrualFactor = (dt2 - dt1) / 360
        return 0
    elif accrual == AccrualCalculationModel.ACT_365:  # 5
        # Case 3  'ACT/365
        #     CouponAccrualFactor = (dt2 - dt1) / 365
        return 0
    elif accrual == AccrualCalculationModel.ACT_365_25:  # 6
        # Case 106  'Act/365.25
        #     CouponAccrualFactor = (dt2 - dt1) / 365.25
        return 0
    elif accrual == AccrualCalculationModel.ACT_365_366:  # 7
        # Case 107  'Act/365(366)
        #     If y1 < y2 Then
        #         If (Month(DateSerial(y1, 2, 29)) = 2 Or Month(DateSerial(y2, 2, 29)) = 2) And _
        #                 DateSerial(y1, 2, 29) >= dt1 And DateSerial(y1, 2, 29) <= dt2 Then
        #             CouponAccrualFactor = (dt2 - dt1 + 1) / 366
        #         Else
        #             CouponAccrualFactor = (dt2 - dt1 + 1) / 365
        #         End If
        #     End If
        return 0
    elif accrual == AccrualCalculationModel.ACT_1_365:  # 8
        # Case 104  'Act+1/365
        #     CouponAccrualFactor = (dt2 - dt1 + 1) / 365
        return 0
    elif accrual == AccrualCalculationModel.ACT_1_360:  # 9
        # CouponAccrualFactor = (dt2 - dt1 + 1) / 360
        return 0
    elif accrual == AccrualCalculationModel.C_30_360:  # 11
        # Case 5  '30/360
        #     If d1 = 31 Then d1 = 30
        #     If d2 = 31 And (d1 = 30 Or d1 = 31) Then d2 = 30
        #     CouponAccrualFactor = ((y2 - y1) * 360 + (M2 - M1) * 30 + (d2 - d1)) / 360
        return 0
    elif accrual == AccrualCalculationModel.C_30_360_NO_EOM:  # 12
        # Case 14  '30/360 (NO EOM)
        #     If d1 = 31 Then d1 = 30
        #     If d2 = 31 And (d1 = 30 Or d1 = 31) Then d2 = 30
        #     CouponAccrualFactor = ((y2 - y1) * 360 + (M2 - M1) * 30 + (d2 - d1)) / 360
        return 0
    elif accrual == AccrualCalculationModel.C_30E_P_360:  # 24
        # Case 101  '30E+/360
        #     If d1 = 31 Then d1 = 30
        #     If d2 = 31 Then
        #     M2 = M2 + 1
        #     d2 = 1
        #     End If
        #     CouponAccrualFactor = ((y2 - y1) * 360 + (M2 - M1) * 30 + (d2 - d1)) / 360
        return 0
    elif accrual == AccrualCalculationModel.C_30E_P_360_ITL:  # 13
        # Case 102  '30E+/360.ITL
        #     If d1 = 31 Then d1 = 30
        #     If d2 = 31 Then d2 = 30
        #     CouponAccrualFactor = ((y2 - y1) * 360 + (M2 - M1) * 30 + (d2 - d1 + 1)) / 360
        return 0
    elif accrual == AccrualCalculationModel.NL_365:  # 14
        # Case 9  'NL/365
        #     Y1_leap = Month(DateSerial(Year(dt1), 2, 29)) = 2
        #     Y2_leap = Month(DateSerial(Year(dt2), 2, 29)) = 2
        #     k = 0
        #     If Y1_leap And dt1 < DateSerial(Year(dt1), 2, 29) And dt2 >= DateSerial(Year(dt1), 2, 29) Then k = 1
        #     If Y2_leap And dt2 >= DateSerial(Year(dt2), 2, 29) And dt1 < DateSerial(Year(dt2), 2, 29) Then k = 1
        #     CouponAccrualFactor = (dt2 - dt1 - k) / 365
        return 0
    elif accrual == AccrualCalculationModel.NL_365_NO_EOM:  # 15
        # Case 18  'NL/365 (NO-EOM)
        #     Y1_leap = Month(DateSerial(Year(dt1), 2, 29)) = 2
        #     Y2_leap = Month(DateSerial(Year(dt2), 2, 29)) = 2
        #     k = 0
        #     If Y1_leap And dt1 < DateSerial(Year(dt1), 2, 29) And dt2 >= DateSerial(Year(dt1), 2, 29) Then k = 1
        #     If Y2_leap And dt2 >= DateSerial(Year(dt2), 2, 29) And dt1 < DateSerial(Year(dt2), 2, 29) Then k = 1
        #     CouponAccrualFactor = (dt2 - dt1 - k) / 365
        return 0
    elif accrual == AccrualCalculationModel.ISMA_30_365:  # 16
        # Case 20  'ISMA-30/360 = 30E/360
        #     If d1 = 31 Then d1 = 30
        #     If d2 = 31 Then d2 = 30
        #     CouponAccrualFactor = ((y2 - y1) * 360 + (M2 - M1) * 30 + (d2 - d1)) / 360
        return 0
    elif accrual == AccrualCalculationModel.ISMA_30_365_NO_EOM:  # 17
        # Case 23  'ISMA-30/360 (NO EOM)
        #     If d1 = 31 Then d1 = 30
        #     If d2 = 31 Then d2 = 30
        #     CouponAccrualFactor = ((y2 - y1) * 360 + (M2 - M1) * 30 + (d2 - d1)) / 360
        return 0
    elif accrual == AccrualCalculationModel.US_MINI_30_360_EOM:  # 18
        # Case 29  'US MUNI-30/360 (EOM)
        #     If d1 = 31 Then d1 = 30
        #     If d2 = 31 And (d1 = 30 Or d1 = 31) Then d2 = 30
        #     lastDay1 = Month(dt1 + 1) = 3 And Day(dt1 + 1) = 1
        #     lastDay2 = Month(dt2 + 1) = 3 And Day(dt2 + 1) = 1
        #     If lastDay1 Then d1 = 30
        #     If lastDay1 And lastDay2 Then d2 = 30
        #     CouponAccrualFactor = ((y2 - y1) * 360 + (M2 - M1) * 30 + (d2 - d1)) / 360
        return 0
    elif accrual == AccrualCalculationModel.US_MINI_30_360_NO_EOM:  # 19
        # Case 32  'US MUNI-30/360 (NO EOM)
        #     If d1 = 31 Then d1 = 30
        #     If d2 = 31 And (d1 = 30 Or d1 = 31) Then d2 = 30
        #     CouponAccrualFactor = ((y2 - y1) * 360 + (M2 - M1) * 30 + (d2 - d1)) / 360
        return 0
    elif accrual == AccrualCalculationModel.BUS_DAYS_252:  # 20
        # Case 33  'BUS DAYS/252
        #     CouponAccrualFactor = (DateDiff("d", dt1, dt2) - DateDiff("ww", dt1, dt2, vbSaturday) - _
        #         DateDiff("d", dt1, dt2, vbSunday)) / 252
        return 0
    elif accrual == AccrualCalculationModel.GERMAN_30_360_EOM:  # 21
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
        return 0
    elif accrual == AccrualCalculationModel.GERMAN_30_360_NO_EOM:  # 22
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
        return 0
    elif accrual == AccrualCalculationModel.REVERSED_ACT_365:  # 23
        # Case 1001  'reversed ACT/365
        #     CouponAccrualFactor = (dt3 - dt2) / 365
        return 0
    pass
