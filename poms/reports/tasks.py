import logging
from datetime import date

from celery import shared_task
from celery.result import AsyncResult

from poms.instruments.models import CostMethod
from poms.reports.models import BalanceReport
from poms.users.models import MasterUser

_l = logging.getLogger('poms.instruments')


@shared_task(name='reports.balance_report')
def balance_report_async(master_user, cost_method, report_date, portfolios=None, accounts=None, strategies1=None,
                         strategies2=None, strategies3=None, value_currency=None, use_portfolio=False,
                         use_account=False, use_strategy=False, custom_fields=None):
    _l.debug('balance_report: master_user=%s, cost_method=%s, report_date=%s, portfolios=%s, accounts=%s, '
             'strategies1=%s, strategies2=%s, strategies3=%s, value_currency=%s, '
             'use_portfolio=%s, use_account=%s, use_strategy=%s, custom_fields=%s',
             master_user, cost_method, report_date, portfolios, accounts,
             strategies1, strategies2, strategies3, value_currency,
             use_portfolio, use_account, use_strategy, custom_fields)
    master_user = MasterUser.objects.get(pk=master_user)
    cost_method = CostMethod.objects.get(pk=cost_method)
    report_date = date.fromordinal(report_date)

    portfolios = portfolios or []
    accounts = accounts or []
    strategies1 = strategies1 or []
    strategies2 = strategies2 or []
    strategies3 = strategies3 or []
    value_currency = value_currency or master_user.currency

    report = BalanceReport(
        master_user=master_user,
        end_date=report_date,
        use_portfolio=use_portfolio, use_account=use_account,
        use_strategy=use_strategy,
        cost_method=cost_method,
    )

    _l.debug('finished')
    return []


def balance_report(report=None, result_id=None):
    if result_id:
        res = AsyncResult(result_id)
        report.async_status = res.status
        if res.ready():
            # update config
            pass
    else:
        res = balance_report_async.apply_async(kwargs={
            'report': report
        })
        report.async_result_id = res.id
        report.async_status = res.status
    return report
