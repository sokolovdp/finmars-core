from __future__ import unicode_literals

from django.utils.translation import ugettext as _
from rest_framework import permissions
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from reversion import revisions as reversion

from poms.audit import history
from poms.audit.models import VersionInfo
from poms.audit.serializers import VersionSerializer
from poms.users.fields import get_master_user


# class HistoricalPageNumberPagination(PageNumberPagination):
#     page_size_query_param = 'size'
#     page_size = 5
#     max_page_size = 10


# TODO: request is to hard for DB, can't prefetch or any optimization
class HistoricalMixin(object):
    ignore_duplicate_revisions = False
    history_latest_first = True

    # history_pagination_class = HistoricalPageNumberPagination

    def dispatch(self, request, *args, **kwargs):
        self._reversion_is_active = False
        if request.method.upper() in permissions.SAFE_METHODS:
            return super(HistoricalMixin, self).dispatch(request, *args, **kwargs)
        else:
            self._reversion_is_active = True
            with reversion.create_revision(), history.enable():
                response = super(HistoricalMixin, self).dispatch(request, *args, **kwargs)
                if not reversion.get_comment():
                    reversion.set_comment(_('No fields changed.'))
                return response

    def initial(self, request, *args, **kwargs):
        super(HistoricalMixin, self).initial(request, *args, **kwargs)

        if self._reversion_is_active:
            reversion.set_user(request.user)
            # reversion.set_ignore_duplicates(True)

            master_user = get_master_user(request)
            reversion.add_meta(VersionInfo, master_user=master_user, username=request.user.username)

    @list_route()
    def deleted(self, request, pk=None):
        master_user = get_master_user(request)
        model = self.get_queryset().model
        deleted_list = reversion.get_deleted(model).filter(revision__info__master_user=master_user)

        self._version_id = request.query_params.get('version_id')
        if self._version_id:
            deleted_list = deleted_list.filter(pk=self._version_id)

        return self._make_historical_reponse(deleted_list)

    @detail_route()
    def history(self, request, pk=None):
        # instance = self.get_object()
        # version_list = reversion.get_for_object(instance)

        master_user = get_master_user(request)
        model = self.get_queryset().model
        version_list = reversion.get_for_object_reference(model, pk).filter(revision__info__master_user=master_user)

        self._version_id = request.query_params.get('version_id')
        if self._version_id:
            version_list = version_list.filter(pk=self._version_id)

        return self._make_historical_reponse(version_list)

    # def _get_fields(self, model):
    #     fields = [field for field in model._meta.fields]
    #     concrete_model = model._meta.concrete_model
    #     fields += concrete_model._meta.many_to_many
    #     return fields

    def _history_load_object(self, version):
        # TODO: load one-to-one from history, currently loaded from db
        # TODO: show many-to-many from history, currently loaded from db
        if version and self._version_id:
            serializer = self.get_serializer(instance=history.ModelProxy(version))
            version.object_json = serializer.data

    def _history_load_objects(self, versions):
        if self._version_id:
            for v in versions:
                self._history_load_object(v)

    def _make_historical_reponse(self, versions):
        queryset = versions.select_related('content_type', 'revision__user').prefetch_related('revision__info')

        if self._version_id:
            version = queryset.first()
            self._history_load_object(version)
            serializer = VersionSerializer(version)
            return Response(serializer.data)

        if self.history_latest_first:
            queryset = queryset.order_by("-pk")
        else:
            queryset = queryset.order_by("pk")

        page = self.paginate_queryset(queryset)
        if page is not None:
            self._history_load_objects(page)
            serializer = VersionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        self._history_load_objects(queryset)
        serializer = VersionSerializer(queryset, many=True)
        return Response(serializer.data)

        # @cached_property
        # def _historical_paginator(self):
        #     if self.history_pagination_class:
        #         return self.history_pagination_class()
        #     return self.pagination_class()
        #
        # def _historical_paginate_queryset(self, queryset):
        #     if self._historical_paginator is None:
        #         return None
        #     return self._historical_paginator.paginate_queryset(queryset, self.request, view=self)
        #
        #     # return self.paginate_queryset(queryset)
        #
        # def _historical_get_paginated_response(self, data):
        #     assert self._historical_paginator is not None
        #     return self._historical_paginator.get_paginated_response(data)
