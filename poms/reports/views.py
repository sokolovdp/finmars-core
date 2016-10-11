from __future__ import unicode_literals

from rest_framework import status
from rest_framework.response import Response

from poms.common.views import AbstractViewSet
from poms.reports.backends.balance import BalanceReportBuilder, BalanceReport2Builder
from poms.reports.backends.cost import CostReportBuilder, CostReport2Builder
from poms.reports.backends.pl import PLReportBuilder, PLReport2Builder
from poms.reports.backends.simple_multipliers import SimpleMultipliersReportBuilder, SimpleMultipliersReport2Builder
from poms.reports.backends.ytm import YTMReportBuilder, YTMReport2Builder
from poms.reports.serializers import BalanceReportSerializer, SimpleMultipliersReportSerializer, PLReportSerializer, \
    CostReportSerializer, YTMReportSerializer, SimpleMultipliersReport2Serializer


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


# class BalanceReportViewSet(BaseReportViewSet):
#     serializer_class = BalanceReportSerializer
#     report_builder_class = BalanceReportBuilder


class BalanceReport2ViewSet(BaseReportViewSet):
    serializer_class = BalanceReportSerializer
    report_builder_class = BalanceReport2Builder


# class PLReportViewSet(BaseReportViewSet):
#     serializer_class = PLReportSerializer
#     report_builder_class = PLReportBuilder


class PLReport2ViewSet(BaseReportViewSet):
    serializer_class = PLReportSerializer
    report_builder_class = PLReport2Builder


# class CostReportViewSet(BaseReportViewSet):
#     serializer_class = CostReportSerializer
#     report_builder_class = CostReportBuilder


class CostReport2ViewSet(BaseReportViewSet):
    serializer_class = CostReportSerializer
    report_builder_class = CostReport2Builder


# class YTMReportViewSet(BaseReportViewSet):
#     serializer_class = YTMReportSerializer
#     report_builder_class = YTMReportBuilder


class YTMReport2ViewSet(BaseReportViewSet):
    serializer_class = YTMReportSerializer
    report_builder_class = YTMReport2Builder


# class SimpleMultipliersReportViewSet(AbstractViewSet):
#     serializer_class = SimpleMultipliersReportSerializer
#
#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         instance = serializer.save()
#         builder = SimpleMultipliersReportBuilder(instance=instance)
#         instance = builder.build()
#         serializer = self.get_serializer(instance=instance, many=False)
#         return Response(serializer.data, status=status.HTTP_201_CREATED)


class SimpleMultipliersReport2ViewSet(BaseReportViewSet):
    serializer_class = SimpleMultipliersReport2Serializer
    report_builder_class = SimpleMultipliersReport2Builder
