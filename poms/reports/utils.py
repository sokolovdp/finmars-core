import logging
from datetime import date

from poms.common.utils import isclose
from poms.instruments.models import CostMethod

_l = logging.getLogger('poms.reports')


def sprint_table(data, headers=None, floatfmt=".4f"):
    import tabulate
    return tabulate.tabulate(data, headers=headers, floatfmt=floatfmt)


def calc_cash_for_contract_for_difference(member, instrument, portfolio, account, transaction,
                                          is_calculate_for_newer=False, is_calculate_for_all=False, save=False):
    from poms.reports.builders import Report, ReportBuilder, VirtualTransaction

    # queryset = Transaction.objects.all()

    if is_calculate_for_all or is_calculate_for_newer:
        report_date = date.max
    else:
        if transaction is None:
            return None
        report_date = transaction.accounting_date

    r = Report(master_user=member.master_user,
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
            _l.debug('+ => %s: cash=%s, v_cash=%s', vt, vt.trn.cash_consideration, vt.cash)
            vt.trn.cash_consideration = vt.cash
            if save:
                vt.trn.save()
                vt.pk = vt.trn.pk
        else:
            _l.debug('- => %s: cash=%s, v_cash=%s', vt, vt.trn.cash_consideration, vt.cash)

    VirtualTransaction.dumps(transactions)

    return [vt.trn for vt in transactions]
