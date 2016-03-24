from __future__ import unicode_literals

from django.contrib.auth.models import User
from rest_framework import permissions
from rest_framework.decorators import detail_route, list_route
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from reversion import revisions as reversion

from poms.audit.models import VersionInfo
from poms.audit.serializers import VersionSerializer
from poms.users.fields import get_master_user


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

            master_user = get_master_user(request)
            reversion.add_meta(VersionInfo, master_user=master_user, username=request.user.username)

    @list_route()
    def deleted(self, request, pk=None):
        master_user = get_master_user(request)
        if master_user is None:
            raise PermissionDenied()

        model = self.get_queryset().model
        deleted_list = reversion.get_deleted(model).filter(revision__info__master_user=master_user)
        return self._make_historical_reponse(model, deleted_list)

    @detail_route()
    def history(self, request, pk=None):
        master_user = get_master_user(request)
        if master_user is None:
            raise PermissionDenied()

        instance = self.get_object()
        version_list = reversion.get_for_object(instance)
        model = self.get_queryset().model
        return self._make_historical_reponse(model, version_list)

    def _get_fields(self, model):
        fields = [field for field in model._meta.fields]
        concrete_model = model._meta.concrete_model
        fields += concrete_model._meta.many_to_many
        return fields

    def _history_annotate_object(self, model, fields, versions):
        for v in versions:
            print(v.serialized_data)
            print(v.field_dict)

            # obj = v.object_version.object # deserialize m2m as current value :(

            obj = model()
            for field in fields:
                # print(repr(field))
                setattr(obj, field.name, v.field_dict.get(field.name, None))

            serializer = self.get_serializer(instance=obj)
            try:
                v.object_json = serializer.data
            except (KeyError, AttributeError):
                v.object_json = None

    def _make_historical_reponse(self, model, versions):
        fields = self._get_fields(model)
        queryset = versions.select_related('content_type', 'revision__user').prefetch_related('revision__info')

        page = self.paginate_queryset(queryset)
        if page is not None:
            self._history_annotate_object(model, fields, page)

            serializer = VersionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        self._history_annotate_object(model, fields, queryset)
        serializer = VersionSerializer(queryset, many=True)
        return Response(serializer.data)
