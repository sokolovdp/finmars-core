from __future__ import unicode_literals

from django.contrib.auth import login, logout
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet


class ObtainAuthTokenViewSet(ViewSet):
    parser_classes = (FormParser, MultiPartParser, JSONParser,)
    serializer_class = AuthTokenSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        Token.objects.filter(user=user).delete()
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})


class LoginViewSet(ViewSet):
    permission_classes = ()
    parser_classes = (FormParser, MultiPartParser, JSONParser,)
    serializer_class = AuthTokenSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        return Response({'success': True})


class LogoutViewSet(ViewSet):
    def create(self, request, *args, **kwargs):
        logout(request)
        return Response({'success': True})
