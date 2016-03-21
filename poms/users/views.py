from __future__ import unicode_literals

from django.contrib.auth import login, logout
from django.contrib.auth.models import Permission, Group, User
from django.contrib.contenttypes.models import ContentType
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED
from rest_framework.viewsets import ViewSet, ReadOnlyModelViewSet, ModelViewSet

from poms.api.mixins import DbTransactionMixin
from poms.users.serializers import PermissionSerializer, ContentTypeSerializer, GroupSerializer, UserSerializer, \
    ObjectPermissionSerializer


class ObtainAuthTokenViewSet(DbTransactionMixin, ViewSet):
    parser_classes = (FormParser, MultiPartParser, JSONParser,)
    serializer_class = AuthTokenSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        Token.objects.filter(user=user).delete()
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})


class LoginViewSet(DbTransactionMixin, ViewSet):
    permission_classes = ()
    parser_classes = (FormParser, MultiPartParser, JSONParser,)
    serializer_class = AuthTokenSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        return Response({'success': True})


class LogoutViewSet(DbTransactionMixin, ViewSet):
    def create(self, request, *args, **kwargs):
        logout(request)
        return Response({'success': True})


AVAILABLE_APPS = ['accounts', 'counterparties', 'currencies', 'instruments', 'portfolios', 'strategies', 'transactions',
                  'reports', 'users']


# class IsAdminUser(BasePermission):
#     def has_object_permission(self, request, view, obj):
#         return request.user and hasattr(request.user, 'profile') and request.user.profile.is_admin


class ContentTypeViewSet(DbTransactionMixin, ReadOnlyModelViewSet):
    queryset = ContentType.objects.filter(app_label__in=AVAILABLE_APPS)
    serializer_class = ContentTypeSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None


class PermissionViewSet(DbTransactionMixin, ReadOnlyModelViewSet):
    queryset = Permission.objects.filter(content_type__app_label__in=AVAILABLE_APPS)
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None


class GroupViewSet(DbTransactionMixin, ModelViewSet):
    queryset = Group.objects.filter(profile__isnull=False)
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None


class UserViewSet(DbTransactionMixin, ModelViewSet):
    queryset = User.objects.filter(id__gt=0)
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def retrieve(self, request, *args, **kwargs):
        # super(UserViewSet, self).retrieve(request, *args, **kwargs)
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        if self.kwargs[lookup_url_kwarg] == 'me':
            instance = request.user
        else:
            instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class ObjectPermissionViewSet(DbTransactionMixin, ViewSet):
    serializer_class = ObjectPermissionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer([], many=True)
        return Response(serializer.data)

    def get_object(self):
        pk = self.kwargs['pk']
        content_type_pk, object_pk = str(pk).split('__')
        print(content_type_pk, object_pk)
        return content_type_pk, object_pk

    def create(self, request, *args, **kwargs):
        return Response({}, status=HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        return Response({})

    def update(self, request, *args, **kwargs):
        return Response({})

    def delete(self, request, *args, **kwargs):
        return Response({})

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)

    def get_serializer_class(self):
        return self.serializer_class

    def get_serializer_context(self):
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }
