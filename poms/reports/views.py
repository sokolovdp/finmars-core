from __future__ import unicode_literals

from celery.result import AsyncResult
from django.core.signing import Signer
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import FilterSet
from rest_framework.response import Response

from poms.common.filters import NoOpFilter, CharFilter
from poms.common.views import AbstractViewSet, AbstractModelViewSet
from poms.reports.models import CustomField
from poms.reports.serializers import CustomFieldSerializer, ReportSerializer
from poms.reports.tasks import build_report
from poms.users.filters import OwnerByMasterUserFilter


# class ReportClassViewSet(AbstractClassModelViewSet):
#     queryset = ReportClass.objects
#     serializer_class = ReportClassSerializer


class CustomFieldFilterSet(FilterSet):
    id = NoOpFilter()
    # report_class = django_filters.ModelMultipleChoiceFilter(queryset=ReportClass.objects)
    name = CharFilter()

    class Meta:
        model = CustomField
        fields = []


class CustomFieldViewSet(AbstractModelViewSet):
    queryset = CustomField.objects.select_related(
        'master_user'
    )
    serializer_class = CustomFieldSerializer
    # permission_classes = AbstractModelViewSet.permission_classes + [
    #     SuperUserOrReadOnly,
    # ]
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]
    filter_class = CustomFieldFilterSet
    ordering_fields = [
        # 'report_class', 'report_class__name',
        'name',
    ]


# New report api


class ReportViewSet(AbstractViewSet):
    serializer_class = ReportSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        task_id = instance.task_id

        signer = Signer()

        if task_id:
            res = AsyncResult(signer.unsign(task_id))
            if res.ready():
                instance = res.result
            if instance.master_user.id != self.request.user.master_user.id:
                raise PermissionDenied()
            instance.task_id = task_id
            instance.task_status = res.status
            serializer = self.get_serializer(instance=instance, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            res = build_report.apply_async(kwargs={'instance': instance})
            instance.task_id = signer.sign('%s' % res.id)
            instance.task_status = res.status
            serializer = self.get_serializer(instance=instance, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)

# # ---
#
# class BaseReportViewSet(AbstractViewSet):
#     report_builder_class = None
#
#     def create(self, request, *args, **kwargs):
#         assert self.report_builder_class is not None
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         instance = serializer.save()
#         builder = self.report_builder_class(instance=instance)
#         instance = builder.build()
#         serializer = self.get_serializer(instance=instance, many=False)
#         return Response(serializer.data, status=status.HTTP_201_CREATED)
#
#
# class AsyncAbstractReportViewSet(AbstractViewSet):
#     async_task = None
#
#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         instance = serializer.save()
#
#         task_id = instance.task_id
#         if task_id:
#             res = AsyncResult(task_id)
#             if res.ready():
#                 instance = res.result
#             if instance.master_user.id != self.request.user.master_user.id:
#                 raise PermissionDenied()
#             instance.task_id = task_id
#             instance.task_status = res.status
#             serializer = self.get_serializer(instance=instance, many=False)
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         else:
#             res = self.async_task.apply_async(kwargs={'instance': instance})
#             instance.task_id = res.id
#             instance.task_status = res.status
#             serializer = self.get_serializer(instance=instance, many=False)
#             return Response(serializer.data, status=status.HTTP_200_OK)
#
#
# class BalanceReport2ViewSet(AsyncAbstractReportViewSet):
#     serializer_class = BalanceReportSerializer
#     # report_builder_class = BalanceReport2Builder
#     async_task = balance_report
#
#     # def create(self, request, *args, **kwargs):
#     #     serializer = self.get_serializer(data=request.data)
#     #     serializer.is_valid(raise_exception=True)
#     #     instance = serializer.save()
#     #
#     #     task_id = instance.task_id
#     #     if task_id:
#     #         res = AsyncResult(task_id)
#     #         if res.ready():
#     #             instance = res.result
#     #         if instance.master_user.id != self.request.user.master_user.id:
#     #             raise PermissionDenied()
#     #         instance.task_id = task_id
#     #         instance.task_status = res.status
#     #         serializer = self.get_serializer(instance=instance, many=False)
#     #         return Response(serializer.data, status=status.HTTP_200_OK)
#     #     else:
#     #         res = self.async_task.apply_async(kwargs={'instance': instance})
#     #         instance.task_id = res.id
#     #         instance.task_status = res.status
#     #         serializer = self.get_serializer(instance=instance, many=False)
#     #         return Response(serializer.data, status=status.HTTP_200_OK)
#
#
# class PLReport2ViewSet(AsyncAbstractReportViewSet):
#     serializer_class = PLReportSerializer
#     # report_builder_class = PLReport2Builder
#     async_task = pl_report
#
#
# class CostReport2ViewSet(BaseReportViewSet):
#     serializer_class = CostReportSerializer
#     report_builder_class = CostReport2Builder
#
#
# class YTMReport2ViewSet(BaseReportViewSet):
#     serializer_class = YTMReportSerializer
#     report_builder_class = YTMReport2Builder
#
#
# class SimpleMultipliersReport2ViewSet(BaseReportViewSet):
#     serializer_class = SimpleMultipliersReport2Serializer
#     report_builder_class = SimpleMultipliersReport2Builder
