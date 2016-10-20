import base64
import hashlib
import logging

from celery import shared_task

from poms.reports.backends.balance import BalanceReport2Builder

_l = logging.getLogger('poms.instruments')


def _cache_key(master_user, *args, **kwargs):
    m = hashlib.sha256()
    m.update(str(args).encode('utf-8'))
    m.update(str(kwargs).encode('utf-8'))
    digest = base64.b64encode(m.digest())
    # digest = m.hexdigest()
    return '%s_%s' % (master_user, digest)


def _balance_cache_key(master_user, cost_method, report_date, portfolios=None, accounts=None, strategies1=None,
                       strategies2=None, strategies3=None, value_currency=None, use_portfolio=False,
                       use_account=False, use_strategy=False, custom_fields=None):
    portfolios = sorted(portfolios) if portfolios else []
    accounts = sorted(accounts) if accounts else []
    strategies1 = sorted(strategies1) if strategies1 else []
    strategies2 = sorted(strategies2) if strategies2 else []
    strategies3 = sorted(strategies3) if strategies3 else []
    return _cache_key(
        master_user, cost_method, report_date.toordinal(),
        portfolios, accounts, strategies1, strategies2, strategies3,
        value_currency, use_portfolio, use_account, use_strategy, custom_fields
    )


@shared_task(name='reports.balance_report')
# def balance_report(master_user, cost_method, begin_date, end_date, portfolios=None, accounts=None, strategies1=None,
#                    strategies2=None, strategies3=None, value_currency=None, use_portfolio=False,
#                    use_account=False, use_strategy=False, custom_fields=None, **kwargs):
def balance_report(instance):
    # _l.debug('balance_report: master_user=%s, cost_method=%s, begin_date=%s, end_date=%s, portfolios=%s, accounts=%s, '
    #          'strategies1=%s, strategies2=%s, strategies3=%s, value_currency=%s, '
    #          'use_portfolio=%s, use_account=%s, use_strategy=%s, custom_fields=%s',
    #          master_user, cost_method, begin_date, end_date, portfolios, accounts,
    #          strategies1, strategies2, strategies3, value_currency,
    #          use_portfolio, use_account, use_strategy, custom_fields)
    # _l.debug('balance_report: %s', pprint.pformat(instance, indent=2))
    _l.debug('balance_report: master_user=%s, cost_method=%s, begin_date=%s, end_date=%s, portfolios=%s, accounts=%s, '
             'strategies1=%s, strategies2=%s, strategies3=%s, value_currency=%s, use_portfolio=%s, use_account=%s, '
             'use_strategy=%s, custom_fields=%s',
             instance.master_user, instance.cost_method, instance.begin_date, instance.end_date, instance.portfolios,
             instance.accounts, instance.strategies1, instance.strategies2, instance.strategies3,
             instance.value_currency, instance.use_portfolio, instance.use_account, instance.use_strategy,
             instance.custom_fields)
    # serializer = BalanceReportSerializer(data=instance)
    # serializer.is_valid(raise_exception=True)
    # instance = serializer.save()

    # master_user = MasterUser.objects.get(pk=master_user)
    # cost_method = CostMethod.objects.get(pk=cost_method)
    # report_date = date.fromordinal(report_date)

    # portfolios = portfolios or []
    # accounts = accounts or []
    # strategies1 = strategies1 or []
    # strategies2 = strategies2 or []
    # strategies3 = strategies3 or []
    # value_currency = value_currency or master_user.currency

    # report = BalanceReport(
    #     master_user=master_user,
    #     begin_date=begin_date,
    #     end_date=end_date,
    #     use_portfolio=use_portfolio,
    #     use_account=use_account,
    #     use_strategy=use_strategy,
    #     cost_method=cost_method,
    # )

    builder = BalanceReport2Builder(instance=instance)
    instance = builder.build()

    _l.debug('finished')

    # serializer = BalanceReportSerializer(instance=instance)
    # return serializer.data
    return instance
