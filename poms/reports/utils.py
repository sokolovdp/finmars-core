from datetime import date

from poms.instruments.models import CostMethod


def sprint_table(data, headers=None, floatfmt=".4f"):
    import tabulate
    return tabulate.tabulate(data, headers=headers, floatfmt=floatfmt)


def calc_cash_flow_for_contract_for_difference(member, instr, prtfl, acc, trn, update_newer=True):
    from poms.reports.builders import Report, ReportBuilder, VirtualTransaction

    # queryset = Transaction.objects.all()

    if update_newer:
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
    rb.calc_fifo_multipliers(transactions)
    VirtualTransaction.dumps(transactions)

    # vt_mode : o-older, t-this, n-newer
    vt_older = 1
    vt_this = 2
    vt_newer = 3

    vt_mode = vt_older
    for vt in transactions:
        if vt_mode == vt_this:
            vt_mode = vt_newer
        if vt.trn.id == trn.id:
            vt_mode = vt_this

        if vt_mode == vt_older:
            pass
        elif vt_mode == vt_this:
            pass
        elif vt_mode == vt_newer:
            if not update_newer:
                break
            pass
