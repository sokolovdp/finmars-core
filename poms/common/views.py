from __future__ import unicode_literals

from django.conf import settings
from django.db import transaction
from django.db.models import ProtectedError
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from rest_framework import permissions
from rest_framework import status
from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet, ViewSet

from poms.audit.mixins import HistoricalMixin
from poms.users.utils import get_master_user
from poms.users.utils import get_member


class AbstractApiView(HistoricalMixin, APIView):
    atomic = True

    def perform_authentication(self, request):
        super(AbstractApiView, self).perform_authentication(request)
        if request.user.is_authenticated():
            request.user.master_user = get_master_user(request)
            request.user.member = get_member(request)

    def initial(self, request, *args, **kwargs):
        super(AbstractApiView, self).initial(request, *args, **kwargs)

        if request.user.is_authenticated():
            master_user = request.user.master_user
            if master_user and master_user.timezone:
                timezone.activate(master_user.timezone)
            else:
                timezone.activate(settings.TIME_ZONE)

    def dispatch(self, request, *args, **kwargs):
        if self.atomic:
            if request.method.upper() in permissions.SAFE_METHODS:
                return super(AbstractApiView, self).dispatch(request, *args, **kwargs)
            else:
                with transaction.atomic():
                    return super(AbstractApiView, self).dispatch(request, *args, **kwargs)
        else:
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


class AbstractModelViewSet(AbstractApiView, ModelViewSet):
    permission_classes = [
        IsAuthenticated
    ]
    filter_backends = [
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]

    def update(self, request, *args, **kwargs):
        response = super(AbstractModelViewSet, self).update(request, *args, **kwargs)
        # total reload object, due many to many don't correctly returned
        if response.status_code == status.HTTP_200_OK:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        return response

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
        except ProtectedError:
            return Response({
                'non_fields_error': _(
                    'Cannot delete instance because they are referenced through a protected foreign key'),
            }, status=status.HTTP_409_CONFLICT)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AbstractReadOnlyModelViewSet(AbstractApiView, ReadOnlyModelViewSet):
    permission_classes = [
        IsAuthenticated
    ]
    filter_backends = [
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter
    ]


class AbstractClassModelViewSet(AbstractReadOnlyModelViewSet):
    # ordering_fields = ['id', 'system_code', 'name', ]
    ordering_fields = []
    search_fields = ['system_code', 'name_en', ]
    pagination_class = None
