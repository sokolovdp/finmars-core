from __future__ import unicode_literals

from django.conf import settings
from django.db import transaction
from django.db.models import ProtectedError
from django.utils import timezone
from django.utils.translation import ugettext_lazy
from rest_framework import permissions
from rest_framework import status
from rest_framework.decorators import list_route
from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet, ViewSet

from poms.audit import history
from poms.audit.mixins import HistoricalMixin
from poms.common.serializers import BulkModelSerializer
from poms.users.utils import get_master_user
from poms.users.utils import get_member


class AbstractApiView(APIView):
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

    def perform_create(self, serializer):
        with history.enable():
            history.set_flag_addition()
            super(AbstractApiView, self).perform_create(serializer)
            history.set_actor_content_object(serializer.instance)

    def perform_update(self, serializer):
        with history.enable():
            history.set_flag_change()
            history.set_actor_content_object(serializer.instance)
            super(AbstractApiView, self).perform_update(serializer)

    def perform_destroy(self, instance):
        with history.enable():
            history.set_flag_deletion()
            history.set_actor_content_object(instance)
            super(AbstractApiView, self).perform_destroy(instance)


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

    def get_queryset(self):
        qs = super(AbstractModelViewSet, self).get_queryset()
        if getattr(self, 'has_feature_is_deleted', False):
            is_deleted = self.request.query_params.get('is_deleted', None)
            if is_deleted is None:
                if getattr(self, 'action', '') == 'list':
                    qs = qs.filter(is_deleted=False)
        return qs

    def get_serializer(self, *args, **kwargs):
        # if self.action == 'bulk_save':
        #     kwargs['child_serializer_class'] = self.serializer_class
        return super(AbstractModelViewSet, self).get_serializer(*args, **kwargs)

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
                'non_fields_error': ugettext_lazy(
                    'Cannot delete instance because they are referenced through a protected foreign key'),
            }, status=status.HTTP_409_CONFLICT)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        if getattr(self, 'has_feature_is_deleted', False):
            instance.fake_delete()
        else:
            super(AbstractModelViewSet, self).perform_destroy(instance)

    @list_route(methods=['post'], url_path='bulk-save')
    def bulk_save(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = BulkModelSerializer(child_serializer_class=self.serializer_class,
                                         queryset=queryset,
                                         data=request.data,
                                         context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        instances = serializer.save()
        return Response(serializer.to_representation(instances), status=status.HTTP_200_OK)


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
