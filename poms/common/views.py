from __future__ import unicode_literals

import logging
from collections import OrderedDict

from celery.result import AsyncResult
from django.conf import settings
from django.core.signing import TimestampSigner
from django.db import transaction
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import DjangoFilterBackend, OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet, ViewSet

from poms.audit.mixins import HistoricalModelMixin
from poms.common.filters import ByIdFilterBackend, ByIsDeletedFilterBackend
from poms.common.mixins import BulkModelMixin, DestroyModelFakeMixin, UpdateModelMixinExt
from poms.users.utils import get_master_user_and_member


_l = logging.getLogger('poms.common')


class AbstractApiView(APIView):
    def perform_authentication(self, request):
        super(AbstractApiView, self).perform_authentication(request)
        if request.user.is_authenticated():
            request.user.member, request.user.master_user = get_master_user_and_member(request)

    def initial(self, request, *args, **kwargs):
        super(AbstractApiView, self).initial(request, *args, **kwargs)

        timezone.activate(settings.TIME_ZONE)
        if request.user.is_authenticated():
            master_user = request.user.master_user
            if master_user and master_user.timezone:
                timezone.activate(master_user.timezone)

    def dispatch(self, request, *args, **kwargs):
        if request.method.upper() in permissions.SAFE_METHODS:
            response = super(AbstractApiView, self).dispatch(request, *args, **kwargs)
            return self._mini_if_need(request, response)
        else:
            with transaction.atomic():
                response = super(AbstractApiView, self).dispatch(request, *args, **kwargs)
                return self._mini_if_need(request, response)

    def _mini_if_need(self, request, response):
        if '_mini' in request.GET:
            self._remove_object(response.data)
        return response

    def _remove_object(self, data):
        if isinstance(data, (list, tuple)):
            for i, v in enumerate(data):
                data[i] = self._remove_object(v)
        elif isinstance(data, (dict, OrderedDict)):
            for k, v in list(data.items()):
                if k.endswith('_object') or k in ['user_object_permissions', 'group_object_permissions']:
                    del data[k]
                else:
                    data[k] = self._remove_object(v)
        return data


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


class AbstractAsyncViewSet(AbstractViewSet):
    serializer_class = None
    celery_task = None

    def get_serializer_context(self):
        context = super(AbstractAsyncViewSet, self).get_serializer_context()
        context['show_object_permissions'] = False
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        task_id = instance.task_id

        signer = TimestampSigner()

        if task_id:
            res = AsyncResult(signer.unsign(task_id))

            # _l.info('res.ready() -> %s', res.ready())
            #
            # _l.info('0.instance -> %s', instance)
            # _l.info('0.instance.master_user -> %s', getattr(instance, 'master_user', None))

            if res.ready():
                res.maybe_reraise()
                instance = res.result

            # _l.info('instance -> %s', instance)
            # _l.info('instance.master_user -> %s', getattr(instance, 'master_user', None))
            # _l.info('request.user -> %s', request.user)
            # _l.info('request.user.master_user -> %s', getattr(request.user, 'master_user', None))
            # _l.info('self.request.user -> %s', self.request.user)
            # _l.info('self.request.user.master_user -> %s', getattr(self.request.user, 'master_user', None))

            if instance.master_user.id != request.user.master_user.id:
                raise PermissionDenied()
            instance.task_id = task_id
            instance.task_status = res.status
            serializer = self.get_serializer(instance=instance, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            res = self.celery_task.apply_async(kwargs={'instance': instance})
            instance.task_id = signer.sign('%s' % res.id)
            instance.task_status = res.status
            serializer = self.get_serializer(instance=instance, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)
