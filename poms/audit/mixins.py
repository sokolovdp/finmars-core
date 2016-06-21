from __future__ import unicode_literals

from django.utils.translation import ugettext as _
from rest_framework import permissions
from rest_framework.decorators import detail_route, list_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from reversion import revisions as reversion

from poms.audit import history
from poms.audit.models import VersionInfo
from poms.audit.serializers import VersionSerializer
from poms.users.permissions import SuperUserOnly


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
        self._history_is_active = False
        if request.method.upper() in permissions.SAFE_METHODS:
            return super(HistoricalMixin, self).dispatch(request, *args, **kwargs)
        else:
            self._history_is_active = True
            with reversion.create_revision(), history.enable():
                response = super(HistoricalMixin, self).dispatch(request, *args, **kwargs)
                if not reversion.get_comment():
                    reversion.set_comment(_('No fields changed.'))
                return response

    def initial(self, request, *args, **kwargs):
        super(HistoricalMixin, self).initial(request, *args, **kwargs)

        if self._history_is_active:
            reversion.set_user(request.user)
            # reversion.set_ignore_duplicates(True)

            # instance = self.get_object()
            # serializer = self.get_serializer(instance)
            # self._o1 = serializer.data
            #
            master_user = request.user.master_user
            reversion.add_meta(VersionInfo, master_user=master_user, username=request.user.username)

    def finalize_response(self, request, response, *args, **kwargs):
        # if self._history_is_active:
        #     try:
        #         instance = self.get_object()
        #         serializer = self.get_serializer(instance)
        #         self._o2 = serializer.data
        #     except ObjectDoesNotExist:
        #         self._o2 = None
        #     pprint.pprint(self._o1)
        #     pprint.pprint(self._o2)
        return super(HistoricalMixin, self).finalize_response(request, response, *args, **kwargs)

    @list_route(permission_classes=(IsAuthenticated, SuperUserOnly,))
    def deleted(self, request, pk=None):
        # master_user = get_master_user(request)
        master_user = request.user.master_user
        model = self.get_queryset().model
        deleted_list = reversion.get_deleted(model).filter(revision__info__master_user=master_user)

        self._version_id = request.query_params.get('version_id')
        if self._version_id:
            deleted_list = deleted_list.filter(pk=self._version_id)

        return self._make_historical_reponse(deleted_list)

    @detail_route(permission_classes=(IsAuthenticated, SuperUserOnly,))
    def history(self, request, pk=None):
        # instance = self.get_object()
        # version_list = reversion.get_for_object(instance)

        # master_user = get_master_user(request)
        master_user = request.user.master_user
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
        # TODO: show one-to-many from history, currently loaded from db
        # TODO: show many-to-one from history, currently loaded from db
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

# class BaseAuditModelMixin(object):
#     def get_object_data(self):
#         instance = self.get_object()
#         serializer = self.get_serializer(instance)
#         return serializer.data
#
#     def audit(self, data, changed=None):
#         pass
#
#
# class AuditCreateModelMixin(BaseAuditModelMixin, CreateModelMixin):
#     def create(self, request, *args, **kwargs):
#         response = super(AuditCreateModelMixin, self).create(request, *args, **kwargs)
#         self.audit(response.data)
#         return response
#
#
# class AuditUpdateModelMixin(BaseAuditModelMixin, UpdateModelMixin):
#     def __init__(self, **kwargs):
#         super(AuditUpdateModelMixin, self).__init__(**kwargs)
#         self._audit_object = False
#
#     def get_object(self):
#         if self._audit_object is None:
#             self._audit_object = super(AuditUpdateModelMixin, self).get_object()
#         return self._audit_object
#
#     def update(self, request, *args, **kwargs):
#         instance = self.get_object()
#         serializer = self.get_serializer(instance)
#         readed_data = serializer.data
#
#         response = super(AuditUpdateModelMixin, self).update(request, *args, **kwargs)
#
#         self._audit_object = None
#         instance = self.get_object()
#         serializer = self.get_serializer(instance)
#         updated_data = serializer.data
#
#         response.data = updated_data
#
#         changed = self.audit_diff(readed_data, updated_data)
#         self.audit(response.data, changed=changed)
#         return response
#
#     def audit_diff(self, readed_data, updated_data):
#         return []
#
#
# class AuditDestroyModelMixin(BaseAuditModelMixin, DestroyModelMixin):
#     def destroy(self, request, *args, **kwargs):
#         response = super(AuditDestroyModelMixin, self).destroy(request, *args, **kwargs)
#         self.audit(None)
#         return response
#
#
# class AuditModelMixin(AuditCreateModelMixin, AuditUpdateModelMixin, AuditDestroyModelMixin):
#     pass
#
#
# class HistoricalMixin2(GenericAPIView):
#     def __init__(self, **kwargs):
#         super(HistoricalMixin2, self).__init__(**kwargs)
#         self._history_is_active = False
#         self._history_cached_object = None
#         self._history_original_data = None
#         self._history_changed_data = None
#
#     def get_object(self):
#         if self._history_cached_object is None:
#             self._history_cached_object = super(HistoricalMixin2, self).get_object()
#         return self._history_cached_object
#
#     def reset_cache(self):
#         self._history_cached_object = None
#
#     def _get_data(self):
#         instance = self.get_object()
#         serializer = self.get_serializer(instance)
#         data = OrderedDict(serializer.data)
#
#         import pprint
#         print('----')
#         pprint.pprint(OrderedDict(data))
#
#         return data
#
#     def initial(self, request, *args, **kwargs):
#         super(HistoricalMixin2, self).initial(request, *args, **kwargs)
#         self._history_is_active = request.method.upper() not in permissions.SAFE_METHODS
#         if self._history_is_active:
#             self._history_original_data = self._get_data()
#
#     def finalize_response(self, request, response, *args, **kwargs):
#         if self._history_is_active:
#             if request.method.upper() != 'DELETE':
#                 self.reset_cache()
#                 self._history_changed_data = self._get_data()
#                 response.data = self._history_changed_data
#         return super(HistoricalMixin2, self).finalize_response(request, response, *args, **kwargs)
#
# HistoricalMixin = HistoricalMixin2
