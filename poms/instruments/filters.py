from __future__ import unicode_literals

from rest_framework.filters import BaseFilterBackend

from poms.api.filters import IsOwnerByMasterUserFilter
from poms.instruments.models import Instrument


class IsOwnerViaInstrumentFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        instruments = Instrument.objects.all()
        instruments = IsOwnerByMasterUserFilter().filter_queryset(request, instruments, view)
        return queryset.filter(instrument__in=instruments)
