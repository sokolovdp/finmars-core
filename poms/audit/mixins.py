from __future__ import unicode_literals

from rest_framework import permissions
from rest_framework.generics import GenericAPIView

from poms.audit import history


# class HistoricalMixin(GenericAPIView):
#     ignore_duplicate_revisions = False
#     history_latest_first = True
#
#     # history_pagination_class = HistoricalPageNumberPagination
#
#     def dispatch(self, request, *args, **kwargs):
#         self._history_is_active = False
#         if request.method.upper() in permissions.SAFE_METHODS:
#             return super(HistoricalMixin, self).dispatch(request, *args, **kwargs)
#         else:
#             self._history_is_active = True
#             # with reversion.create_revision(), history.enable():
#             with history.enable():
#                 response = super(HistoricalMixin, self).dispatch(request, *args, **kwargs)
#                 # if not reversion.get_comment():
#                 #     reversion.set_comment(_('No fields changed.'))
#                 return response
#
#     def get_object(self):
#         obj = super(HistoricalMixin, self).get_object()
#         # if self._history_is_active:
#         #     # history.set_content_object(obj)
#         #     reversion.add_to_revision(obj)
#         return obj
#
#     # def initial(self, request, *args, **kwargs):
#     #     super(HistoricalMixin, self).initial(request, *args, **kwargs)
#     #
#     #     if self._history_is_active:
#     #         # if self.action == 'create':
#     #         #     history.set_flag_addition()
#     #         # elif self.action == 'update' or self.action == 'partial_update':
#     #         #     history.set_flag_change()
#     #         # elif self.action == 'destroy':
#     #         #     history.set_flag_deletion()
#     #
#     #         reversion.set_user(request.user)
#     #         reversion.add_meta(VersionInfo,
#     #                            master_user=request.user.master_user,
#     #                            member=request.user.member,
#     #                            username=request.user.username)
#
#     def finalize_response(self, request, response, *args, **kwargs):
#         # if self._history_is_active:
#         #     try:
#         #         instance = self.get_object()
#         #         serializer = self.get_serializer(instance)
#         #         self._o2 = serializer.data
#         #     except ObjectDoesNotExist:
#         #         self._o2 = None
#         #     pprint.pprint(self._o1)
#         #     pprint.pprint(self._o2)
#         return super(HistoricalMixin, self).finalize_response(request, response, *args, **kwargs)
#
#     def perform_create(self, serializer):
#         history.set_flag_addition()
#         super(HistoricalMixin, self).perform_create(serializer)
#         history.set_content_object(serializer.instance)
#
#     def perform_update(self, serializer):
#         history.set_flag_change()
#         history.set_content_object(serializer.instance)
#         super(HistoricalMixin, self).perform_update(serializer)
#
#     def perform_destroy(self, instance):
#         history.set_flag_deletion()
#         history.set_content_object(instance)
#         super(HistoricalMixin, self).perform_destroy(instance)
#
#         # @list_route(permission_classes=(IsAuthenticated, SuperUserOnly,))
#         # def deleted(self, request, pk=None):
#         #     # master_user = get_master_user(request)
#         #     master_user = request.user.master_user
#         #     model = self.get_queryset().model
#         #
#         #     deleted_list = Version.objects.get_deleted(model).filter(revision__info__master_user=master_user)
#         #
#         #     self._version_id = request.query_params.get('version_id')
#         #     if self._version_id:
#         #         deleted_list = deleted_list.filter(pk=self._version_id)
#         #
#         #     return self._make_historical_reponse(deleted_list)
#         #
#         # @list_route(permission_classes=(IsAuthenticated, SuperUserOnly,))
#         # def histories(self, request, pk=None):
#         #     # instance = self.get_object()
#         #     # version_list = reversion.get_for_object(instance)
#         #
#         #     # master_user = get_master_user(request)
#         #     master_user = request.user.master_user
#         #     model = self.get_queryset().model
#         #     version_list = Version.objects.get_for_model(model).filter(
#         #         revision__info__master_user=master_user)
#         #
#         #     self._version_id = request.query_params.get('version_id')
#         #     if self._version_id:
#         #         version_list = version_list.filter(pk=self._version_id)
#         #
#         #     return self._make_historical_reponse(version_list)
#         #
#         # @detail_route(permission_classes=(IsAuthenticated, SuperUserOnly,))
#         # def history(self, request, pk=None):
#         #     # instance = self.get_object()
#         #     # version_list = reversion.get_for_object(instance)
#         #
#         #     # master_user = get_master_user(request)
#         #     master_user = request.user.master_user
#         #     model = self.get_queryset().model
#         #     version_list = Version.objects.get_for_object_reference(model, pk).filter(
#         #         revision__info__master_user=master_user)
#         #
#         #     self._version_id = request.query_params.get('version_id')
#         #     if self._version_id:
#         #         version_list = version_list.filter(pk=self._version_id)
#         #
#         #     return self._make_historical_reponse(version_list)
#         #
#         # def _history_load_object(self, version):
#         #     # TODO: load one-to-one from history, currently loaded from db
#         #     # TODO: show many-to-many from history, currently loaded from db
#         #     # TODO: show one-to-many from history, currently loaded from db
#         #     # TODO: show many-to-one from history, currently loaded from db
#         #     if version and self._version_id:
#         #         serializer = self.get_serializer(instance=history.ModelProxy(version))
#         #         version.object_json = serializer.data
#         #
#         # def _history_load_objects(self, versions):
#         #     if self._version_id:
#         #         for v in versions:
#         #             self._history_load_object(v)
#         #
#         # def _make_historical_reponse(self, versions):
#         #     queryset = versions.select_related('content_type', 'revision__user').prefetch_related('revision__info')
#         #
#         #     if self._version_id:
#         #         version = queryset.first()
#         #         if version is None:
#         #             return Response(status=status.HTTP_404_NOT_FOUND)
#         #         self._history_load_object(version)
#         #         serializer = VersionSerializer(version, context=self.get_serializer_context())
#         #         return Response(serializer.data)
#         #
#         #     if self.history_latest_first:
#         #         queryset = queryset.order_by("-pk")
#         #     else:
#         #         queryset = queryset.order_by("pk")
#         #
#         #     page = self.paginate_queryset(queryset)
#         #     if page is not None:
#         #         self._history_load_objects(page)
#         #         serializer = VersionSerializer(page, many=True, context=self.get_serializer_context())
#         #         return self.get_paginated_response(serializer.data)
#         #
#         #     self._history_load_objects(queryset)
#         #     serializer = VersionSerializer(queryset, many=True, context=self.get_serializer_context())
#         #     return Response(serializer.data)
