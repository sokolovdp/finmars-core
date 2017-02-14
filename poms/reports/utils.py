import logging
from datetime import date

from django.conf import settings

from poms.common.utils import isclose
from poms.instruments.models import CostMethod

_l = logging.getLogger('poms.reports')


def sprint_table(data, headers=None, floatfmt=".4f"):
    import tabulate
    return tabulate.tabulate(data, headers=headers, floatfmt=floatfmt)


def calc_cash_for_contract_for_difference(transaction, instrument, portfolio, account, member,
                                          is_calculate_for_newer=False, is_calculate_for_all=False, save=False):
    _l.debug('calc_cash_for_contract_for_difference: transaction=%s, instrument=%s, portfolio=%s, account=%s, '
             'member=%s, is_calculate_for_newer=%s, is_calculate_for_all=%s, save=%s',
             transaction.id if transaction else None,
             instrument.id if instrument else None,
             portfolio.id if portfolio else None,
             account.id if account else None,
             member.id if member else None,
             is_calculate_for_newer, is_calculate_for_all, save)

    from poms.reports.builders import Report, ReportBuilder, VirtualTransaction

    # queryset = Transaction.objects.all()

    if is_calculate_for_all or is_calculate_for_newer:
        report_date = date.max
    else:
        if transaction is None:
            return None
        report_date = transaction.accounting_date

    if transaction and instrument is None:
        instrument = transaction.instrument

    assert instrument is not None, "instrument must be specified"

    r = Report(master_user=instrument.master_user,
               member=member,
               instruments=[instrument.id],
               portfolios=[portfolio.id] if portfolio else None,
               accounts=[account.id] if account else None,
               portfolio_mode=Report.MODE_INDEPENDENT if portfolio else Report.MODE_IGNORE,
               account_mode=Report.MODE_INDEPENDENT if account else Report.MODE_IGNORE,
               strategy1_mode=Report.MODE_IGNORE,
               strategy2_mode=Report.MODE_IGNORE,
               strategy3_mode=Report.MODE_IGNORE,
               cost_method=CostMethod.objects.get(pk=CostMethod.FIFO),
               report_date=report_date,
               pricing_policy=None)
    rb = ReportBuilder(instance=r)

    transactions = rb.get_transactions()
    if transaction:
        add_this = transaction.id is None or not any(transaction.pk == t.pk for t in transactions)
        if add_this:
            transactions.append(VirtualTransaction(report=rb.instance, pricing_provider=rb.pricing_provider,
                                                   fx_rate_provider=rb.fx_rate_provider, trn=transaction))
            transactions = rb.sort_transactions(transactions)

    rb.calc_fifo_multipliers(transactions)

    if settings.DEV:
        VirtualTransaction.dumps(transactions)

    processed = set()

    # def _calc_cash(trn):
    #     trn.cash += trn.overheads
    #     # trn.cash += (trn.principal + trn.carry) * trn.fifo_multiplier
    #     for cb, delta in trn.fifo_closed_by:
    #         cb.cash += (trn.principal + trn.carry) * delta

    vt_older = -1
    vt_this = 0
    vt_newer = 1
    vt_state = vt_older
    for vt in transactions:
        vt.cash += vt.overheads
        for vt_to, delta in vt.fifo_closed_by:
            if vt_to.lid not in processed:
                processed.add(vt_to.lid)
                # vt_to.cash += (vt_to.principal + vt_to.carry) * vt_to.fifo_multiplier + vt_to.overheads
                vt_to.cash += (vt_to.principal + vt_to.carry) * vt_to.fifo_multiplier
            vt_to.cash += (vt.principal + vt.carry) * delta

        if transaction:
            if vt_state == vt_this:
                vt_state = vt_newer
            elif (vt.pk == transaction.pk) or (transaction.pk is None and vt.pk is None):
                vt_state = vt_this

        t_save = False
        if is_calculate_for_all or (vt_state == vt_this) or (is_calculate_for_newer and vt_state == vt_newer):
            t_save = True

        if t_save and not isclose(vt.trn.cash_consideration, vt.cash):
            if settings.DEV:
                _l.debug('+ => %s: cash=(%s => %s)', vt, vt.trn.cash_consideration, vt.cash)
            vt.trn.cash_consideration = vt.cash
            if save:
                vt.trn.save()
                vt.pk = vt.trn.pk
        else:
            if settings.DEV:
                _l.debug('- => %s: cash=(%s <> %s)', vt, vt.trn.cash_consideration, vt.cash)
            pass

    if settings.DEV:
        VirtualTransaction.dumps(transactions)

    return [vt.trn for vt in transactions]


def xnpv(rate, values, dates):
    '''Equivalent of Excel's XNPV function.
    https://support.office.com/en-us/article/XNPV-function-1b42bbf6-370f-4532-a0eb-d67c16b664b7

    >>> from datetime import date
    >>> dates = [date(2010, 12, 29), date(2012, 1, 25), date(2012, 3, 8)]
    >>> values = [-10000, 20, 10100]
    >>> xnpv(0.1, values, dates)
    -966.4345...
    '''
    # _l.debug('xnpv > rate=%s', rate)
    try:
        if rate <= -1.0:
            return float('inf')
        d0 = dates[0]  # or min(dates)
        return sum(
            (vi / (1.0 + rate) ** ((di - d0).days / 365.0))
            for vi, di in zip(values, dates)
        )
    finally:
        # _l.debug('xnpv <')
        pass


def xirr(values, dates):
    '''Equivalent of Excel's XIRR function.
    https://support.office.com/en-us/article/XIRR-function-de1242ec-6477-445b-b11b-a303ad9adc9d

    >>> from datetime import date
    >>> dates = [date(2010, 12, 29), date(2012, 1, 25), date(2012, 3, 8)]
    >>> values = [-10000, 20, 10100]
    >>> xirr(values, dates)
    0.0100612...
    '''
    # _l.debug('xirr >')
    try:
        from scipy.optimize import newton, brentq

        # return newton(lambda r: xnpv(r, values, dates), 0.0), \
        #        brentq(lambda r: xnpv(r, values, dates), -1.0, 1e10)
        # return newton(lambda r: xnpv(r, values, dates), 0.0)
        # return brentq(lambda r: xnpv(r, values, dates), -1.0, 1e10)
        try:
            return newton(lambda r: xnpv(r, values, dates), 0.0)
        except RuntimeError:  # Failed to converge?
            return brentq(lambda r: xnpv(r, values, dates), -1.0, 1e10)
    finally:
        # _l.debug('xirr <')
        pass
