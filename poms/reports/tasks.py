import logging

from celery import shared_task

from poms.reports.builders import ReportBuilder

_l = logging.getLogger('poms.instruments')


# def _cache_key(master_user, *args, **kwargs):
#     m = hashlib.sha256()
#     m.update(str(args).encode('utf-8'))
#     m.update(str(kwargs).encode('utf-8'))
#     digest = base64.b64encode(m.digest())
#     # digest = m.hexdigest()
#     return '%s_%s' % (master_user, digest)
#
#
# def _balance_cache_key(master_user, cost_method, report_date, portfolios=None, accounts=None, strategies1=None,
#                        strategies2=None, strategies3=None, report_currency=None, use_portfolio=False,
#                        use_account=False, use_strategy=False, custom_fields=None):
#     portfolios = sorted(portfolios) if portfolios else []
#     accounts = sorted(accounts) if accounts else []
#     strategies1 = sorted(strategies1) if strategies1 else []
#     strategies2 = sorted(strategies2) if strategies2 else []
#     strategies3 = sorted(strategies3) if strategies3 else []
#     return _cache_key(
#         master_user, cost_method, report_date.toordinal(),
#         portfolios, accounts, strategies1, strategies2, strategies3,
#         report_currency, use_portfolio, use_account, use_strategy, custom_fields
#     )
#
#
# @shared_task(name='reports.balance_report')
# def balance_report(instance):
#     _l.debug('balance_report: %s', instance)
#     # _l.debug('balance_report: master_user=%s, cost_method=%s, begin_date=%s, end_date=%s, portfolios=%s, accounts=%s, '
#     #          'strategies1=%s, strategies2=%s, strategies3=%s, value_currency=%s, use_portfolio=%s, use_account=%s, '
#     #          'use_strategy=%s, custom_fields=%s',
#     #          instance.master_user, instance.cost_method, instance.begin_date, instance.end_date, instance.portfolios,
#     #          instance.accounts, instance.strategies1, instance.strategies2, instance.strategies3,
#     #          instance.value_currency, instance.use_portfolio, instance.use_account, instance.use_strategy,
#     #          instance.custom_fields)
#
#     builder = BalanceReport2Builder(instance=instance)
#     instance = builder.build()
#
#     _l.debug('finished')
#     return instance
#
#
# @shared_task(name='reports.pl_report')
# def pl_report(instance):
#     _l.debug('pl_report: %s', instance)
#
#     builder = PLReport2Builder(instance=instance)
#     instance = builder.build()
#
#     _l.debug('finished')
#     return instance


@shared_task(name='reports.build_report')
def build_report(instance):
    _l.debug('build_report: %s', instance)

    builder = ReportBuilder(instance=instance)
    instance = builder.build()

    _l.debug('finished')
    return instance


@shared_task(name='reports.transaction_report')
def transaction_report(instance):
    _l.debug('transaction_report')

    from poms.transactions.views import ComplexTransactionViewSet
    complex_transactions = ComplexTransactionViewSet.queryset.order_by(
        'date', 'code'
    )

    transactions = []
    for ct in complex_transactions:
        for t in ct.transactions.all():
            transactions.append(t)

    def _transaction_key(item):
        return (
            item.complex_transaction.date,
            item.complex_transaction.code,
            item.transaction_code,
        )

    instance.transactions = sorted(transactions, key=_transaction_key)

    _l.debug('finished')
    return instance
