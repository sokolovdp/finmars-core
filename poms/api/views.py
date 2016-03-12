from __future__ import unicode_literals

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response


class PingViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        return Response({
            'messages': 'pong',
            'version': request.version,
        })


class ProtectedPingViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        return Response({
            'messages': 'pong',
            'version': request.version,
        })
