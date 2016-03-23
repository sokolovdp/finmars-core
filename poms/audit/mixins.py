from __future__ import unicode_literals

from rest_framework import permissions
from rest_framework.decorators import detail_route, list_route
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from reversion import revisions as reversion

from poms.audit.models import VersionInfo
from poms.audit.serializers import VersionSerializer


class HistoricalMixin(object):
    def dispatch(self, request, *args, **kwargs):
        self._reversion_is_active = False
        if request.method.upper() in permissions.SAFE_METHODS:
            return super(HistoricalMixin, self).dispatch(request, *args, **kwargs)
        else:
            self._reversion_is_active = True
            with reversion.create_revision():
                return super(HistoricalMixin, self).dispatch(request, *args, **kwargs)

    def initial(self, request, *args, **kwargs):
        super(HistoricalMixin, self).initial(request, *args, **kwargs)

        if self._reversion_is_active:
            reversion.set_user(request.user)
            reversion.set_ignore_duplicates(True)

            profile = getattr(request.user, 'profile', None)
            master_user = getattr(profile, 'master_user', None)
            if master_user:
                reversion.add_meta(VersionInfo, master_user=master_user, username=request.user.username)

    @list_route()
    def deleted(self, request, pk=None):
        profile = getattr(request.user, 'profile', None)
        master_user = getattr(profile, 'master_user', None)
        if master_user is None:
            raise PermissionDenied()

        model = self.get_queryset().model
        deleted_list = reversion.get_deleted(model).filter(revision__info__master_user=master_user)
        return self._make_historical_reponse(deleted_list)

    @detail_route()
    def history(self, request, pk=None):
        profile = getattr(request.user, 'profile', None)
        master_user = getattr(profile, 'master_user', None)
        if master_user is None:
            raise PermissionDenied()

        instance = self.get_object()
        version_list = reversion.get_for_object(instance)
        return self._make_historical_reponse(version_list)

    def _history_annotate_object(self, versions):
        for v in versions:
            instance = v.object_version.object
            serializer = self.get_serializer(instance=instance)
            try:
                v.object_json = serializer.data
            except (KeyError, AttributeError):
                v.object_json = None

    def _make_historical_reponse(self, versions):
        queryset = versions.select_related('content_type', 'revision__user').prefetch_related('revision__info')

        page = self.paginate_queryset(queryset)
        if page is not None:
            self._history_annotate_object(page)

            serializer = VersionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        self._history_annotate_object(queryset)
        serializer = VersionSerializer(queryset, many=True)
        return Response(serializer.data)
