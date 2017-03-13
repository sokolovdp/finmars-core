from __future__ import unicode_literals

import logging

from celery.result import AsyncResult
from django.core.signing import TimestampSigner
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import FilterSet
from rest_framework.response import Response

from poms.common.filters import NoOpFilter, CharFilter
from poms.common.views import AbstractViewSet, AbstractModelViewSet, AbstractAsyncViewSet
from poms.reports.models import CustomField
from poms.reports.serializers import CustomFieldSerializer, ReportSerializer, TransactionReportSerializer, \
    CashFlowProjectionReportSerializer
from poms.reports.tasks import build_report, transaction_report, cash_flow_projection_report
from poms.users.filters import OwnerByMasterUserFilter

_l = logging.getLogger('poms.reports')


class CustomFieldFilterSet(FilterSet):
    id = NoOpFilter()
    name = CharFilter()

    class Meta:
        model = CustomField
        fields = []


class CustomFieldViewSet(AbstractModelViewSet):
    queryset = CustomField.objects.select_related(
        'master_user'
    )
    serializer_class = CustomFieldSerializer
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]
    filter_class = CustomFieldFilterSet
    ordering_fields = [
        'name',
    ]


# New report api

#
# class AbstractAsyncViewSet(AbstractViewSet):
#     serializer_class = None
#     celery_task = None
#
#     def get_serializer_context(self):
#         context = super(AbstractAsyncViewSet, self).get_serializer_context()
#         context['show_object_permissions'] = False
#         return context
#
#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         instance = serializer.save()
#         task_id = instance.task_id
#
#         signer = TimestampSigner()
#
#         if task_id:
#             res = AsyncResult(signer.unsign(task_id))
#             if res.ready():
#                 instance = res.result
#             if instance.master_user.id != self.request.user.master_user.id:
#                 raise PermissionDenied()
#             instance.task_id = task_id
#             instance.task_status = res.status
#             serializer = self.get_serializer(instance=instance, many=False)
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         else:
#             res = self.celery_task.apply_async(kwargs={'instance': instance})
#             instance.task_id = signer.sign('%s' % res.id)
#             instance.task_status = res.status
#             serializer = self.get_serializer(instance=instance, many=False)
#             return Response(serializer.data, status=status.HTTP_200_OK)


# class AbstractAsyncJsonViewSet(AbstractViewSet):
#     serializer_class = None
#     celery_task = None
#
#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         instance = serializer.save()
#         task_id = instance.task_id
#
#         signer = TimestampSigner()
#
#         if task_id:
#             res = AsyncResult(signer.unsign(task_id))
#             if res.ready():
#                 data = res.result
#             else:
#                 data = {}
#             # if instance.master_user.id != self.request.user.master_user.id:
#             #     raise PermissionDenied()
#             data['task_id'] = signer.sign('%s' % res.id)
#             data['task_status'] = res.status
#             return Response(data, status=status.HTTP_200_OK)
#         else:
#             res = self.celery_task.apply_async(kwargs={
#                 'data': serializer.data,
#                 'master_user': instance.master_user.id,
#                 'member': instance.member.id,
#             })
#             if res.ready():
#                 data = res.result
#             else:
#                 data = {}
#             data['task_id'] = signer.sign('%s' % res.id)
#             data['task_status'] = res.status
#             return Response(data, status=status.HTTP_200_OK)


class ReportViewSet(AbstractAsyncViewSet):
    serializer_class = ReportSerializer
    celery_task = build_report


class TransactionReportViewSet(AbstractAsyncViewSet):
    serializer_class = TransactionReportSerializer
    celery_task = transaction_report

    def get_serializer_context(self):
        context = super(TransactionReportViewSet, self).get_serializer_context()
        context['attributes_hide_objects'] = True
        context['custom_fields_hide_objects'] = True
        return context


class CashFlowProjectionReportViewSet(AbstractAsyncViewSet):
    serializer_class = CashFlowProjectionReportSerializer
    celery_task = cash_flow_projection_report

    def get_serializer_context(self):
        context = super(CashFlowProjectionReportViewSet, self).get_serializer_context()
        context['attributes_hide_objects'] = True
        context['custom_fields_hide_objects'] = True
        return context
