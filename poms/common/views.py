from __future__ import unicode_literals

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import permissions
from rest_framework.filters import DjangoFilterBackend, OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet, ViewSet

from poms.audit.mixins import HistoricalModelMixin
from poms.common.filters import ByIdFilterBackend, ByIsDeletedFilterBackend
from poms.common.mixins import BulkModelMixin, DestroyModelFakeMixin, UpdateModelMixinExt
from poms.users.utils import get_master_user_and_member


class AbstractApiView(APIView):
    def perform_authentication(self, request):
        super(AbstractApiView, self).perform_authentication(request)
        if request.user.is_authenticated():
            request.user.member, request.user.master_user = get_master_user_and_member(request)

    def initial(self, request, *args, **kwargs):
        super(AbstractApiView, self).initial(request, *args, **kwargs)

        if request.user.is_authenticated():
            master_user = request.user.master_user
            if master_user and master_user.timezone:
                timezone.activate(master_user.timezone)
            else:
                timezone.activate(settings.TIME_ZONE)

    def dispatch(self, request, *args, **kwargs):
        if request.method.upper() in permissions.SAFE_METHODS:
            return super(AbstractApiView, self).dispatch(request, *args, **kwargs)
        else:
            with transaction.atomic():
                return super(AbstractApiView, self).dispatch(request, *args, **kwargs)


class AbstractViewSet(AbstractApiView, ViewSet):
    serializer_class = None
    permission_classes = [
        IsAuthenticated
    ]

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


class AbstractModelViewSet(AbstractApiView, HistoricalModelMixin, UpdateModelMixinExt, DestroyModelFakeMixin,
                           BulkModelMixin, ModelViewSet):
    permission_classes = [
        IsAuthenticated
    ]
    filter_backends = [
        ByIdFilterBackend,
        ByIsDeletedFilterBackend,
        DjangoFilterBackend,
        OrderingFilter,
    ]


class AbstractReadOnlyModelViewSet(AbstractApiView, HistoricalModelMixin, ReadOnlyModelViewSet):
    permission_classes = [
        IsAuthenticated
    ]
    filter_backends = [
        ByIdFilterBackend,
        DjangoFilterBackend,
        OrderingFilter,
    ]


class AbstractClassModelViewSet(AbstractReadOnlyModelViewSet):
    ordering_fields = ['name']
    filter_fields = ['system_code', 'name']
    pagination_class = None
