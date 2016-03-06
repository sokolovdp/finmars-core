from __future__ import unicode_literals

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from poms.reports.backends.balance import BalanceReportBuilder
from poms.reports.serializers import BalanceReportSerializer


class BalanceReportViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer(self, *args, **kwargs):
        kwargs['context'] = self.get_serializer_context()
        return BalanceReportSerializer(*args, **kwargs)

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
        builder = BalanceReportBuilder(instance=instance)
        instance = builder.build()
        serializer = self.get_serializer(instance=instance, many=False)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
