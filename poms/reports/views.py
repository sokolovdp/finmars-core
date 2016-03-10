from __future__ import unicode_literals

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from poms.reports.backends.balance import BalanceReportBuilder
from poms.reports.backends.pl import PLReportBuilder
from poms.reports.backends.simple_multipliers import SimpleMultipliersReportBuilder
from poms.reports.serializers import BalanceReportSerializer, SimpleMultipliersReportSerializer, PLReportSerializer


class BaseReportViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = None
    report_builder_class = None

    def get_serializer(self, *args, **kwargs):
        assert self.serializer_class is not None
        kwargs['context'] = self.get_serializer_context()
        return self.serializer_class(*args, **kwargs)

    def get_serializer_context(self):
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }

    def create(self, request, *args, **kwargs):
        assert self.report_builder_class is not None
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        builder = self.report_builder_class(instance=instance)
        instance = builder.build()
        serializer = self.get_serializer(instance=instance, many=False)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BalanceReportViewSet(BaseReportViewSet):
    serializer_class = BalanceReportSerializer
    report_builder_class = BalanceReportBuilder


class PLReportViewSet(BaseReportViewSet):
    serializer_class = PLReportSerializer
    report_builder_class = PLReportBuilder


class SimpleMultipliersReportViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer(self, *args, **kwargs):
        kwargs['context'] = self.get_serializer_context()
        return SimpleMultipliersReportSerializer(*args, **kwargs)

    def get_serializer_context(self):
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        builder = SimpleMultipliersReportBuilder(instance=instance)
        instance = builder.build()
        serializer = self.get_serializer(instance=instance, many=False)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
