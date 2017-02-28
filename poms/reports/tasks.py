import logging

from celery import shared_task
from django.db import transaction
from django.utils import translation, timezone

from poms.reports.builders import ReportBuilder
from poms.reports.cash_flow_projection import TransactionReportBuilder, CashFlowProjectionReportBuilder
from poms.users.models import MasterUser, Member

_l = logging.getLogger('poms.instruments')


# curl -X POST --user a:a  http://127.0.0.1:8000/api/v1/reports/transaction-report/?format=json  -v -o /dev/null


class FakeRequest:
    def __init__(self, master_user, member):
        self.user = member.user
        self.user.member = member
        self.user.master_user = master_user


@shared_task(name='reports.build_report', expires=30)
def build_report(instance):
    _l.debug('build_report: %s', instance)
    with transaction.atomic():
        try:
            builder = ReportBuilder(instance=instance)
            instance = builder.build()
            return instance
        finally:
            transaction.set_rollback(True)
            _l.debug('finished')


def _json_cb(data, master_user, member, serializer_class):
    _l.debug('_json_cb: >')

    master_user = MasterUser.objects.get(id=master_user)
    member = Member.objects.get(id=member)

    with translation.override(None), timezone.override(None):
        ser = serializer_class(data=data, context={
            'request': FakeRequest(master_user, member),
            'master_user': master_user,
            'member': member,
        })
        ser.is_valid(raise_exception=True)
        instance = ser.save()

        instance = transaction_report(instance)

        ser = serializer_class(instance=instance, context={
            # 'request': FakeRequest(master_user, member),
            'master_user': master_user,
            'member': member,
        })
        res_data = ser.data

    _l.debug('_json_cb: <')

    return res_data


@shared_task(name='reports.transaction_report', expires=30)
def transaction_report(instance):
    _l.debug('transaction_report: >')
    with transaction.atomic():
        try:
            builder = TransactionReportBuilder(instance)
            builder.build()
            return builder.instance
        finally:
            transaction.set_rollback(True)
            _l.debug('transaction_report: <')


@shared_task(name='reports.transaction_report_json', expires=30)
def transaction_report_json(data, master_user, member):
    _l.debug('transaction_report_json: >')

    from poms.reports.serializers import TransactionReportSerializer
    res_data = _json_cb(data=data, master_user=master_user, member=member, serializer_class=TransactionReportSerializer)

    _l.debug('transaction_report_json: <')
    return res_data


@shared_task(name='reports.cash_flow_projection_report', expires=30)
def cash_flow_projection_report(instance):
    _l.debug('cash_flow_projection_report: >')
    with transaction.atomic():
        try:
            builder = CashFlowProjectionReportBuilder(instance)
            builder.build()
            return builder.instance
        finally:
            transaction.set_rollback(True)
            _l.debug('cash_flow_projection_report: <')
