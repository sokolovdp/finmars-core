from __future__ import unicode_literals

from celery.result import AsyncResult
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from poms.common.views import AbstractViewSet
from poms.reports.backends.cost import CostReport2Builder
from poms.reports.backends.simple_multipliers import SimpleMultipliersReport2Builder
from poms.reports.backends.ytm import YTMReport2Builder
from poms.reports.serializers import BalanceReportSerializer, PLReportSerializer, \
    CostReportSerializer, YTMReportSerializer, SimpleMultipliersReport2Serializer
from poms.reports.tasks import balance_report, pl_report


class BaseReportViewSet(AbstractViewSet):
    report_builder_class = None

    def create(self, request, *args, **kwargs):
        assert self.report_builder_class is not None
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        builder = self.report_builder_class(instance=instance)
        instance = builder.build()
        serializer = self.get_serializer(instance=instance, many=False)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AsyncAbstractReportViewSet(AbstractViewSet):
    async_task = None

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        task_id = instance.task_id
        if task_id:
            res = AsyncResult(task_id)
            if res.ready():
                instance = res.result
            if instance.master_user.id != self.request.user.master_user.id:
                raise PermissionDenied()
            instance.task_id = task_id
            instance.task_status = res.status
            serializer = self.get_serializer(instance=instance, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            res = self.async_task.apply_async(kwargs={'instance': instance})
            instance.task_id = res.id
            instance.task_status = res.status
            serializer = self.get_serializer(instance=instance, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)


class BalanceReport2ViewSet(AsyncAbstractReportViewSet):
    serializer_class = BalanceReportSerializer
    # report_builder_class = BalanceReport2Builder
    async_task = balance_report

    # def create(self, request, *args, **kwargs):
    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     instance = serializer.save()
    #
    #     task_id = instance.task_id
    #     if task_id:
    #         res = AsyncResult(task_id)
    #         if res.ready():
    #             instance = res.result
    #         if instance.master_user.id != self.request.user.master_user.id:
    #             raise PermissionDenied()
    #         instance.task_id = task_id
    #         instance.task_status = res.status
    #         serializer = self.get_serializer(instance=instance, many=False)
    #         return Response(serializer.data, status=status.HTTP_200_OK)
    #     else:
    #         res = self.async_task.apply_async(kwargs={'instance': instance})
    #         instance.task_id = res.id
    #         instance.task_status = res.status
    #         serializer = self.get_serializer(instance=instance, many=False)
    #         return Response(serializer.data, status=status.HTTP_200_OK)


class PLReport2ViewSet(AsyncAbstractReportViewSet):
    serializer_class = PLReportSerializer
    # report_builder_class = PLReport2Builder
    async_task = pl_report


class CostReport2ViewSet(BaseReportViewSet):
    serializer_class = CostReportSerializer
    report_builder_class = CostReport2Builder


class YTMReport2ViewSet(BaseReportViewSet):
    serializer_class = YTMReportSerializer
    report_builder_class = YTMReport2Builder


class SimpleMultipliersReport2ViewSet(BaseReportViewSet):
    serializer_class = SimpleMultipliersReport2Serializer
    report_builder_class = SimpleMultipliersReport2Builder
