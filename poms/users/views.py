from __future__ import unicode_literals

import django_filters
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.decorators import detail_route
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import FilterSet
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from poms.common.filters import CharFilter, NoOpFilter
from poms.common.pagination import BigPagination
from poms.common.views import AbstractModelViewSet, AbstractApiView
from poms.users.filters import OwnerByMasterUserFilter, MasterUserFilter
from poms.users.models import MasterUser, Member, Group
from poms.users.permissions import SuperUserOrReadOnly, IsCurrentMasterUser, IsCurrentUser
from poms.users.serializers import GroupSerializer, UserSerializer, MasterUserSerializer, MemberSerializer, \
    PingSerializer, UserSetPasswordSerializer, MasterUserSetCurrentSerializer, UserUnsubscribeSerializer, \
    UserRegisterSerializer
from poms.users.utils import set_master_user


class ObtainAuthTokenViewSet(AbstractApiView, ViewSet):
    parser_classes = (FormParser, MultiPartParser, JSONParser,)
    serializer_class = AuthTokenSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        Token.objects.filter(user=user).delete()
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})


class PingViewSet(AbstractApiView, ViewSet):
    permission_classes = [AllowAny, ]

    @method_decorator(ensure_csrf_cookie)
    def list(self, request, *args, **kwargs):
        serializer = PingSerializer(instance={
            'message': 'pong',
            'version': request.version,
            'is_authenticated': request.user.is_authenticated(),
            'is_anonymous': request.user.is_anonymous(),
            'now': timezone.template_localtime(timezone.now()),
        })
        return Response(serializer.data)


class ProtectedPingViewSet(PingViewSet):
    permission_classes = [IsAuthenticated, ]


class LoginViewSet(ViewSet):
    permission_classes = []
    parser_classes = [FormParser, MultiPartParser, JSONParser, ]
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


class UserRegisterViewSet(AbstractApiView, ViewSet):
    serializer_class = UserRegisterSerializer
    permission_classes = []
    authentication_classes = []

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.save()
        user = validated_data['user']
        login(request, user)
        return Response({'success': True})


class UserViewSet(AbstractModelViewSet):
    queryset = User.objects
    serializer_class = UserSerializer
    permission_classes = AbstractModelViewSet.permission_classes + [
        IsCurrentUser,
    ]

    # filter_backends = AbstractReadOnlyModelViewSet.filter_backends + [
    #     UserFilter
    # ]

    # def get_serializer_class(self):
    #     # print(self.action)
    #     # print(self.request.method)
    #     if self.action == 'change_password':
    #         return UserSetPasswordSerializer
    #     return super(UserViewSet, self).get_serializer_class()

    def get_queryset(self):
        qs = super(UserViewSet, self).get_queryset()
        qs = qs.filter(id=self.request.user.id)
        return qs

    def get_object(self):
        return self.request.user

    def create(self, request, *args, **kwargs):
        raise PermissionDenied()

    @detail_route(methods=('PUT',), url_path='set-password', serializer_class=UserSetPasswordSerializer)
    def set_password(self, request, pk=None):
        # user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # return Response(serializer.data)
        return Response()

    @detail_route(methods=('PUT',), url_path='unsubscribe', serializer_class=UserUnsubscribeSerializer)
    def unsubscribe(self, request, pk=None):
        # user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # return Response(serializer.data)
        return Response()


class MasterUserViewSet(AbstractModelViewSet):
    queryset = MasterUser.objects
    serializer_class = MasterUserSerializer
    permission_classes = AbstractModelViewSet.permission_classes + [
        IsCurrentMasterUser,
        SuperUserOrReadOnly,
    ]
    filter_backends = AbstractModelViewSet.filter_backends + [
        MasterUserFilter,
    ]
    ordering_fields = ['name', ]
    search_fields = ['name', ]
    pagination_class = BigPagination

    def get_object(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs[lookup_url_kwarg]
        if lookup_value == '0':
            return self.request.user.master_user
        return super(MasterUserViewSet, self).get_object()

    def create(self, request, *args, **kwargs):
        raise PermissionDenied()

    @detail_route(methods=('PUT', 'PATCH',), url_path='set-current', permission_classes=[IsAuthenticated],
                  serializer_class=MasterUserSetCurrentSerializer)
    def set_current(self, request, pk=None):
        instance = self.get_object()
        set_master_user(request, instance)
        return Response({'success': True})


class MemberFilterSet(FilterSet):
    id = NoOpFilter()
    is_deleted = django_filters.BooleanFilter()
    username = CharFilter()

    class Meta:
        model = Member
        fields = []


class MemberViewSet(AbstractModelViewSet):
    queryset = Member.objects.prefetch_related('user', 'groups')
    serializer_class = MemberSerializer
    permission_classes = AbstractModelViewSet.permission_classes + [
        SuperUserOrReadOnly,
    ]
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]
    filter_class = MemberFilterSet
    ordering_fields = ['username', ]
    search_fields = ['username', ]
    pagination_class = BigPagination
    # has_feature_is_deleted = True

    def get_object(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs[lookup_url_kwarg]
        if lookup_value == '0':
            return self.request.user.member
        return super(MemberViewSet, self).get_object()

    def create(self, request, *args, **kwargs):
        raise PermissionDenied()


class GroupFilterSet(FilterSet):
    id = NoOpFilter()
    name = CharFilter()

    class Meta:
        model = Group
        fields = []


class GroupViewSet(AbstractModelViewSet):
    queryset = Group.objects.prefetch_related('master_user', 'members')
    serializer_class = GroupSerializer
    permission_classes = AbstractModelViewSet.permission_classes + [
        SuperUserOrReadOnly,
    ]
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]
    ordering_fields = ['name', ]
    search_fields = ['name', ]
    pagination_class = BigPagination
