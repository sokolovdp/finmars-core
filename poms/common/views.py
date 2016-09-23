from __future__ import unicode_literals

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import ProtectedError
from django.utils import timezone
from django.utils.translation import ugettext_lazy
from rest_framework import permissions
from rest_framework import status
from rest_framework.decorators import list_route
from rest_framework.exceptions import MethodNotAllowed, ValidationError, PermissionDenied
from rest_framework.filters import DjangoFilterBackend, OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet, ViewSet

from poms.audit import history
from poms.common.filters import ByIdFilterBackend, ByIsDeletedFilterBackend
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

    @history.enable
    def perform_create(self, serializer):
        history.set_flag_addition()
        super(AbstractApiView, self).perform_create(serializer)
        history.set_actor_content_object(serializer.instance)

    @history.enable
    def perform_update(self, serializer):
        history.set_flag_change()
        history.set_actor_content_object(serializer.instance)
        super(AbstractApiView, self).perform_update(serializer)

    @history.enable
    def perform_destroy(self, instance):
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
        ByIdFilterBackend,
        ByIsDeletedFilterBackend,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]

    # def get_queryset(self):
    #     qs = super(AbstractModelViewSet, self).get_queryset()
    #     if getattr(self, 'has_feature_is_deleted', False):
    #         is_deleted = self.request.query_params.get('is_deleted', None)
    #         if is_deleted is None:
    #             if getattr(self, 'action', '') == 'list':
    #                 qs = qs.filter(is_deleted=False)
    #     return qs

    def get_serializer(self, *args, **kwargs):
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
                api_settings.NON_FIELD_ERRORS_KEY: ugettext_lazy(
                    'Cannot delete instance because they are referenced through a protected foreign key'),
            }, status=status.HTTP_409_CONFLICT)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        if getattr(self, 'has_feature_is_deleted', False):
            with history.enable():
                history.set_flag_deletion()
                history.set_actor_content_object(instance)
                instance.fake_delete()
        else:
            super(AbstractModelViewSet, self).perform_destroy(instance)

    @list_route(methods=['post', 'put', 'patch', 'delete'], url_path='bulk')
    def bulk_ops(self, request):
        method = request.method.lower()

        if method == 'post':
            return self.bulk_create(request)
        elif method in ['put', 'patch']:
            return self.bulk_update(request)
        elif method in ['delete']:
            return self.bulk_delete(request)

        raise MethodNotAllowed(request.method)

    @list_route(methods=['post'], url_path='bulk-create')
    def bulk_create(self, request):
        data = request.data
        if not isinstance(data, list):
            raise ValidationError(ugettext_lazy('Required list'))

        has_error = False
        serializers = []
        for adata in data:
            serializer = self.get_serializer(data=adata)
            if not serializer.is_valid(raise_exception=False):
                has_error = True
            serializers.append(serializer)

        if has_error:
            errors = []
            for serializer in serializers:
                errors.append(serializer.errors)
            raise ValidationError(errors)
        else:
            instances = []
            for serializer in serializers:
                self.perform_create(serializer)
                instances.append(serializer.instance)
            ret_serializer = self.get_serializer(instance=instances, many=True)
            return Response(list(ret_serializer.data), status=status.HTTP_201_CREATED)

    @list_route(methods=['put', 'patch'], url_path='bulk-update')
    def bulk_update(self, request):
        data = request.data
        if not isinstance(data, list):
            raise ValidationError(ugettext_lazy('Required list'))

        partial = request.method.lower() == 'patch'
        queryset = self.filter_queryset(self.get_queryset())

        has_error = False
        serializers = []
        for adata in data:
            pk = adata['id']
            try:
                instance = queryset.get(pk=pk)
            except ObjectDoesNotExist:
                has_error = True
                serializers.append(None)
            else:
                try:
                    self.check_object_permissions(request, instance)
                except PermissionDenied:
                    raise

                serializer = self.get_serializer(instance=instance, data=adata, partial=partial)
                if not serializer.is_valid(raise_exception=False):
                    has_error = True
                serializers.append(serializer)

        if has_error:
            errors = []
            for serializer in serializers:
                if serializer:
                    errors.append(serializer.errors)
                else:
                    errors.append({
                        api_settings.NON_FIELD_ERRORS_KEY: ugettext_lazy('Not Found')
                    })
            raise ValidationError(errors)
        else:
            instances = []
            for serializer in serializers:
                self.perform_update(serializer)
                instances.append(serializer.instance)

            ret_serializer = self.get_serializer(
                instance=queryset.filter(pk__in=(i.id for i in instances)), many=True)
            return Response(list(ret_serializer.data), status=status.HTTP_200_OK)

    @list_route(methods=['post', 'put', 'patch'], url_path='bulk-save')
    def bulk_save(self, request):
        data = request.data
        if not isinstance(data, list):
            raise ValidationError(ugettext_lazy('Required list'))

        partial = request.method.lower() == 'patch'
        queryset = self.filter_queryset(self.get_queryset())

        has_error = False
        serializers = []
        for adata in data:
            pk = adata.get('id', None)
            if pk is None:
                serializer = self.get_serializer(data=adata)
                if not serializer.is_valid(raise_exception=False):
                    has_error = True
                serializers.append(serializer)
            else:
                try:
                    instance = queryset.get(pk=pk)
                except ObjectDoesNotExist:
                    has_error = True
                    serializers.append(None)
                else:
                    try:
                        self.check_object_permissions(request, instance)
                    except PermissionDenied:
                        raise
                    serializer = self.get_serializer(instance=instance, data=adata, partial=partial)
                    if not serializer.is_valid(raise_exception=False):
                        has_error = True
                    serializers.append(serializer)

        if has_error:
            errors = []
            for serializer in serializers:
                if serializer:
                    errors.append(serializer.errors)
                else:
                    errors.append({
                        api_settings.NON_FIELD_ERRORS_KEY: ugettext_lazy('Not Found')
                    })
            raise ValidationError(errors)
        else:
            instances = []
            for serializer in serializers:
                if serializer.instance is None:
                    self.perform_create(serializer)
                else:
                    self.perform_update(serializer)
                instances.append(serializer.instance)

            ret_serializer = self.get_serializer(
                instance=queryset.filter(pk__in=(i.id for i in instances)), many=True)
            return Response(list(ret_serializer.data), status=status.HTTP_200_OK)

    @list_route(methods=['get', 'delete'], url_path='bulk-delete')
    def bulk_delete(self, request):
        if request.method.lower() == 'get':
            return self.list(request)

        queryset = self.filter_queryset(self.get_queryset())

        data = request.data
        if data is not None and data:
            if not isinstance(data, list):
                raise ValidationError(ugettext_lazy('Required list'))
            pk_set = []
            for adata in data:
                if isinstance(data, dict):
                    pk_set.append(adata['id'])
                elif isinstance(data, (int, float)):
                    pk_set.append(int(data))
            if pk_set:
                queryset = queryset.filter(pk__in=pk_set)

        for instance in queryset:
            try:
                self.check_object_permissions(request, instance)
            except PermissionDenied:
                raise
            self.perform_destroy(instance)

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
