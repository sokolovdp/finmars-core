from __future__ import unicode_literals

from django.utils.functional import cached_property
from django.utils.translation import ugettext as _
from rest_framework import permissions
from rest_framework.decorators import detail_route, list_route
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from reversion import revisions as reversion

from poms.audit import history
from poms.audit.models import VersionInfo, ModelProxy
from poms.audit.pagination import HistoricalPageNumberPagination
from poms.audit.serializers import VersionSerializer
from poms.users.fields import get_master_user


# TODO: request is to hard for DB, can't prefetch or any optimization
class HistoricalMixin(object):
    ignore_duplicate_revisions = False
    history_latest_first = True
    history_pagination_class = HistoricalPageNumberPagination

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

    def _historical_annotate_object(self, model, fields, versions):
        for v in versions:
            # print('-'*79)
            # print(v.serialized_data)
            # print(v.field_dict)

            # TODO: load one-to-one from history, currently loaded from db
            # TODO: show many-to-many from history, currently loaded from db

            # deser_obj = v.object_version
            # obj = deser_obj.object

            # if deser_obj.m2m_data:
            #     for accessor_name, object_list in deser_obj.m2m_data.items():
            #         setattr(self.object, accessor_name, object_list)
            # obj = v.object_version.object # deserialize m2m as current value :(

            # obj = model()
            # for field in fields:
            #     # print(repr(field))
            #     setattr(obj, field.name, v.field_dict.get(field.name, None))

            # profile = UserProfile.objects.get(user=obj.pk)
            # try:
            #     profile = reversion.get_for_date(profile, v.revision.date_created)
            #     profile = profile.object_version.object
            #     obj.profile = profile
            # except ObjectDoesNotExist:
            #     obj.profile = UserProfile()

            # serializer = self.get_serializer(instance=obj)
            serializer = self.get_serializer(instance=ModelProxy(v))
            v.object_json = serializer.data

    def _make_historical_reponse(self, model, versions):
        fields = self._get_fields(model)
        queryset = versions.select_related('content_type', 'revision__user').prefetch_related('revision__info')

        if self.history_latest_first:
            queryset = queryset.order_by("-pk")
        else:
            queryset = queryset.order_by("pk")

        page = self._historical_paginate_queryset(queryset)
        if page is not None:
            self._historical_annotate_object(model, fields, page)

            serializer = VersionSerializer(page, many=True)
            return self._historical_get_paginated_response(serializer.data)

        self._historical_annotate_object(model, fields, queryset)
        serializer = VersionSerializer(queryset, many=True)
        return Response(serializer.data)

    @cached_property
    def _historical_paginator(self):
        if self.history_pagination_class:
            return self.history_pagination_class()
        return self.pagination_class()

    def _historical_paginate_queryset(self, queryset):
        if self._historical_paginator is None:
            return None
        return self._historical_paginator.paginate_queryset(queryset, self.request, view=self)

        # return self.paginate_queryset(queryset)

    def _historical_get_paginated_response(self, data):
        assert self._historical_paginator is not None
        return self._historical_paginator.get_paginated_response(data)
