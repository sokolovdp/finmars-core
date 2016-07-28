from __future__ import unicode_literals

from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django_filters import MethodFilter
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.decorators import detail_route
from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter, FilterSet
from rest_framework.mixins import UpdateModelMixin, DestroyModelMixin
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from poms.audit.mixins import HistoricalMixin
from poms.common import pagination
from poms.common.filters import CharFilter
from poms.common.pagination import BigPagination
from poms.common.views import AbstractModelViewSet, AbstractReadOnlyModelViewSet
from poms.users.filters import OwnerByMasterUserFilter, MasterUserFilter
from poms.users.models import MasterUser, Member, Group
from poms.users.permissions import SuperUserOrReadOnly, IsCurrentMasterUser, IsCurrentUser
from poms.users.serializers import GroupSerializer, UserSerializer, MasterUserSerializer, MemberSerializer, \
    PingSerializer, UserSetPasswordSerializer, MasterUserSetCurrentSerializer, UserUnsubscribeSerializer
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
    permission_classes = [IsAuthenticated]


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


class UserViewSet(HistoricalMixin, UpdateModelMixin, AbstractReadOnlyModelViewSet):
    queryset = User.objects
    serializer_class = UserSerializer
    permission_classes = [
        # IsAuthenticated,
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
        # IsAuthenticated,
        IsCurrentMasterUser,
        SuperUserOrReadOnly,
    ]
    filter_backends = [
        MasterUserFilter,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    ordering_fields = ['name', ]
    search_fields = ['name', ]
    pagination_class = BigPagination

    @detail_route(methods=('PUT', 'PATCH',), url_path='set-current', permission_classes=[IsAuthenticated],
                  serializer_class=MasterUserSetCurrentSerializer)
    def set_current(self, request, pk=None):
        instance = self.get_object()
        set_master_user(request, instance)
        return Response({'success': True})


class MemberFilterSet(FilterSet):
    is_deleted = MethodFilter(action='filter_is_deleted')
    username = CharFilter()

    class Meta:
        model = Member
        fields = ['is_deleted']

    def filter_is_deleted(self, qs, value):
        # if value = 1
        return qs


class MemberViewSet(HistoricalMixin, UpdateModelMixin, DestroyModelMixin, AbstractReadOnlyModelViewSet):
    queryset = Member.objects.select_related('user').prefetch_related('groups')
    serializer_class = MemberSerializer
    permission_classes = AbstractModelViewSet.permission_classes + [
        # IsAuthenticated,
        SuperUserOrReadOnly
    ]
    filter_backends = AbstractReadOnlyModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    filter_class = MemberFilterSet
    ordering_fields = ['username', ]
    search_fields = ['username', ]
    pagination_class = BigPagination


class GroupFilterSet(FilterSet):
    name = CharFilter()

    class Meta:
        model = Group
        fields = ['name', ]


class GroupViewSet(AbstractModelViewSet):
    queryset = Group.objects.select_related('master_user').prefetch_related('members')
    serializer_class = GroupSerializer
    permission_classes = AbstractModelViewSet.permission_classes + [
        # IsAuthenticated,
        SuperUserOrReadOnly
    ]
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    ordering_fields = ['name', ]
    search_fields = ['name', ]
    pagination_class = BigPagination
