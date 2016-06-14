from __future__ import unicode_literals

from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.decorators import detail_route
from rest_framework.mixins import UpdateModelMixin, DestroyModelMixin
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, BasePermission, SAFE_METHODS, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet, ModelViewSet, ReadOnlyModelViewSet

from poms.audit.mixins import HistoricalMixin
from poms.users.fields import GroupOwnerByMasterUserFilter
from poms.users.filters import OwnerByMasterUserFilter, MasterUserFilter, UserFilter
from poms.users.models import MasterUser, Member, Group
from poms.users.permissions import SuperUserOrReadOnly
from poms.users.serializers import GroupSerializer, UserSerializer, MasterUserSerializer, MemberSerializer
from poms.users.utils import set_master_user


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


class PingViewSet(ViewSet):
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        return Response({
            'message': 'pong',
            'version': request.version,
        })


class ProtectedPingViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        return Response({
            'message': 'pong',
            'version': request.version,
        })


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


class UserPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method.upper() in SAFE_METHODS:
            return True
        user = request.user
        return user.id == obj.id


class UserViewSet(HistoricalMixin, UpdateModelMixin, ReadOnlyModelViewSet):
    queryset = User.objects
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, UserPermission]
    filter_backends = [UserFilter]

    def get_queryset(self):
        qs = super(UserViewSet, self).get_queryset()
        qs = qs.filter(id=self.request.user.id)
        return qs

    def retrieve(self, request, *args, **kwargs):
        # super(UserViewSet, self).retrieve(request, *args, **kwargs)
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        if self.kwargs[lookup_url_kwarg] == 'me':
            instance = request.user
        else:
            instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class MasterUserPermission(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return request.user.master_user.id == obj.id


class MasterUserViewSet(HistoricalMixin, ModelViewSet):
    queryset = MasterUser.objects
    serializer_class = MasterUserSerializer
    permission_classes = [IsAuthenticated, SuperUserOrReadOnly, MasterUserPermission]
    filter_backends = [MasterUserFilter]

    @detail_route()
    def set_current(self, request, pk=None):
        instance = self.get_object()
        set_master_user(request, instance)
        return Response({
            'status': 'OK',
            'master_user': instance.pk,
        })


class MemberViewSet(HistoricalMixin, UpdateModelMixin, DestroyModelMixin, ReadOnlyModelViewSet):
    queryset = Member.objects.select_related('user')
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticated, SuperUserOrReadOnly]
    filter_backends = [OwnerByMasterUserFilter]


class GroupViewSet(HistoricalMixin, ModelViewSet):
    queryset = Group.objects.select_related('master_user')
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated, SuperUserOrReadOnly]
    filter_backends = [GroupOwnerByMasterUserFilter]
