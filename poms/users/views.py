from __future__ import unicode_literals

from django.contrib.auth import login, logout
from django.contrib.auth.models import Group, User
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet, ModelViewSet

from poms.api.mixins import DbTransactionMixin
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


# class ContentTypeViewSet(DbTransactionMixin, ReadOnlyModelViewSet):
#     queryset = ContentType.objects.filter(app_label__in=AVAILABLE_APPS)
#     serializer_class = ContentTypeSerializer
#     permission_classes = [IsAuthenticated]
#
#
# class PermissionViewSet(DbTransactionMixin, ReadOnlyModelViewSet):
#     queryset = Permission.objects.filter(content_type__app_label__in=AVAILABLE_APPS)
#     serializer_class = PermissionSerializer
#     permission_classes = [IsAuthenticated]
#     pagination_class = None


class GroupViewSet(DbTransactionMixin, ModelViewSet):
    queryset = Group.objects.prefetch_related('permissions', 'permissions__content_type').select_related('profile')
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]


class UserViewSet(DbTransactionMixin, ModelViewSet):
    queryset = User.objects.filter(id__gt=0)
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        # super(UserViewSet, self).retrieve(request, *args, **kwargs)
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        if self.kwargs[lookup_url_kwarg] == 'me':
            instance = request.user
        else:
            instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class MasterUserViewSet(DbTransactionMixin, ModelViewSet):
    queryset = MasterUser.objects.filter()
    serializer_class = MasterUserSerializer
    permission_classes = [IsAuthenticated]


class MemberViewSet(DbTransactionMixin, ModelViewSet):
    queryset = Member.objects.filter()
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticated]
