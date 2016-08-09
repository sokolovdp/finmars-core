from __future__ import unicode_literals

from rest_framework import permissions
from rest_framework.views import APIView

from poms.audit import history


class HistoricalMixin(APIView):
    def dispatch(self, request, *args, **kwargs):
        if request.method.upper() in permissions.SAFE_METHODS:
            return super(HistoricalMixin, self).dispatch(request, *args, **kwargs)
        else:
            with history.enable():
                response = super(HistoricalMixin, self).dispatch(request, *args, **kwargs)
                return response

    # def get_object(self):
    #     obj = super(HistoricalMixin, self).get_object()
    #     # history.set_actor_content_object(obj)
    #     return obj

    def perform_create(self, serializer):
        history.set_flag_addition()
        super(HistoricalMixin, self).perform_create(serializer)
        history.set_actor_content_object(serializer.instance)

    def perform_update(self, serializer):
        history.set_flag_change()
        history.set_actor_content_object(serializer.instance)
        super(HistoricalMixin, self).perform_update(serializer)

    def perform_destroy(self, instance):
        history.set_flag_deletion()
        history.set_actor_content_object(instance)
        super(HistoricalMixin, self).perform_destroy(instance)
