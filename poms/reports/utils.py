import logging
from datetime import date

from poms.instruments.models import CostMethod

_l = logging.getLogger('poms.reports')


def sprint_table(data, headers=None, floatfmt=".4f"):
    import tabulate
    return tabulate.tabulate(data, headers=headers, floatfmt=floatfmt)


def calc_cash_for_contract_for_difference(member, instr, prtfl, acc, trn,
                                          calc_newer=False, calc_all=False, save=False):
    from poms.reports.builders import Report, ReportBuilder, VirtualTransaction

    # queryset = Transaction.objects.all()

    if calc_all:
        report_date = date.max
    else:
        if trn is None:
            return
        if calc_newer:
            report_date = date.max
        else:
            report_date = trn.accounting_date

    r = Report(
        master_user=member.master_user,
        member=member,
        instruments=[instr.id],
        portfolios=[prtfl.id],
        accounts=[acc.id],
        portfolio_mode=Report.MODE_INDEPENDENT,
        account_mode=Report.MODE_INDEPENDENT,
        strategy1_mode=Report.MODE_IGNORE,
        strategy2_mode=Report.MODE_IGNORE,
        strategy3_mode=Report.MODE_IGNORE,
        cost_method=CostMethod.objects.get(pk=CostMethod.FIFO),
        report_date=report_date,
        pricing_policy=None
    )
    rb = ReportBuilder(instance=r)

    transactions = rb.get_transactions()
    if trn:
        add_this = trn.id is None or not any(trn.pk == t.pk for t in transactions)
        if add_this:
            transactions.append(VirtualTransaction(report=rb.instance, pricing_provider=rb.pricing_provider,
                                                   fx_rate_provider=rb.fx_rate_provider, trn=trn))
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

        t_save = False
        if calc_all:
            t_save = True
            pass
        else:
            if vt_state == vt_this:
                vt_state = vt_newer
            elif (vt.pk == trn.pk) or (trn.pk is None and vt.pk is None):
                vt_state = vt_this

            _l.info('%s -> %s', vt, vt_state)

            if vt_state == vt_older:
                pass
            elif vt_state == vt_this:
                t_save = True
                pass
            elif vt_state == vt_newer:
                if calc_newer:
                    t_save = True
                    pass
                else:
                    break
        if save and t_save:
            vt.trn.cash_consideration = vt.cash
            # vt.trn.save(update_fields=['cash_consideration'])
            vt.trn.save()
            vt.pk = vt.trn.pk
            _l.info('save -> %s' % vt)

    for vt in transactions:
        vt.trn.cash_consideration = vt.cash

    VirtualTransaction.dumps(transactions)

    return [vt.trn for vt in transactions]
