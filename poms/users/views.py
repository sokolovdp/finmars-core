from __future__ import unicode_literals

from django.contrib.auth import login, logout
from django.contrib.auth.models import User, Group
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.filters import BaseFilterBackend
from rest_framework.mixins import UpdateModelMixin, DestroyModelMixin
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, BasePermission, SAFE_METHODS
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet, ModelViewSet, ReadOnlyModelViewSet

from poms.api.mixins import DbTransactionMixin
from poms.audit.mixins import HistoricalMixin
from poms.users.fields import GroupOwnerByMasterUserFilter
from poms.users.fields import get_master_user
from poms.users.filters import OwnerByMasterUserFilter
from poms.users.models import MasterUser, Member
from poms.users.serializers import GroupSerializer, UserSerializer, MasterUserSerializer, MemberSerializer


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


# class IsAdminUser(BasePermission):
#     def has_object_permission(self, request, view, obj):
#         return request.user and hasattr(request.user, 'profile') and request.user.profile.is_admin


# class GuardByUserFilter(BaseFilterBackend):
#     def filter_queryset(self, request, queryset, view):
#         user = request.user
#         return queryset.filter(user)
#
#
# class GuardByMasterUserFilter(BaseFilterBackend):
#     def filter_queryset(self, request, queryset, view):
#         user = request.user
#         return queryset.filter(master_user__in=user.member_of.all())
#
#


class UserPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method.upper() in SAFE_METHODS:
            return True
        user = request.user
        return user.id == obj.id


class UserFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        master_user = get_master_user(request)
        return queryset.filter(member_of=master_user)


class UserViewSet(DbTransactionMixin, HistoricalMixin, UpdateModelMixin, DestroyModelMixin, ReadOnlyModelViewSet):
    queryset = User.objects
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, UserPermission]
    filter_backends = [UserFilter]

    def retrieve(self, request, *args, **kwargs):
        # super(UserViewSet, self).retrieve(request, *args, **kwargs)
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        if self.kwargs[lookup_url_kwarg] == 'me':
            instance = request.user
        else:
            instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class MasterUserFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        user = request.user
        return queryset.filter(members=user)


class MasterUserViewSet(DbTransactionMixin, HistoricalMixin, ModelViewSet):
    queryset = MasterUser.objects.filter()
    serializer_class = MasterUserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [MasterUserFilter]


class MemberViewSet(DbTransactionMixin, HistoricalMixin, ModelViewSet):
    queryset = Member.objects.filter()
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [OwnerByMasterUserFilter]


# class GroupViewSet(DbTransactionMixin, ModelViewSet):
#     queryset = GroupProfile.objects.prefetch_related('group__permissions', 'group__permissions__content_type'). \
#         select_related('group')
#     serializer_class = GroupSerializer
#     permission_classes = [IsAuthenticated]
#     filter_backends = [OwnerByMasterUserFilter]

class GroupViewSet(DbTransactionMixin, HistoricalMixin, ModelViewSet):
    queryset = Group.objects.prefetch_related('profile', 'profile__master_user', 'permissions',
                                              'permissions__content_type')
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [GroupOwnerByMasterUserFilter]
